import functools
import os

import redis

r = redis.from_url(os.getenv("REDIS_URL") or "redis://")


def require_lock(name: str, wait_seconds: int):
    def decorator_lock(func):
        @functools.wraps(func)
        def wrapper_lock(*args, **kwargs):
            with r.lock(name, blocking_timeout=wait_seconds):
                return func(*args, **kwargs)

        return wrapper_lock

    return decorator_lock
