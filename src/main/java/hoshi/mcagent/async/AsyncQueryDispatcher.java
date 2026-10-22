package hoshi.mcagent.async;

import hoshi.mcagent.cache.QueryCache;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.engine.FastPathResolver;
import hoshi.mcagent.engine.PromptSafetyFence;
import hoshi.mcagent.format.MinecraftTextFormatter;
import hoshi.mcagent.security.PlayerRateLimiter;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ForkJoinPool;
import java.util.function.Function;

/**
 * Handles non-blocking asynchronous dispatch between the Minecraft 20-TPS loop and AI engines.
 * Integrates LRU caching and token-bucket player rate limiting.
 */
public final class AsyncQueryDispatcher {

    public record QueryResult(
            String rawAnswer,
            String suggestedCommand,
            String category,
            boolean isFastPath,
            List<MinecraftTextFormatter.ChatComponent> components,
            long processingTimeMs
    ) {}

    private final ExecutorService workerExecutor;
    private final Function<PromptSafetyFence.FencedPrompt, String> llmInvoker;
    private final QueryCache cache;
    private final PlayerRateLimiter rateLimiter;

    public AsyncQueryDispatcher(
            ExecutorService executor,
            Function<PromptSafetyFence.FencedPrompt, String> llmInvoker,
            QueryCache cache,
            PlayerRateLimiter rateLimiter
    ) {
        this.workerExecutor = executor != null ? executor : ForkJoinPool.commonPool();
        this.llmInvoker = llmInvoker != null ? llmInvoker : (p -> "LLM Mock: Received prompt with " + p.userPrompt().length() + " chars.");
        this.cache = cache != null ? cache : new QueryCache(256, 600_000L);
        this.rateLimiter = rateLimiter != null ? rateLimiter : new PlayerRateLimiter(2000L, 2);
    }

    public AsyncQueryDispatcher(ExecutorService executor, Function<PromptSafetyFence.FencedPrompt, String> llmInvoker) {
        this(executor, llmInvoker, new QueryCache(256, 600_000L), new PlayerRateLimiter(2000L, 2));
    }

    public QueryCache getCache() {
        return cache;
    }

    public PlayerRateLimiter getRateLimiter() {
        return rateLimiter;
    }

    /**
     * Dispatches query processing with player-aware rate limiting and query caching.
     */
    public CompletableFuture<QueryResult> dispatchAsync(String playerId, String rawQuery, ContextSnapshot context) {
        long startTime = System.currentTimeMillis();

        // 1. Rate Limiting Check
        if (rateLimiter != null) {
            var limit = rateLimiter.checkAndConsume(playerId);
            if (!limit.isAllowed()) {
                var components = MinecraftTextFormatter.parseComponents(limit.message(), null);
                return CompletableFuture.completedFuture(
                        new QueryResult(limit.message(), null, "RATE_LIMITED", true, components, 0L)
                );
            }
        }

        // 2. Query Cache Check (Instant 0ms hit for recurring questions)
        String cacheKey = buildCacheKey(rawQuery, context);
        if (cache != null) {
            var cached = cache.get(cacheKey);
            if (cached.isPresent()) {
                return CompletableFuture.completedFuture(cached.get());
            }
        }

        // 3. Worker Execution
        return CompletableFuture.supplyAsync(() -> {
            // Fast-Path Resolution
            var fastPath = FastPathResolver.tryResolve(rawQuery, context);
            if (fastPath.isPresent()) {
                var res = fastPath.get();
                var components = MinecraftTextFormatter.parseComponents(res.textResponse(), res.suggestedCommand());
                long elapsed = System.currentTimeMillis() - startTime;
                var queryResult = new QueryResult(res.textResponse(), res.suggestedCommand(), res.category(), true, components, elapsed);
                if (cache != null) {
                    cache.put(cacheKey, queryResult);
                }
                return queryResult;
            }

            // LLM Remote Inference with Safety Fence
            var fenced = PromptSafetyFence.build(rawQuery, context);
            String llmResponse = llmInvoker.apply(fenced);
            var components = MinecraftTextFormatter.parseComponents(llmResponse, null);
            long elapsed = System.currentTimeMillis() - startTime;
            var queryResult = new QueryResult(llmResponse, null, "LLM_INFERENCE", false, components, elapsed);
            if (cache != null) {
                cache.put(cacheKey, queryResult);
            }
            return queryResult;
        }, workerExecutor);
    }

    /**
     * Backward-compatible overload for anonymous or single-player queries.
     */
    public CompletableFuture<QueryResult> dispatchAsync(String rawQuery, ContextSnapshot context) {
        return dispatchAsync("player", rawQuery, context);
    }

    private String buildCacheKey(String rawQuery, ContextSnapshot context) {
        String queryPart = rawQuery == null ? "" : rawQuery.trim().toLowerCase();
        String dimPart = context != null && context.dimension() != null ? "@" + context.dimension() : "";
        return queryPart + dimPart;
    }
}
