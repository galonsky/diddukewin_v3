import functools
import json
from typing import TYPE_CHECKING

from ddw.config import use_redis
from ddw.redis import r


if TYPE_CHECKING:
    from redis import Redis


class RedisCache:
    def __init__(self, r: "Redis"):
        self.r = r

    @classmethod
    def factory(cls, r: "Redis"):
        return cls(r)

    def set_cache(self, key: str, value: dict, ttl_seconds: int = None):
        if not use_redis():
            return
        serialized = json.dumps(value, sort_keys=True)
        self.r.set(name=key, value=serialized, ex=ttl_seconds)

    def get_cache(self, key: str):
        if not use_redis():
            return None
        value_str = self.r.get(name=key)
        if value_str is None:
            return None
        return json.loads(value_str)

    def invalidate(self, key: str):
        return self.r.delete(key)

    def cache_result(self, key: str, ttl_seconds: int):
        def decorator_cache(func):
            @functools.wraps(func)
            def wrapper_cache(*args, **kwargs):
                cached = self.get_cache(key)
                if cached is None:
                    value = func(*args, **kwargs)
                    self.set_cache(key, value, ttl_seconds)
                    return value
                return cached

            return wrapper_cache

        return decorator_cache


cache = RedisCache.factory(r)
