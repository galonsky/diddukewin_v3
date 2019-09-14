import os
from datetime import datetime, timezone, timedelta

import twitter

from ddw.caching import cache
from ddw.models import Tweet
from ddw.redis import require_lock

api = twitter.Api(
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

SCREEN_NAME = "diddukewin"
MIN_HOURS_BETWEEN_TWEETS = int(os.getenv("MIN_HOURS_BETWEEN_TWEETS", 8))


@cache.cache_result("latest_tweet", 60 * 60)
def get_latest_tweet() -> dict:
    statuses = api.GetUserTimeline(screen_name=SCREEN_NAME, count=1)
    status = statuses[0]
    return {"text": status.text, "created_at": status.created_at}


@require_lock("tweeting-lock", 30)
def post_tweet(tweet_text: str):
    latest_tweet_dict = get_latest_tweet()
    latest_tweet = Tweet.from_tweet_dict(latest_tweet_dict)

    now = datetime.now(timezone.utc)
    time_since_last_tweet = now - latest_tweet.created_at
    hours_since_last_tweet = time_since_last_tweet / timedelta(hours=1)

    if hours_since_last_tweet <= MIN_HOURS_BETWEEN_TWEETS:
        return

    new_tweet = Tweet(tweet_text)
    if latest_tweet.text_without_link == new_tweet.text_without_link:
        return

    cache.invalidate("latest_tweet")
    api.PostUpdate(tweet_text)
