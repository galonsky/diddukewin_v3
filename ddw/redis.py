import functools
import os

import redis

from ddw.config import use_redis

r = redis.from_url(os.getenv("REDIS_URL") or "redis://")


def require_lock(name: str, wait_seconds: int):
    def decorator_lock(func):
        @functools.wraps(func)
        def wrapper_lock(*args, **kwargs):
            if not use_redis():
                return func(*args, **kwargs)
            with r.lock(name, blocking_timeout=wait_seconds):
                return func(*args, **kwargs)

        return wrapper_lock

    return decorator_lock
