package hoshi.mcagent.cache;

import hoshi.mcagent.async.AsyncQueryDispatcher.QueryResult;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Thread-safe LRU query cache with TTL (Time-To-Live) eviction.
 * Eliminates duplicate fast-path evaluations and redundant remote LLM calls in Minecraft servers.
 */
public final class QueryCache {

    public record CacheStats(
            long hits,
            long misses,
            int size,
            int capacity,
            long ttlMillis
    ) {
        public double hitRatio() {
            long total = hits + misses;
            return total == 0 ? 0.0 : (double) hits / total;
        }
    }

    private static final class CacheEntry {
        final QueryResult result;
        final long expiresAt;

        CacheEntry(QueryResult result, long expiresAt) {
            this.result = result;
            this.expiresAt = expiresAt;
        }
    }

    private final int capacity;
    private final long ttlMillis;
    private final Map<String, CacheEntry> store;

    private long hitCount = 0;
    private long missCount = 0;

    public QueryCache(int capacity, long ttlMillis) {
        this.capacity = capacity > 0 ? capacity : 256;
        this.ttlMillis = ttlMillis > 0 ? ttlMillis : 600_000L; // default 10 mins

        this.store = new LinkedHashMap<>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, CacheEntry> eldest) {
                return size() > QueryCache.this.capacity;
            }
        };
    }

    public synchronized Optional<QueryResult> get(String key) {
        if (key == null) {
            missCount++;
            return Optional.empty();
        }

        String normKey = key.trim().toLowerCase();
        CacheEntry entry = store.get(normKey);
        if (entry == null) {
            missCount++;
            return Optional.empty();
        }

        long now = System.currentTimeMillis();
        if (now > entry.expiresAt) {
            store.remove(normKey);
            missCount++;
            return Optional.empty();
        }

        hitCount++;
        return Optional.of(entry.result);
    }

    public synchronized void put(String key, QueryResult result) {
        if (key == null || result == null) return;
        String normKey = key.trim().toLowerCase();
        long expiresAt = System.currentTimeMillis() + ttlMillis;
        store.put(normKey, new CacheEntry(result, expiresAt));
    }

    public synchronized boolean containsValid(String key) {
        if (key == null) return false;
        CacheEntry entry = store.get(key.trim().toLowerCase());
        return entry != null && System.currentTimeMillis() <= entry.expiresAt;
    }

    public synchronized void invalidate(String key) {
        if (key != null) {
            store.remove(key.trim().toLowerCase());
        }
    }

    public synchronized void clear() {
        store.clear();
        hitCount = 0;
        missCount = 0;
    }

    public synchronized CacheStats getStats() {
        return new CacheStats(hitCount, missCount, store.size(), capacity, ttlMillis);
    }
}
