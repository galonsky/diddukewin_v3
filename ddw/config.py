import os


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))


def should_toot() -> bool:
    return bool(os.getenv("TOOTING_ENABLED"))


def should_skeet() -> bool:
    return bool(os.getenv("SKEETING_ENABLED"))


def should_force_upload() -> bool:
    return bool(os.getenv("FORCE_UPLOAD"))


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


MIN_POLL_SECONDS = 10  # NCAA's Akamai edge caches the scoreboard for 10s


def live_poll_seconds() -> int:
    return max(MIN_POLL_SECONDS, _int_env("LIVE_POLL_SECONDS", 15))


def pregame_window_minutes() -> int:
    return _int_env("PREGAME_WINDOW_MINUTES", 12)


def pregame_grace_minutes() -> int:
    return _int_env("PREGAME_GRACE_MINUTES", 45)


def max_run_hours() -> int:
    return _int_env("MAX_RUN_HOURS", 4)
