import os
import twitter


api = twitter.Api(
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token_key=os.getenv("TWITTER_ACCESS_TOKEN_KEY"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

SCREEN_NAME = "diddukewin"


def get_latest_tweet():
    statuses = api.GetUserTimeline(screen_name=SCREEN_NAME, count=1)
    status = statuses[0]
    return {"text": status.text, "created_at": status.created_at}
