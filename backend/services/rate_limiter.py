"""
shortcutAI — Rate Limiter
Simple in-memory token-bucket. No external dependencies.
"""

import time
import threading


class TokenBucketRateLimiter:
    """Token-bucket rate limiter. 30 req/min per key."""

    def __init__(self, rate: float = 0.5, capacity: int = 30):
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens = self._buckets.get(key, float(self.capacity))
            last = self._last_refill.get(key, now)
            elapsed = now - last
            tokens = min(self.capacity, tokens + elapsed * self.rate)
            if tokens >= 1:
                self._buckets[key] = tokens - 1
                self._last_refill[key] = now
                return True
            self._buckets[key] = tokens
            self._last_refill[key] = now
            return False

    def reset(self, key: str):
        with self._lock:
            self._buckets.pop(key, None)
            self._last_refill.pop(key, None)


rate_limiter = TokenBucketRateLimiter(rate=0.5, capacity=30)
