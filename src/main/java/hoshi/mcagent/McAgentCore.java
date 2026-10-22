package hoshi.mcagent;

import hoshi.mcagent.async.AsyncQueryDispatcher;
import hoshi.mcagent.cache.QueryCache;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.engine.PromptSafetyFence;
import hoshi.mcagent.security.PlayerRateLimiter;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Function;

/**
 * Main entry point and facade for the McAgentCore subsystem.
 * Exposes non-blocking asynchronous dispatch, caching, rate limiting, and Minecraft text builders.
 */
public class McAgentCore {

    private final AsyncQueryDispatcher dispatcher;

    public McAgentCore(
            ExecutorService executor,
            Function<PromptSafetyFence.FencedPrompt, String> llmInvoker,
            QueryCache cache,
            PlayerRateLimiter rateLimiter
    ) {
        this.dispatcher = new AsyncQueryDispatcher(executor, llmInvoker, cache, rateLimiter);
    }

    public McAgentCore(ExecutorService executor, Function<PromptSafetyFence.FencedPrompt, String> llmInvoker) {
        this.dispatcher = new AsyncQueryDispatcher(executor, llmInvoker);
    }

    public McAgentCore() {
        this(null, null);
    }

    public CompletableFuture<AsyncQueryDispatcher.QueryResult> query(String playerId, String prompt, ContextSnapshot snapshot) {
        return dispatcher.dispatchAsync(playerId, prompt, snapshot);
    }

    public CompletableFuture<AsyncQueryDispatcher.QueryResult> query(String prompt, ContextSnapshot snapshot) {
        return dispatcher.dispatchAsync(prompt, snapshot);
    }

    public QueryCache getCache() {
        return dispatcher.getCache();
    }

    public PlayerRateLimiter getRateLimiter() {
        return dispatcher.getRateLimiter();
    }

    public static TargetBlock createTargetBlock(String blockId, int x, int y, int z, int blockLight, int skyLight, float hardness, String tool) {
        return new TargetBlock(blockId, x, y, z, blockLight, skyLight, hardness, tool, null);
    }
}
