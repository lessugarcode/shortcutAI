"""
Right Click AI — Rate Limiter
Simple in-memory token-bucket rate limiter. No external dependencies.
"""

import time
import threading
from collections import defaultdict


class TokenBucketRateLimiter:
    """
    Token-bucket rate limiter keyed by a string (e.g. client IP).
    
    Each bucket refills at `rate` tokens per second, up to `capacity`.
    Each request consumes 1 token. Excess requests are rejected.
    """

    def __init__(self, rate: float = 0.5, capacity: int = 30):
        """
        Args:
            rate: Tokens refilled per second (0.5 = 30 per minute).
            capacity: Maximum tokens in bucket.
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, float] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """
        Check whether a request from `key` is allowed.
        Returns True if allowed, False if rate-limited.
        """
        now = time.monotonic()
        with self._lock:
            tokens = self._buckets.get(key, self.capacity)
            # Refill
            elapsed = now - getattr(self, "_last_refill", now)
            if elapsed > 0:
                tokens = min(self.capacity, tokens + elapsed * self.rate)
            tokens -= 1
            if tokens >= 0:
                self._buckets[key] = tokens
                return True
            else:
                self._buckets[key] = 0
                return False

    def reset(self, key: str):
        """Reset the bucket for a given key."""
        with self._lock:
            self._buckets.pop(key, None)


# Global singleton: 30 requests per minute per IP
rate_limiter = TokenBucketRateLimiter(rate=0.5, capacity=30)
