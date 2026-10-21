package hoshi.mcagent;

import hoshi.mcagent.async.AsyncQueryDispatcher;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.engine.PromptSafetyFence;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Function;

/**
 * Main entry point and facade for the McAgentCore subsystem.
 */
public class McAgentCore {

    private final AsyncQueryDispatcher dispatcher;

    public McAgentCore(ExecutorService executor, Function<PromptSafetyFence.FencedPrompt, String> llmInvoker) {
        this.dispatcher = new AsyncQueryDispatcher(executor, llmInvoker);
    }

    public CompletableFuture<AsyncQueryDispatcher.QueryResult> query(String prompt, ContextSnapshot snapshot) {
        return dispatcher.dispatchAsync(prompt, snapshot);
    }

    public static TargetBlock createTargetBlock(String blockId, int x, int y, int z, int blockLight, int skyLight, float hardness, String tool) {
        return new TargetBlock(blockId, x, y, z, blockLight, skyLight, hardness, tool, null);
    }
}
