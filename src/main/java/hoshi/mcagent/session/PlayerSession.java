package hoshi.mcagent.session;

import hoshi.mcagent.format.ChatPaginator;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;

/**
 * Stateful conversation memory and active pagination context for an individual Minecraft player.
 */
public class PlayerSession {

    public static class Turn {
        private final String prompt;
        private final String response;
        private final String category;
        private final long timestampMs;

        public Turn(String prompt, String response, String category, long timestampMs) {
            this.prompt = prompt;
            this.response = response;
            this.category = category;
            this.timestampMs = timestampMs;
        }

        public String getPrompt() { return prompt; }
        public String getResponse() { return response; }
        public String getCategory() { return category; }
        public long getTimestampMs() { return timestampMs; }
    }

    private final String playerId;
    private final int maxHistoryTurns;
    private final Deque<Turn> history = new ConcurrentLinkedDeque<>();
    private volatile ChatPaginator.PagedResult activePagedResult;
    private volatile String lastActiveTopic;
    private volatile long lastActiveTimeMs;

    public PlayerSession(String playerId, int maxHistoryTurns) {
        this.playerId = Objects.requireNonNull(playerId, "playerId");
        this.maxHistoryTurns = Math.max(1, maxHistoryTurns);
        this.lastActiveTimeMs = System.currentTimeMillis();
    }

    public String getPlayerId() {
        return playerId;
    }

    public synchronized void recordTurn(String prompt, String response, String category, ChatPaginator.PagedResult paged) {
        this.lastActiveTimeMs = System.currentTimeMillis();
        if (category != null && !category.isEmpty()) {
            this.lastActiveTopic = category;
        }
        if (paged != null) {
            this.activePagedResult = paged;
        }
        history.addLast(new Turn(prompt, response, category, this.lastActiveTimeMs));
        while (history.size() > maxHistoryTurns) {
            history.pollFirst();
        }
    }

    public synchronized void setActivePagedResult(ChatPaginator.PagedResult paged) {
        this.activePagedResult = paged;
        this.lastActiveTimeMs = System.currentTimeMillis();
    }

    public synchronized Optional<ChatPaginator.PagedResult> getActivePagedResult() {
        return Optional.ofNullable(activePagedResult);
    }

    /**
     * Retrieves or re-slices a specific page from the currently active paged result.
     */
    public synchronized Optional<ChatPaginator.PagedResult> getPage(int targetPage) {
        if (activePagedResult == null) {
            return Optional.empty();
        }
        if (activePagedResult.currentPage() == targetPage) {
            return Optional.of(activePagedResult);
        }
        ChatPaginator.PagedResult newPage = ChatPaginator.paginate(
                activePagedResult.originalText(),
                targetPage,
                activePagedResult.pageSize(),
                activePagedResult.commandPrefix()
        );
        this.activePagedResult = newPage;
        this.lastActiveTimeMs = System.currentTimeMillis();
        return Optional.of(newPage);
    }

    public synchronized List<Turn> getHistory() {
        return new ArrayList<>(history);
    }

    public synchronized String getLastActiveTopic() {
        return lastActiveTopic;
    }

    public synchronized void setLastActiveTopic(String topic) {
        this.lastActiveTopic = topic;
    }

    public long getLastActiveTimeMs() {
        return lastActiveTimeMs;
    }

    public synchronized void clear() {
        history.clear();
        activePagedResult = null;
        lastActiveTopic = null;
        lastActiveTimeMs = System.currentTimeMillis();
    }

    public boolean isExpired(long ttlMs, long nowMs) {
        return (nowMs - lastActiveTimeMs) > ttlMs;
    }
}
