from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ddw import config

TZ = ZoneInfo("America/New_York")


def at(hour, minute=0):
    return datetime(2026, 11, 3, hour, minute, tzinfo=TZ)


@pytest.mark.parametrize(
    "hour,expected",
    [(10, False), (11, True), (23, True), (0, True), (1, True), (2, False)],
)
def test_default_window_matches_old_cron_hours(hour, expected):
    assert config.in_active_window(at(hour, 59)) is expected


def test_window_without_wrap(monkeypatch):
    monkeypatch.setenv("ACTIVE_START_HOUR", "9")
    monkeypatch.setenv("ACTIVE_END_HOUR", "17")
    assert not config.in_active_window(at(8, 59))
    assert config.in_active_window(at(9))
    assert not config.in_active_window(at(17))


def test_equal_hours_means_always(monkeypatch):
    monkeypatch.setenv("ACTIVE_START_HOUR", "0")
    monkeypatch.setenv("ACTIVE_END_HOUR", "0")
    assert config.in_active_window(at(5))


def test_seconds_until_active():
    assert config.seconds_until_active(at(12)) == 0
    assert config.seconds_until_active(at(10, 30)) == 30 * 60
    assert config.seconds_until_active(at(2)) == 9 * 3600


def test_idle_poll_seconds(monkeypatch):
    assert config.idle_poll_seconds() == 600
    monkeypatch.setenv("IDLE_POLL_SECONDS", "1")
    assert config.idle_poll_seconds() == config.MIN_POLL_SECONDS
