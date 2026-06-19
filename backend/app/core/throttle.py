# backend/app/core/throttle.py
from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock


class LoginThrottle:
    """In-memory throttle. Single-process MVP; swap for redis if scaled."""

    def __init__(self, max_attempts: int = 5, window: timedelta = timedelta(minutes=15)) -> None:
        self.max_attempts = max_attempts
        self.window = window
        self._buckets: dict[str, deque[datetime]] = {}
        self._lock = Lock()

    def _prune(self, key: str, now: datetime) -> None:
        dq = self._buckets.setdefault(key, deque())
        while dq and (now - dq[0]) > self.window:
            dq.popleft()

    def record_failure(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            self._buckets[key].append(now)

    def record_success(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)

    def is_blocked(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            return len(self._buckets.get(key, ())) >= self.max_attempts
