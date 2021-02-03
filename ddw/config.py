import os


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))


def use_redis() -> bool:
    return bool(os.getenv("USE_REDIS"))
