# backend/tests/core/test_throttle.py
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from app.core.throttle import LoginThrottle


def test_blocks_after_five_failures():
    t = LoginThrottle(max_attempts=5, window=timedelta(minutes=15))
    for _ in range(5):
        t.record_failure("user@example.com")
    assert t.is_blocked("user@example.com") is True


def test_unblocks_after_window():
    t = LoginThrottle(max_attempts=2, window=timedelta(minutes=1))
    with freeze_time("2026-01-01T00:00:00Z"):
        t.record_failure("a")
        t.record_failure("a")
        assert t.is_blocked("a") is True
    with freeze_time("2026-01-01T00:02:00Z"):
        assert t.is_blocked("a") is False


def test_success_resets():
    t = LoginThrottle(max_attempts=3, window=timedelta(minutes=15))
    t.record_failure("z"); t.record_failure("z")
    t.record_success("z")
    assert t.is_blocked("z") is False
