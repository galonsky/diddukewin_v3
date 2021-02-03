import os


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))

