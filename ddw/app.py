import os
import signal
import sys
import threading
from datetime import datetime, timedelta
from typing import Callable

from ddw import cloudflare
from ddw.clock import Clock
from ddw.config import (
    idle_poll_seconds,
    in_active_window,
    live_poll_seconds,
    max_run_hours,
    pregame_grace_minutes,
    pregame_window_minutes,
    seconds_until_active,
)
from ddw.data.ncaa.fetcher import NCAAThrottled
from ddw.bluesky import skeeter
from ddw.data.ncaa.evaluator import NCAAEvaluator
from ddw.evaluator import IEvaluator
from ddw.mastodon import tooter
from ddw.twitter import tweeter
from ddw.config import should_force_upload, should_skeet, should_toot, should_tweet
from ddw.models import GameDisplay, IGame
from ddw.renderer import parse_last_known_game, render, render_state
from ddw.uploader import SCORE_KEY, download, upload
import logging

if os.getenv("SENTRY_DSN"):
    import sentry_sdk

    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

MAX_CONSECUTIVE_FAILURES = 5


def run_update(force_upload: bool | None = None) -> IGame | None:
    """Do one update. Returns the game found (possibly pregame), if any."""
    force_upload = should_force_upload() if force_upload is None else force_upload
    evaluator = get_evaluator()
    game = evaluator.find_current_game()
    pregame: IGame | None = None
    if game and game.is_pregame():
        # Nothing to show before tip-off; the previous result stays up.
        pregame, game = game, None
    using_last_known_game = False
    if not game:
        if not force_upload:
            logger.info("No game found, exiting")
            return pregame

        last_known_html = download()
        game = parse_last_known_game(last_known_html) if last_known_html else None
        if not game:
            logger.info("No last known game found, exiting")
            return pregame

        using_last_known_game = True
        logger.info("No game found, using last known game for forced upload")

    logger.info(f"Found current game: {game}")
    game_display = GameDisplay(game)
    rendered = render(game_display)
    changed = [
        upload(
            rendered,
            force=force_upload,
            cache_control=cloudflare.cache_control(15),
        ),
        upload(
            render_state(game_display),
            key=SCORE_KEY,
            force=force_upload,
            content_type="application/json",
            cache_control=cloudflare.cache_control(5),
        ),
    ]
    if any(changed):
        cloudflare.purge_urls(cloudflare.site_urls())

    if using_last_known_game:
        logger.info("Not posting since using last known game for forced upload")
        return game

    if game.has_ended():
        if should_toot():
            tooter.post_status(game_display.tweet_text)
        else:
            logger.info("Not tooting since tooting disabled")

        if should_tweet():
            tweeter.post_tweet(game_display.tweet_text)
        else:
            logger.info("Not tweeting since tweeting disabled")

        if should_skeet():
            skeeter.post_skeet(game_display.result_and_score)
        else:
            logger.info("Not skeeting since skeeting disabled")
    else:
        logger.info("Not posting since game not ended")
    return game


def should_keep_running(game: IGame | None, now: datetime) -> bool:
    """Stay alive while Duke's game is live or about to tip off."""
    if game is None:
        return False
    if not game.is_pregame():
        return not game.has_ended()
    start = game.get_start_time()
    if start is None:
        return False
    return (
        start - timedelta(minutes=pregame_window_minutes())
        <= now
        <= start + timedelta(minutes=pregame_grace_minutes())
    )


