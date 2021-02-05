import os
from datetime import datetime, timezone, timedelta

import twitter

from ddw.config import get_config_value
from ddw.models import Tweet
import logging


logger = logging.getLogger()


SCREEN_NAME = "diddukewin"
MIN_HOURS_BETWEEN_TWEETS = int(os.getenv("MIN_HOURS_BETWEEN_TWEETS", 8))


def get_latest_tweet(api) -> dict:
    statuses = api.GetUserTimeline(screen_name=SCREEN_NAME, count=1)
    status = statuses[0]
    return {"text": status.text, "created_at": status.created_at}


def post_tweet(tweet_text: str):
    api = twitter.Api(
        consumer_key=get_config_value("TWITTER_CONSUMER_KEY"),
        consumer_secret=get_config_value("TWITTER_CONSUMER_SECRET"),
        access_token_key=get_config_value("TWITTER_ACCESS_TOKEN_KEY"),
        access_token_secret=get_config_value("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    latest_tweet_dict = get_latest_tweet(api)
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

    api.PostUpdate(tweet_text)
    logger.info(f"Posted tweet: {tweet_text}")
