import os


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))


def should_toot() -> bool:
    return bool(os.getenv("TOOTING_ENABLED"))


def should_skeet() -> bool:
    return bool(os.getenv("SKEETING_ENABLED"))
