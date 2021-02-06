import os
from datetime import datetime, timezone, timedelta

import twitter

from ddw.config import get_config_value
from ddw.models import Tweet
import logging


logger = logging.getLogger()


SCREEN_NAME = "diddukewin"
MIN_HOURS_BETWEEN_TWEETS = int(os.getenv("MIN_HOURS_BETWEEN_TWEETS", 8))


def create_api():
    return twitter.Api(
        consumer_key=get_config_value("TWITTER_CONSUMER_KEY"),
        consumer_secret=get_config_value("TWITTER_CONSUMER_SECRET"),
        access_token_key=get_config_value("TWITTER_ACCESS_TOKEN_KEY"),
        access_token_secret=get_config_value("TWITTER_ACCESS_TOKEN_SECRET"),
    )


class Tweeter:
    def __init__(self, api=None):
        self._last_tweet_dict = None
        if not api:
            api = create_api()
        self.api = api

    def get_latest_tweet(self) -> dict:
        if self._last_tweet_dict:
            return self._last_tweet_dict
        statuses = self.api.GetUserTimeline(screen_name=SCREEN_NAME, count=1)
        status = statuses[0]
        t_dict = {"text": status.text, "created_at": status.created_at}
        self._last_tweet_dict = t_dict
        return t_dict

    def bust(self):
        self._last_tweet_dict = None
        self.api = create_api()

    def post_tweet(self, tweet_text: str):
        latest_tweet_dict = self.get_latest_tweet()
        latest_tweet = Tweet.from_tweet_dict(latest_tweet_dict)
        logger.info(f"Found latest tweet: {latest_tweet.text_without_link}")

        now = datetime.now(timezone.utc)
        time_since_last_tweet = now - latest_tweet.created_at
        hours_since_last_tweet = time_since_last_tweet / timedelta(hours=1)

        if hours_since_last_tweet <= MIN_HOURS_BETWEEN_TWEETS:
            logger.info("Too soon, not tweeting.")
            return

        new_tweet = Tweet(tweet_text)
        if latest_tweet.text_without_link == new_tweet.text_without_link:
            logger.info("Same content, not tweeting.")
            return

        self.api.PostUpdate(tweet_text)
        self.bust()
        logger.info(f"Posted tweet: {tweet_text}")


tweeter = Tweeter()
