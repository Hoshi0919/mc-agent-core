import time
from dataclasses import dataclass
from typing import Callable, List, Optional
from .context import ContextSnapshot
from .fast_path import FastPathResolver
from .fence import PromptSafetyFence, FencedPrompt
from .formatter import MinecraftTextFormatter, ChatComponent


@dataclass(frozen=True)
class QueryResult:
    raw_answer: str
    suggested_command: Optional[str]
    category: str
    is_fast_path: bool
    components: List[ChatComponent]
    processing_time_ms: float


class AsyncQueryDispatcher:
    def __init__(self, llm_invoker: Optional[Callable[[FencedPrompt], str]] = None):
        self.llm_invoker = (
            llm_invoker
            if llm_invoker
            else (lambda p: f"LLM Mock: Received prompt with {len(p.user_prompt)} chars.")
        )

    def dispatch(self, raw_query: str, context: Optional[ContextSnapshot]) -> QueryResult:
        start_time = time.perf_counter()

        # 1. Fast Path
        fast_res = FastPathResolver.try_resolve(raw_query, context)
        if fast_res:
            components = MinecraftTextFormatter.parse_components(
                fast_res.text_response, fast_res.suggested_command
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResult(
                raw_answer=fast_res.text_response,
                suggested_command=fast_res.suggested_command,
                category=fast_res.category,
                is_fast_path=True,
                components=components,
                processing_time_ms=elapsed_ms,
            )

        # 2. Build Fenced Prompt
        fenced = PromptSafetyFence.build(raw_query, context)

        # 3. LLM Inference
        llm_resp = self.llm_invoker(fenced)

        # 4. Format
        components = MinecraftTextFormatter.parse_components(llm_resp, None)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return QueryResult(
            raw_answer=llm_resp,
            suggested_command=None,
            category="LLM_INFERENCE",
            is_fast_path=False,
            components=components,
            processing_time_ms=elapsed_ms,
        )
