import os
import twitter

from ddw.caching import cache

api = twitter.Api(
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

SCREEN_NAME = "diddukewin"


@cache.cache_result("latest_tweet", 60 * 5)
def get_latest_tweet() -> dict:
    statuses = api.GetUserTimeline(screen_name=SCREEN_NAME, count=1)
    status = statuses[0]
    return {"text": status.text, "created_at": status.created_at}


def post_tweet():
    latest_tweet = get_latest_tweet()

    # if latest tweet less than X hours ago or same content as this tweet, return
    #
    # invalidate cache
    # tweet
