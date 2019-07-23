import pytest


from datetime import datetime
from datetime import timezone

from ddw.models import Tweet


@pytest.fixture
def tweet_dict():
    return {
        "created_at": "Sun Mar 31 23:08:43 +0000 2019",
        "text": "NO. 67-68 https://t.co/LCKD7TBBTU",
    }


class TestInit:
    def test_created_at_is_parsed(self, tweet_dict):
        tweet = Tweet(tweet_dict)
        assert tweet.created_at == datetime(2019, 3, 31, 23, 8, 43, tzinfo=timezone.utc)
