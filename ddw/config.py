import os
from datetime import datetime, timedelta


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


def idle_poll_seconds() -> int:
    """How often to look for a game when none is live (the old cron interval)."""
    return max(MIN_POLL_SECONDS, _int_env("IDLE_POLL_SECONDS", 600))


def active_start_hour() -> int:
    return _int_env("ACTIVE_START_HOUR", 11) % 24


def active_end_hour() -> int:
    """Exclusive; may be earlier than the start hour to wrap past midnight."""
    return _int_env("ACTIVE_END_HOUR", 2) % 24


def in_active_window(now: datetime) -> bool:
    """Whether idle checks run at this local hour (default 11:00-01:59)."""
    start, end = active_start_hour(), active_end_hour()
    if start == end:
        return True
    if start < end:
        return start <= now.hour < end
    return now.hour >= start or now.hour < end


def seconds_until_active(now: datetime) -> float:
    """Seconds from now until the active window next opens (0 if open now)."""
    if in_active_window(now):
        return 0.0
    opens = now.replace(hour=active_start_hour(), minute=0, second=0, microsecond=0)
    if opens <= now:
        opens += timedelta(days=1)
    return (opens - now).total_seconds()
