import pytest

from datetime import datetime
from zoneinfo import ZoneInfo

from ddw import app
from ddw.app import run_update
from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.data.ncaa.evaluator import NCAAEvaluator
from ddw.models import LastKnownGame, ResultType


@pytest.fixture(autouse=True)
def reset_default_card_flag(monkeypatch):
    monkeypatch.setattr(app, "_default_card_published", False)


class TestRunUpdate:
    @pytest.fixture
    def mock_evaluator(self, mocker):
        return mocker.patch.object(NCAAEvaluator, "find_current_game")

    @pytest.fixture
    def mock_render(self, mocker):
        return mocker.patch("ddw.app.render")

    @pytest.fixture
    def mock_upload(self, mocker):
        return mocker.patch("ddw.app.upload")

    @pytest.fixture
    def mock_post_tweet(self, mocker):
        return mocker.patch("ddw.app.tweeter.post_tweet")

    @pytest.fixture
    def mock_should_tweet(self, mocker):
        return mocker.patch("ddw.app.should_tweet")

    def test_tweeting_disabled_doesnt_tweet(
        self,
        mock_evaluator,
        mock_render,
        mock_upload,
        mock_post_tweet,
        mock_should_tweet,
    ):
        mock_should_tweet.return_value = False
        run_update()
        mock_post_tweet.assert_not_called()

    def test_game_not_ended_doesnt_tweet(
        self,
        mock_evaluator,
        mock_render,
        mock_upload,
        mock_post_tweet,
        mock_should_tweet,
    ):
        mock_should_tweet.return_value = True
        mock_evaluator.return_value = NCAAGame(ResultType.NOT_YET, "32-31")
        run_update()
        mock_post_tweet.assert_not_called()

    def test_game_ended_tweets(
        self,
        mock_evaluator,
        mock_render,
        mock_upload,
        mock_post_tweet,
        mock_should_tweet,
    ):
        mock_should_tweet.return_value = True
        mock_evaluator.return_value = NCAAGame(ResultType.WIN, "32-31")
        run_update()
        mock_post_tweet.assert_called_once_with("YES. 32-31 http://www.diddukewin.com")

    def test_no_game_does_not_upload_without_force_option(
        self, mock_evaluator, mock_render, mock_upload
    ):
        mock_evaluator.return_value = None

        run_update(force_upload=False)

        mock_render.assert_not_called()
        mock_upload.assert_not_called()

    def test_force_option_renders_and_uploads_last_known_game(
        self, mocker, mock_evaluator, mock_render, mock_upload
    ):
        mock_evaluator.return_value = None
        last_known_game = LastKnownGame(ResultType.LOSS, "67-70")
        download_mock = mocker.patch("ddw.app.download", return_value="old html")
        parse_mock = mocker.patch(
            "ddw.app.parse_last_known_game", return_value=last_known_game
        )

        run_update(force_upload=True)

        download_mock.assert_called_once_with()
        parse_mock.assert_called_once_with("old html")
        mock_render.assert_called_once()
        page_upload = mock_upload.call_args_list[-2]
        assert page_upload.args == (mock_render.return_value,)
        assert page_upload.kwargs["force"] is True

    def test_force_option_without_last_known_game_does_not_upload(
        self, mocker, mock_evaluator, mock_render, mock_upload
    ):
        mock_evaluator.return_value = None
        mocker.patch("ddw.app.download", return_value=None)

        run_update(force_upload=True)

        mock_render.assert_not_called()
        mock_upload.assert_not_called()


from datetime import datetime, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from ddw import app  # noqa: E402
from ddw.clock import Clock  # noqa: E402
from ddw.data.ncaa.fetcher import NCAAThrottled  # noqa: E402

NOW = datetime(2026, 11, 3, 19, 0, tzinfo=ZoneInfo("America/New_York"))


class FakeClock(Clock):
    def __init__(self):
        self.current = NOW

    def now(self):
        return self.current


class TestShouldKeepRunning:
    def test_no_game(self):
        assert not app.should_keep_running(None, NOW)

    def test_live(self):
        assert app.should_keep_running(NCAAGame(ResultType.NOT_YET, "1-0"), NOW)

    def test_ended(self):
        assert not app.should_keep_running(NCAAGame(ResultType.WIN, "1-0"), NOW)

    @pytest.mark.parametrize(
        "minutes_until_start,expected",
        [(30, False), (11, True), (0, True), (-30, True), (-60, False)],
    )
    def test_pregame_window(self, minutes_until_start, expected):
        game = NCAAGame(
            ResultType.NOT_YET,
            "0-0",
            game_state="P",
            start_time=NOW + timedelta(minutes=minutes_until_start),
        )
        assert app.should_keep_running(game, NOW) is expected

    def test_pregame_without_start_time(self):
        game = NCAAGame(ResultType.NOT_YET, "0-0", game_state="P")
        assert not app.should_keep_running(game, NOW)


