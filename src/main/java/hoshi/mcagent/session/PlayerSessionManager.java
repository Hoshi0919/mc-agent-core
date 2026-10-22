package hoshi.mcagent.session;

import hoshi.mcagent.format.ChatPaginator;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Thread-safe registry and lifecycle manager for all online/active player sessions.
 */
public class PlayerSessionManager {

    private final ConcurrentHashMap<String, PlayerSession> sessions = new ConcurrentHashMap<>();
    private final int maxHistoryTurns;
    private final long sessionTtlMs;

    public PlayerSessionManager(int maxHistoryTurns, long sessionTtlMs) {
        this.maxHistoryTurns = Math.max(1, maxHistoryTurns);
        this.sessionTtlMs = Math.max(1000L, sessionTtlMs);
    }

    public PlayerSessionManager() {
        this(5, 15 * 60 * 1000L); // 5 turns, 15 minutes TTL
    }

    public PlayerSession getOrCreateSession(String playerId) {
        String id = playerId != null ? playerId : "global";
        return sessions.computeIfAbsent(id, k -> new PlayerSession(k, maxHistoryTurns));
    }

    public Optional<PlayerSession> getSession(String playerId) {
        if (playerId == null) return Optional.empty();
        return Optional.ofNullable(sessions.get(playerId));
    }

    public void recordInteraction(String playerId, String prompt, String response, String category, ChatPaginator.PagedResult paged) {
        PlayerSession session = getOrCreateSession(playerId);
        session.recordTurn(prompt, response, category, paged);
    }

    public Optional<ChatPaginator.PagedResult> getPage(String playerId, int pageNumber) {
        PlayerSession session = sessions.get(playerId);
        if (session == null) {
            return Optional.empty();
        }
        return session.getPage(pageNumber);
    }

    public void clearSession(String playerId) {
        if (playerId != null) {
            PlayerSession session = sessions.remove(playerId);
            if (session != null) {
                session.clear();
            }
        }
    }

    public int cleanupExpiredSessions() {
        long now = System.currentTimeMillis();
        int evicted = 0;
        Iterator<Map.Entry<String, PlayerSession>> it = sessions.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, PlayerSession> entry = it.next();
            if (entry.getValue().isExpired(sessionTtlMs, now)) {
                it.remove();
                evicted++;
            }
        }
        return evicted;
    }

    public int getActiveSessionCount() {
        return sessions.size();
    }
}
