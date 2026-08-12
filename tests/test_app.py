import pytest

from ddw.app import run_update
from ddw.data.espn.models import ESPNGame
from ddw.data.goduke.evaluator import GoDukeEvaluator
from ddw.models import LastKnownGame, ResultType


class TestRunUpdate:
    @pytest.fixture
    def mock_evaluator(self, mocker):
        return mocker.patch.object(GoDukeEvaluator, "find_current_game")

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
        mock_evaluator.return_value = ESPNGame("", "", "asdf", "32-31", "")
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
        mock_evaluator.return_value = ESPNGame("", "", "W", "32-31", "")
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
        mock_upload.assert_called_once_with(mock_render.return_value, force=True)

    def test_force_option_without_last_known_game_does_not_upload(
        self, mocker, mock_evaluator, mock_render, mock_upload
    ):
        mock_evaluator.return_value = None
        mocker.patch("ddw.app.download", return_value=None)

        run_update(force_upload=True)

        mock_render.assert_not_called()
        mock_upload.assert_not_called()
