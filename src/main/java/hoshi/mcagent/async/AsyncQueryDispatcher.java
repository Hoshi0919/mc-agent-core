package hoshi.mcagent.async;

import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.engine.FastPathResolver;
import hoshi.mcagent.engine.PromptSafetyFence;
import hoshi.mcagent.format.MinecraftTextFormatter;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ForkJoinPool;
import java.util.function.Function;

/**
 * Handles non-blocking asynchronous dispatch between the Minecraft 20-TPS loop and AI engines.
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

    public AsyncQueryDispatcher(ExecutorService executor, Function<PromptSafetyFence.FencedPrompt, String> llmInvoker) {
        this.workerExecutor = executor != null ? executor : ForkJoinPool.commonPool();
        this.llmInvoker = llmInvoker != null ? llmInvoker : (p -> "LLM Mock: Received prompt with " + p.userPrompt().length() + " chars.");
    }

    /**
     * Dispatches query processing to the worker pool.
     * Guaranteed to NOT block the Minecraft main thread.
     */
    public CompletableFuture<QueryResult> dispatchAsync(String rawQuery, ContextSnapshot context) {
        long startTime = System.currentTimeMillis();

        return CompletableFuture.supplyAsync(() -> {
            // 1. Fast-Path Resolution (0ms local calculation, saves token & latency)
            var fastPath = FastPathResolver.tryResolve(rawQuery, context);
            if (fastPath.isPresent()) {
                var res = fastPath.get();
                var components = MinecraftTextFormatter.parseComponents(res.textResponse(), res.suggestedCommand());
                long elapsed = System.currentTimeMillis() - startTime;
                return new QueryResult(res.textResponse(), res.suggestedCommand(), res.category(), true, components, elapsed);
            }

            // 2. Build Fenced Prompt (Prompt Injection Protection & RAG Grounding)
            var fenced = PromptSafetyFence.build(rawQuery, context);

            // 3. Invoke LLM provider via network I/O
            String llmResponse = llmInvoker.apply(fenced);

            // 4. Format into Minecraft Text Components
            var components = MinecraftTextFormatter.parseComponents(llmResponse, null);
            long elapsed = System.currentTimeMillis() - startTime;

            return new QueryResult(llmResponse, null, "LLM_INFERENCE", false, components, elapsed);
        }, workerExecutor);
    }
}
