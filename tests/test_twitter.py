import datetime
from unittest.mock import MagicMock

import pytest

from ddw.models import Tweet
from ddw.twitter import Tweeter


@pytest.fixture
def mock_api(mocker):
    return mocker.patch("ddw.twitter.twitter.Api")


class TestGetLatestTweet:
    def test_grabs_first(self):
        status = MagicMock()
        status.text = "foo"
        status.created_at = "Sun Mar 31 23:08:43 +0000 2019"
        mock_api = MagicMock()
        mock_api.GetUserTimeline.return_value = [status]

        latest = Tweeter(mock_api).get_latest_tweet()
        assert latest == {"text": "foo", "created_at": "Sun Mar 31 23:08:43 +0000 2019"}


class TestPostTweet:
    @pytest.fixture
    def mock_get_latest_tweet(self, mocker):
        return mocker.patch.object(Tweeter, "get_latest_tweet")

    @pytest.fixture
    def mock_from_tweet_dict(self, mocker):
        return mocker.patch.object(Tweet, "from_tweet_dict")

    def test_too_early_doesnt_post(
        self, mock_get_latest_tweet, mock_from_tweet_dict, mock_api
    ):
        mock_from_tweet_dict.return_value = Tweet(
            "bar",
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
        )
        Tweeter(mock_api).post_tweet("foo")
        mock_api.PostUpdate.assert_not_called()

    def test_same_text_without_link_doesnt_post(
        self, mock_get_latest_tweet, mock_from_tweet_dict, mock_api
    ):
        mock_from_tweet_dict.return_value = Tweet(
            "foo",
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=9),
        )
        Tweeter(mock_api).post_tweet("foo")
        mock_api.PostUpdate.assert_not_called()

    def test_tweets(self, mock_get_latest_tweet, mock_from_tweet_dict, mock_api):
        mock_from_tweet_dict.return_value = Tweet(
            "bar",
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=9),
        )
        Tweeter(mock_api).post_tweet("foo")
        mock_api.PostUpdate.assert_called_once_with("foo")
