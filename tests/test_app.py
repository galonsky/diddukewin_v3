import pytest

from ddw.app import run_update
from ddw.evaluator import Evaluator
from ddw.models import Game


class TestRunUpdate:
    @pytest.fixture
    def mock_evaluator(self, mocker):
        return mocker.patch.object(Evaluator, "find_current_game")

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
        mock_evaluator.return_value = Game("", "", "asdf", "32-31", "")
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
        mock_evaluator.return_value = Game("", "", "W", "32-31", "")
        run_update()
        mock_post_tweet.assert_called_once_with("YES. 32-31 http://www.diddukewin.com")