class TestRun:
    @pytest.fixture(autouse=True)
    def no_force(self, mocker):
        mocker.patch("ddw.app.should_force_upload", return_value=False)

    @pytest.fixture
    def update(self, mocker):
        return mocker.patch("ddw.app.run_update")

    @staticmethod
    def live():
        return NCAAGame(ResultType.NOT_YET, "10-8")

    @staticmethod
    def final():
        return NCAAGame(ResultType.WIN, "80-70")

    def test_no_game_exits_immediately(self, update):
        update.return_value = None
        app.run(FakeClock(), lambda s: None)
        assert update.call_count == 1

    def test_loops_until_final(self, update):
        update.side_effect = [self.live(), self.live(), self.final()]
        sleeps = []
        app.run(FakeClock(), sleeps.append)
        assert update.call_count == 3
        assert sleeps == [15, 15]

    def test_poll_interval_clamped(self, update, monkeypatch):
        monkeypatch.setenv("LIVE_POLL_SECONDS", "2")
        update.side_effect = [self.live(), self.final()]
        sleeps = []
        app.run(FakeClock(), sleeps.append)
        assert sleeps == [10]

    def test_waits_through_pregame_in_window(self, update):
        pregame = NCAAGame(
            ResultType.NOT_YET,
            "0-0",
            game_state="P",
            start_time=NOW + timedelta(minutes=5),
        )
        update.side_effect = [pregame, self.live(), self.final()]
        app.run(FakeClock(), lambda s: None)
        assert update.call_count == 3

    def test_exits_when_pregame_far_off(self, update):
        pregame = NCAAGame(
            ResultType.NOT_YET,
            "0-0",
            game_state="P",
            start_time=NOW + timedelta(hours=3),
        )
        update.return_value = pregame
        app.run(FakeClock(), lambda s: None)
        assert update.call_count == 1

    def test_first_failure_raises(self, update):
        update.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            app.run(FakeClock(), lambda s: None)

    def test_throttle_with_no_live_game_exits_cleanly(self, update):
        update.side_effect = NCAAThrottled(403)
        app.run(FakeClock(), lambda s: pytest.fail("should not sleep"))
        assert update.call_count == 1

    def test_survives_a_failure_mid_game(self, update):
        update.side_effect = [self.live(), RuntimeError("blip"), self.final()]
        app.run(FakeClock(), lambda s: None)
        assert update.call_count == 3

    def test_stops_after_repeated_failures(self, update):
        update.side_effect = [self.live()] + [RuntimeError("down")] * 10
        with pytest.raises(RuntimeError):
            app.run(FakeClock(), lambda s: None)
        assert update.call_count == 1 + app.MAX_CONSECUTIVE_FAILURES

    def test_throttle_backs_off_then_recovers(self, update):
        update.side_effect = [
            self.live(),
            NCAAThrottled(429),
            NCAAThrottled(429),
            NCAAThrottled(429, retry_after=7),
            self.live(),
            self.final(),
        ]
        sleeps = []
        app.run(FakeClock(), sleeps.append)
        assert sleeps == [15, 30, 60, 7, 15]

    def test_max_run_time(self, update):
        clock = FakeClock()
        update.return_value = self.live()

        def sleep(_):
            clock.current += timedelta(hours=1)

        app.run(clock, sleep)
        assert update.call_count == 5  # t=0h..4h, then deadline hit

    def test_sigterm_stops(self, update):
        update.return_value = self.live()
        app.run(FakeClock(), lambda s: True)
        assert update.call_count == 1

    def test_force_upload_never_loops(self, update, mocker):
        mocker.patch("ddw.app.should_force_upload", return_value=True)
        update.return_value = self.live()
        app.run(FakeClock(), lambda s: pytest.fail("should not sleep"))
        assert update.call_count == 1


