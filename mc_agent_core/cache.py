import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    size: int
    capacity: int
    ttl_millis: int

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return 0.0 if total == 0 else self.hits / total


class QueryCache:
    """
    Thread-safe in-memory LRU cache with TTL eviction.
    """

    def __init__(self, capacity: int = 256, ttl_millis: int = 600_000):
        self.capacity = max(1, capacity)
        self.ttl_millis = max(1, ttl_millis)
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: Optional[str]) -> Optional[Any]:
        if not key:
            self._misses += 1
            return None

        norm_key = key.strip().lower()
        if norm_key not in self._store:
            self._misses += 1
            return None

        val, expires_at = self._store[norm_key]
        now = time.time() * 1000.0
        if now > expires_at:
            del self._store[norm_key]
            self._misses += 1
            return None

        self._store.move_to_end(norm_key)
        self._hits += 1
        return val

    def put(self, key: Optional[str], value: Any) -> None:
        if not key or value is None:
            return

        norm_key = key.strip().lower()
        now = time.time() * 1000.0
        expires_at = now + self.ttl_millis

        if norm_key in self._store:
            self._store.move_to_end(norm_key)
        self._store[norm_key] = (value, expires_at)

        if len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def invalidate(self, key: Optional[str]) -> None:
        if key:
            norm_key = key.strip().lower()
            self._store.pop(norm_key, None)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            size=len(self._store),
            capacity=self.capacity,
            ttl_millis=self.ttl_millis,
        )
