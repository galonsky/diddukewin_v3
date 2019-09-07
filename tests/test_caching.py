from unittest.mock import MagicMock

import pytest

from ddw import caching


@pytest.fixture
def r_mock():
    return MagicMock()


@pytest.fixture
def redis_cache(r_mock):
    return caching.RedisCache.factory(r_mock)


class TestSetCache:
    def test_serializes_and_sets(self, redis_cache, r_mock):
        redis_cache.set_cache("key", {"foo": "bar"}, 30)
        r_mock.set.assert_called_with(name="key", value='{"foo": "bar"}', ex=30)


class TestGetCache:
    def test_when_none_returns_none(self, redis_cache, r_mock):
        r_mock.get.return_value = None
        assert redis_cache.get_cache("key") is None

    def test_when_not_none_deserializes(self, redis_cache, r_mock):
        r_mock.get.return_value = '{"foo": "bar"}'
        assert redis_cache.get_cache("key") == {"foo": "bar"}


class TestCacheResult:
    @pytest.fixture
    def mock_function(self):
        return MagicMock(return_value={"foo": "bar"})

    def test_when_not_in_cache_sets_cache_and_returns(
        self, mock_function, redis_cache, r_mock
    ):
        r_mock.get.return_value = None
        assert redis_cache.cache_result("key", 30)(mock_function)() == {"foo": "bar"}
        mock_function.assert_called_once_with()
        r_mock.set.assert_called_with(name="key", value='{"foo": "bar"}', ex=30)

    def test_when_in_cache_returns_cached_and_doesnt_call(
        self, mock_function, redis_cache, r_mock
    ):
        r_mock.get.return_value = '{"foo": "bar"}'
        assert redis_cache.cache_result("key", 30)(mock_function)() == {"foo": "bar"}
        mock_function.assert_not_called()
        r_mock.set.assert_not_called()


class TestInvalidate:
    def test_calls_delete(self, redis_cache, r_mock):
        redis_cache.invalidate("foo")
        r_mock.delete.assert_called_once_with("foo")