def run(
    clock: Clock | None = None,
    sleep: Callable[[float], object] | None = None,
) -> None:
    """Update once; if a game is live (or about to start), keep polling until
    it ends, then exit. With no game, behaves like a single update."""
    if should_force_upload():
        run_update()
        return

    clock = clock or Clock()
    sleep = sleep or _sigterm_sleep()
    deadline = clock.now() + timedelta(hours=max_run_hours())
    active = False
    failures = 0
    while True:
        delay: float = live_poll_seconds()
        try:
            game = run_update()
            failures = 0
        except Exception as e:
            if not active:
                if isinstance(e, NCAAThrottled):
                    # Off-hours throttle: same as the old no-op exit, not a failed Job.
                    logger.warning(f"NCAA throttled with no live game, exiting: {e}")
                    return
                raise  # nothing live yet; fail like a normal cron run
            failures += 1
            logger.exception("Update failed during live game")
            _report(e)
            if failures >= MAX_CONSECUTIVE_FAILURES:
                logger.error("Too many consecutive failures, exiting")
                raise
            game = None
            delay = _backoff_delay(e, failures)
        else:
            active = should_keep_running(game, clock.now())
        if not active:
            return
        if clock.now() >= deadline:
            logger.warning("Hit max run time, exiting")
            return
        if sleep(delay) is True:  # Event.wait returns True when signaled
            logger.info("Stopping on SIGTERM")
            return


def serve(
    clock: Clock | None = None,
    sleep: Callable[[float], object] | None = None,
) -> None:
    """Run forever as a long-lived worker, so a deploy can replace the process
    at any time, mid-game included: every iteration is stateless.

    Outside the active hours with nothing live, sleep without calling out.
    Inside them, look for a game every idle interval; while one is live or about
    to tip off, poll at the live interval. Errors are reported and retried,
    never fatal; after MAX_CONSECUTIVE_FAILURES in a row during a game, or once
    a game has gone MAX_RUN_HOURS past its start, fall back to the idle schedule.
    Returns only on SIGTERM (or when ``sleep`` returns True)."""
    clock = clock or Clock()
    sleep = sleep or _sigterm_sleep()
    live = False
    live_since: datetime | None = None
    failures = 0
    while True:
        now = clock.now()
        if not live and not in_active_window(now):
            delay = min(idle_poll_seconds(), seconds_until_active(now))
        else:
            delay = idle_poll_seconds()
            try:
                game = run_update(force_upload=False)
            except Exception as e:
                logger.exception("Update failed")
                _report(e)
                if live:
                    failures += 1
                    if failures >= MAX_CONSECUTIVE_FAILURES:
                        logger.error("Too many consecutive failures, going idle")
                        live = False
                    else:
                        delay = _backoff_delay(e, failures)
            else:
                failures = 0
                now = clock.now()
                live = should_keep_running(game, now)
                if not live:
                    live_since = None  # game over or none: next one starts fresh
                elif live_since is None:
                    live_since = now
                if live and _past_game_cap(game, live_since, now):
                    logger.warning("Game past max run time, going idle")
                    live = False
                if live:
                    delay = live_poll_seconds()
        if not live:
            failures = 0
        if sleep(delay) is True:  # Event.wait returns True when signaled
            logger.info("Stopping on SIGTERM")
            return


def _past_game_cap(
    game: IGame | None, live_since: datetime | None, now: datetime
) -> bool:
    """A game still not final MAX_RUN_HOURS after it started (a stale or
    suspended feed) stops getting live polling. Anchored on the listed start so
    the cap survives pod replacement; falls back to when polling began."""
    start = (game.get_start_time() if game else None) or live_since
    return start is not None and now >= start + timedelta(hours=max_run_hours())


def _sigterm_sleep() -> Callable[[float], bool]:
    """A sleep that returns True early once SIGTERM arrives."""
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    return stop.wait


def _report(error: Exception) -> None:
    if os.getenv("SENTRY_DSN"):
        sentry_sdk.capture_exception(error)


def _backoff_delay(error: Exception, failures: int) -> float:
    if isinstance(error, NCAAThrottled):
        return error.retry_after or min(30 * 2 ** (failures - 1), 300)
    return live_poll_seconds()


def get_evaluator() -> IEvaluator:
    return NCAAEvaluator()


if __name__ == "__main__":
    # `once` (or FORCE_UPLOAD) is a one-off manual run; the default is the
    # long-lived worker the Kubernetes Deployment runs.
    if should_force_upload() or sys.argv[1:] == ["once"]:
        run()
    else:
        serve()
