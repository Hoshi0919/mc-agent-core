package hoshi.mcagent.security;

import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Token-bucket rate limiter and anti-spam cooldown manager per player (UUID or name).
 * Prevents denial-of-service, token depletion, and chat flooding on dedicated Minecraft servers.
 */
public final class PlayerRateLimiter {

    public record RateLimitResult(
            boolean isAllowed,
            long remainingCooldownMs,
            String message
    ) {}

    private static final class PlayerBucket {
        double tokens;
        long lastTimestamp;
        int dailyRequests;
        long dayEpoch;

        PlayerBucket(double tokens, long lastTimestamp, long dayEpoch) {
            this.tokens = tokens;
            this.lastTimestamp = lastTimestamp;
            this.dailyRequests = 0;
            this.dayEpoch = dayEpoch;
        }
    }

    private final long minIntervalMs;
    private final int burstCapacity;
    private final int dailyQuota;
    private final Map<String, PlayerBucket> buckets = new ConcurrentHashMap<>();

    public PlayerRateLimiter(long minIntervalMs, int burstCapacity, int dailyQuota) {
        this.minIntervalMs = minIntervalMs > 0 ? minIntervalMs : 2000L;
        this.burstCapacity = burstCapacity > 0 ? burstCapacity : 2;
        this.dailyQuota = dailyQuota > 0 ? dailyQuota : 100;
    }

    public PlayerRateLimiter(long minIntervalMs, int burstCapacity) {
        this(minIntervalMs, burstCapacity, 150);
    }

    public synchronized RateLimitResult checkAndConsume(String playerId) {
        String id = (playerId == null || playerId.trim().isEmpty()) ? "anonymous" : playerId.trim();
        long now = System.currentTimeMillis();
        long currentDay = now / 86_400_000L;

        PlayerBucket bucket = buckets.computeIfAbsent(id, k -> new PlayerBucket(burstCapacity, now, currentDay));

        // Reset daily count if day changed
        if (bucket.dayEpoch != currentDay) {
            bucket.dailyRequests = 0;
            bucket.dayEpoch = currentDay;
        }

        // Daily quota check
        if (bucket.dailyRequests >= dailyQuota) {
            return new RateLimitResult(
                    false,
                    86_400_000L,
                    String.format("§c[Hoshi] 玩家 %s 今日提问次数已达上限 (%d 次)，请明日再试！§r", id, dailyQuota)
            );
        }

        // Refill tokens based on elapsed time
        long elapsed = now - bucket.lastTimestamp;
        bucket.lastTimestamp = now;
        double refillTokens = (double) elapsed / minIntervalMs;
        bucket.tokens = Math.min(burstCapacity, bucket.tokens + refillTokens);

        // Check token availability
        if (bucket.tokens < 1.0) {
            long waitMs = (long) Math.ceil((1.0 - bucket.tokens) * minIntervalMs);
            double waitSec = waitMs / 1000.0;
            return new RateLimitResult(
                    false,
                    waitMs,
                    String.format("§c[Hoshi] 提问过快！请等待 %.1f 秒后再试。§r", waitSec)
            );
        }

        // Consume 1 token
        bucket.tokens -= 1.0;
        bucket.dailyRequests++;

        // Periodic maintenance cleanup if table grows large (> 1000 players)
        if (buckets.size() > 1000) {
            cleanupStaleBuckets(now);
        }

        return new RateLimitResult(true, 0, "OK");
    }

    private void cleanupStaleBuckets(long now) {
        long oneHour = 3_600_000L;
        Iterator<Map.Entry<String, PlayerBucket>> it = buckets.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, PlayerBucket> entry = it.next();
            if (now - entry.getValue().lastTimestamp > oneHour) {
                it.remove();
            }
        }
    }

    public synchronized void reset(String playerId) {
        if (playerId != null) {
            buckets.remove(playerId.trim());
        }
    }

    public synchronized void clear() {
        buckets.clear();
    }

    public int getTrackedPlayerCount() {
        return buckets.size();
    }
}
