import math
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RateLimitResult:
    is_allowed: bool
    remaining_cooldown_ms: int
    message: str


class _PlayerBucket:
    def __init__(self, tokens: float, last_timestamp: float, day_epoch: int):
        self.tokens = tokens
        self.last_timestamp = last_timestamp
        self.daily_requests = 0
        self.day_epoch = day_epoch


class PlayerRateLimiter:
    """
    Per-player Token Bucket rate limiter with daily quota protection.
    """

    def __init__(self, min_interval_ms: int = 2000, burst_capacity: int = 2, daily_quota: int = 100):
        self.min_interval_ms = max(1, min_interval_ms)
        self.burst_capacity = max(1, burst_capacity)
        self.daily_quota = max(1, daily_quota)
        self._buckets: Dict[str, _PlayerBucket] = {}

    def check_and_consume(self, player_id: Optional[str]) -> RateLimitResult:
        pid = player_id.strip() if player_id and player_id.strip() else "anonymous"
        now = time.time() * 1000.0
        current_day = int(now // 86_400_000.0)

        if pid not in self._buckets:
            self._buckets[pid] = _PlayerBucket(
                tokens=float(self.burst_capacity),
                last_timestamp=now,
                day_epoch=current_day,
            )

        bucket = self._buckets[pid]

        # Daily rollover
        if bucket.day_epoch != current_day:
            bucket.daily_requests = 0
            bucket.day_epoch = current_day

        # Daily quota check
        if bucket.daily_requests >= self.daily_quota:
            return RateLimitResult(
                is_allowed=False,
                remaining_cooldown_ms=86_400_000,
                message=f"§c[Hoshi] 玩家 {pid} 今日提问次数已达上限 ({self.daily_quota} 次)，请明日再试！§r",
            )

        # Refill tokens
        elapsed = now - bucket.last_timestamp
        bucket.last_timestamp = now
        refill = elapsed / self.min_interval_ms
        bucket.tokens = min(float(self.burst_capacity), bucket.tokens + refill)

        # Token check
        if bucket.tokens < 1.0:
            wait_ms = int(math.ceil((1.0 - bucket.tokens) * self.min_interval_ms))
            wait_sec = wait_ms / 1000.0
            return RateLimitResult(
                is_allowed=False,
                remaining_cooldown_ms=wait_ms,
                message=f"§c[Hoshi] 提问过快！请等待 {wait_sec:.1f} 秒后再试。§r",
            )

        bucket.tokens -= 1.0
        bucket.daily_requests += 1

        # Periodic cleanup if table grows large
        if len(self._buckets) > 1000:
            self._cleanup_stale(now)

        return RateLimitResult(is_allowed=True, remaining_cooldown_ms=0, message="OK")

    def _cleanup_stale(self, now: float) -> None:
        one_hour = 3_600_000.0
        stale_keys = [k for k, b in self._buckets.items() if now - b.last_timestamp > one_hour]
        for k in stale_keys:
            self._buckets.pop(k, None)

    def reset(self, player_id: Optional[str]) -> None:
        if player_id:
            self._buckets.pop(player_id.strip(), None)

    def clear(self) -> None:
        self._buckets.clear()

    @property
    def tracked_player_count(self) -> int:
        return len(self._buckets)
