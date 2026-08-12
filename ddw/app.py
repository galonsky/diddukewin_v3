import os

from ddw.bluesky import skeeter
from ddw.data.goduke.evaluator import GoDukeEvaluator
from ddw.data.ncaa.evaluator import NCAAEvaluator
from ddw.evaluator import IEvaluator
from ddw.mastodon import tooter
from ddw.twitter import tweeter
from ddw.config import should_force_upload, should_skeet, should_toot, should_tweet
from ddw.models import GameDisplay
from ddw.renderer import parse_last_known_game, render
from ddw.uploader import download, upload
import logging

if os.getenv("SENTRY_DSN"):
    import sentry_sdk

    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def run_update(force_upload: bool | None = None):
    force_upload = should_force_upload() if force_upload is None else force_upload
    evaluator = get_evaluator()
    game = evaluator.find_current_game()
    using_last_known_game = False
    if not game:
        if not force_upload:
            logger.info("No game found, exiting")
            return

        last_known_html = download()
        game = parse_last_known_game(last_known_html) if last_known_html else None
        if not game:
            logger.info("No last known game found, exiting")
            return

        using_last_known_game = True
        logger.info("No game found, using last known game for forced upload")

    logger.info(f"Found current game: {game}")
    game_display = GameDisplay(game)
    rendered = render(game_display)
    if force_upload:
        upload(rendered, force=True)
    else:
        upload(rendered)

    if using_last_known_game:
        logger.info("Not posting since using last known game for forced upload")
        return

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


def get_evaluator() -> IEvaluator:
    if os.getenv("USE_NCAA"):
        return NCAAEvaluator()
    return GoDukeEvaluator()


if __name__ == "__main__":
    run_update()