class TestServe:
    """The long-lived worker: idle checks in the window, live polling in games."""

    @pytest.fixture
    def update(self, mocker):
        return mocker.patch("ddw.app.run_update")

    live = staticmethod(TestRun.live)
    final = staticmethod(TestRun.final)

    @staticmethod
    def serve(start=NOW, max_sleeps=10):
        """Run serve() on a fake clock that each sleep advances; stop (as if
        SIGTERM arrived) after ``max_sleeps`` sleeps. Returns the delays."""
        clock = FakeClock()
        clock.current = start
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            clock.current += timedelta(seconds=seconds)
            return len(sleeps) >= max_sleeps

        app.serve(clock, sleep)
        return sleeps

    def test_idles_when_no_game(self, update):
        update.return_value = None
        assert self.serve(max_sleeps=3) == [600, 600, 600]
        assert update.call_count == 3
        update.assert_called_with(force_upload=False)

    def test_sleeps_outside_window_without_calling_out(self, update):
        update.return_value = None
        start = NOW.replace(hour=10, minute=55)
        assert self.serve(start, max_sleeps=3) == [300, 600, 600]
        assert update.call_count == 2  # at 11:00 and 11:10

    def test_polls_live_then_returns_to_idle(self, update):
        pregame = NCAAGame(
            ResultType.NOT_YET,
            "0-0",
            game_state="P",
            start_time=NOW + timedelta(minutes=5),
        )
        update.side_effect = [None, pregame, self.live(), self.final(), None]
        start = NOW - timedelta(minutes=10)
        assert self.serve(start, max_sleeps=5) == [600, 15, 15, 600, 600]

    def test_keeps_polling_live_game_past_window_end(self, update):
        update.return_value = self.live()
        start = NOW.replace(hour=1, minute=59, second=50)
        assert self.serve(start, max_sleeps=4) == [15, 15, 15, 15]
        assert update.call_count == 4

    def test_final_after_window_end_goes_quiet(self, update):
        update.side_effect = [self.live(), self.final()]
        start = NOW.replace(hour=1, minute=59, second=50)
        assert self.serve(start, max_sleeps=3) == [15, 600, 600]
        assert update.call_count == 2  # 02:10 is outside the window

    def test_failures_never_exit(self, update):
        update.side_effect = RuntimeError("down")
        assert self.serve(max_sleeps=10) == [600] * 10

    def test_live_failures_back_off_and_recover(self, update):
        update.side_effect = [
            self.live(),
            NCAAThrottled(429),
            NCAAThrottled(429, retry_after=7),
            RuntimeError("blip"),
            self.live(),
        ]
        assert self.serve(max_sleeps=5) == [15, 30, 7, 15, 15]

    def test_persistent_live_failures_fall_back_to_idle(self, update):
        update.side_effect = [self.live()] + [RuntimeError("down")] * 20
        sleeps = self.serve(max_sleeps=10)
        live_retries = app.MAX_CONSECUTIVE_FAILURES - 1
        assert sleeps == [15] * (1 + live_retries) + [600] * (10 - 1 - live_retries)

    def test_persistent_live_failures_go_quiet_outside_window(self, update):
        update.side_effect = [self.live()] + [RuntimeError("down")] * 20
        start = NOW.replace(hour=1, minute=59, second=0)
        self.serve(start, max_sleeps=10)
        # 1 live update + MAX failures, then nothing until 11:00
        assert update.call_count == 1 + app.MAX_CONSECUTIVE_FAILURES

    def test_game_past_cap_from_start_time_goes_idle(self, update):
        stale = NCAAGame(
            ResultType.NOT_YET, "40-40", start_time=NOW - timedelta(hours=4)
        )
        update.return_value = stale
        assert self.serve(max_sleeps=3) == [600, 600, 600]

    def test_game_without_start_time_capped_from_first_live_poll(
        self, update, monkeypatch
    ):
        monkeypatch.setenv("MAX_RUN_HOURS", "1")
        monkeypatch.setenv("LIVE_POLL_SECONDS", "1200")  # 20-minute polls
        update.return_value = self.live()
        assert self.serve(max_sleeps=5) == [1200, 1200, 1200, 600, 600]

    def test_idle_throttle_waits_idle_interval(self, update):
        update.side_effect = [NCAAThrottled(403), None]
        assert self.serve(max_sleeps=2) == [600, 600]

    def test_sigterm_stops(self, update):
        update.return_value = self.live()
        app.serve(FakeClock(), lambda s: True)
        assert update.call_count == 1


class TestRunUpdateLive:
    def test_pregame_is_not_uploaded(self, mocker):
        pregame = NCAAGame(ResultType.NOT_YET, "0-0", game_state="P")
        mocker.patch.object(NCAAEvaluator, "find_current_game", return_value=pregame)
        upload_mock = mocker.patch("ddw.app.upload")
        assert app.run_update(force_upload=False) is pregame
        upload_mock.assert_not_called()

    def test_uploads_both_files_and_purges_on_change(self, mocker):
        mocker.patch.object(
            NCAAEvaluator,
            "find_current_game",
            return_value=NCAAGame(ResultType.NOT_YET, "10-8"),
        )
        upload_mock = mocker.patch("ddw.app.upload", return_value=True)
        purge = mocker.patch("ddw.app.cloudflare.purge_urls")
        app.run_update(force_upload=False)
        assert upload_mock.call_count == 3
        assert upload_mock.call_args_list[0].kwargs["key"] == "cards/default.png"
        assert upload_mock.call_args_list[2].kwargs["key"] == "score.json"
        purge.assert_called_once()

    def test_no_purge_when_unchanged(self, mocker):
        mocker.patch.object(
            NCAAEvaluator,
            "find_current_game",
            return_value=NCAAGame(ResultType.NOT_YET, "10-8"),
        )
        mocker.patch("ddw.app.upload", return_value=False)
        purge = mocker.patch("ddw.app.cloudflare.purge_urls")
        app.run_update(force_upload=False)
        purge.assert_not_called()


