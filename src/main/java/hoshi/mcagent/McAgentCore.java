package hoshi.mcagent;

import hoshi.mcagent.async.AsyncQueryDispatcher;
import hoshi.mcagent.cache.QueryCache;
import hoshi.mcagent.command.CommandResult;
import hoshi.mcagent.command.CommandRouter;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.engine.PromptSafetyFence;
import hoshi.mcagent.security.PlayerRateLimiter;
import hoshi.mcagent.session.PlayerSessionManager;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Function;

/**
 * Main entry point and facade for the McAgentCore subsystem (v1.6.0).
 * Exposes non-blocking asynchronous dispatch, caching, rate limiting, session memory,
 * full game-state context awareness, recipe crafting checker, and in-game command routing.
 */
public class McAgentCore {

    private final AsyncQueryDispatcher dispatcher;
    private final PlayerSessionManager sessionManager;
    private final CommandRouter commandRouter;

    public McAgentCore(
            ExecutorService executor,
            Function<PromptSafetyFence.FencedPrompt, String> llmInvoker,
            QueryCache cache,
            PlayerRateLimiter rateLimiter,
            PlayerSessionManager sessionManager
    ) {
        this.dispatcher = new AsyncQueryDispatcher(executor, llmInvoker, cache, rateLimiter);
        this.sessionManager = sessionManager != null ? sessionManager : new PlayerSessionManager();
        this.commandRouter = new CommandRouter(this, this.sessionManager);
    }

    public McAgentCore(
            ExecutorService executor,
            Function<PromptSafetyFence.FencedPrompt, String> llmInvoker,
            QueryCache cache,
            PlayerRateLimiter rateLimiter
    ) {
        this(executor, llmInvoker, cache, rateLimiter, null);
    }

    public McAgentCore(ExecutorService executor, Function<PromptSafetyFence.FencedPrompt, String> llmInvoker) {
        this(executor, llmInvoker, null, null, null);
    }

    public McAgentCore() {
        this(null, null, null, null, null);
    }

    public CompletableFuture<AsyncQueryDispatcher.QueryResult> query(String playerId, String prompt, ContextSnapshot snapshot) {
        return dispatcher.dispatchAsync(playerId, prompt, snapshot);
    }

    public CompletableFuture<AsyncQueryDispatcher.QueryResult> query(String prompt, ContextSnapshot snapshot) {
        return dispatcher.dispatchAsync(prompt, snapshot);
    }

    public CommandResult handleCommand(String playerId, String rawCommand, ContextSnapshot snapshot) {
        return commandRouter.execute(playerId, rawCommand, snapshot);
    }

    public AsyncQueryDispatcher getDispatcher() {
        return dispatcher;
    }

    public CommandRouter getCommandRouter() {
        return commandRouter;
    }

    public PlayerSessionManager getSessionManager() {
        return sessionManager;
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