class TestSocialCards:
    @pytest.fixture
    def uploads(self, mocker):
        return mocker.patch("ddw.app.upload", return_value=True)

    @pytest.fixture
    def skeet(self, mocker):
        mocker.patch("ddw.app.should_skeet", return_value=True)
        mocker.patch("ddw.app.should_toot", return_value=False)
        mocker.patch("ddw.app.should_tweet", return_value=False)
        return mocker.patch("ddw.app.skeeter.post_skeet")

    def final_game(self):
        return NCAAGame(
            ResultType.WIN,
            "82-75",
            start_time=datetime(
                2026, 11, 12, 19, 0, tzinfo=ZoneInfo("America/New_York")
            ),
        )

    def test_final_game_uploads_card_then_permalink_then_homepage(
        self, mocker, uploads, skeet
    ):
        mocker.patch.object(
            NCAAEvaluator, "find_current_game", return_value=self.final_game()
        )
        app.run_update(force_upload=False)

        keys = [c.kwargs.get("key", "index.html") for c in uploads.call_args_list]
        slug = keys[0].split("/")[1]
        assert keys == [
            f"g/{slug}/card.png",
            f"g/{slug}/index.html",
            "index.html",
            "score.json",
        ]
        card = uploads.call_args_list[0]
        assert card.args[0].startswith(b"\x89PNG")
        assert card.kwargs["content_type"] == "image/png"
        permalink_html = uploads.call_args_list[1].args[0]
        assert f"https://diddukewin.com/g/{slug}/" in permalink_html
        assert "<title>Did Duke Win? Yes</title>" in permalink_html
        homepage_html = uploads.call_args_list[2].args[0]
        assert f"https://diddukewin.com/g/{slug}/card.png" in homepage_html
        assert "content=https://diddukewin.com/ property=og:url" in homepage_html

    def test_final_game_skeets_permalink_with_card(self, mocker, uploads, skeet):
        mocker.patch.object(
            NCAAEvaluator, "find_current_game", return_value=self.final_game()
        )
        app.run_update(force_upload=False)

        text, link_card = skeet.call_args.args
        assert text == "YES. 82-75"
        assert link_card.url.startswith("https://diddukewin.com/g/20261112-")
        assert link_card.title == "Did Duke Win? Yes"
        assert link_card.description == "W 82-75"
        assert link_card.image_png.startswith(b"\x89PNG")

    def test_live_game_uploads_no_game_card(self, mocker, uploads):
        mocker.patch.object(
            NCAAEvaluator,
            "find_current_game",
            return_value=NCAAGame(ResultType.NOT_YET, "10-8"),
        )
        app.run_update(force_upload=False)

        keys = [c.kwargs.get("key", "index.html") for c in uploads.call_args_list]
        assert not any(key.startswith("g/") for key in keys)
        homepage_html = uploads.call_args_list[1].args[0]
        assert "https://diddukewin.com/cards/default.png" in homepage_html

    def test_default_card_is_checked_once_per_process(self, mocker, uploads):
        mocker.patch.object(
            NCAAEvaluator,
            "find_current_game",
            return_value=NCAAGame(ResultType.NOT_YET, "10-8"),
        )
        app.run_update(force_upload=False)
        app.run_update(force_upload=False)

        keys = [c.kwargs.get("key") for c in uploads.call_args_list]
        assert keys.count("cards/default.png") == 1

    def test_forced_upload_of_last_known_game_keeps_existing_card(
        self, mocker, uploads
    ):
        mocker.patch.object(NCAAEvaluator, "find_current_game", return_value=None)
        mocker.patch(
            "ddw.app.download",
            return_value='<meta property="og:image" content="https://diddukewin.com/g/20261112-abc123/card.png">',
        )
        mocker.patch(
            "ddw.app.parse_last_known_game",
            return_value=LastKnownGame(ResultType.WIN, "82-75"),
        )
        app.run_update(force_upload=True)

        keys = [c.kwargs.get("key", "index.html") for c in uploads.call_args_list]
        assert keys == ["index.html", "score.json"]
        homepage_html = uploads.call_args_list[0].args[0]
        assert "https://diddukewin.com/g/20261112-abc123/card.png" in homepage_html
