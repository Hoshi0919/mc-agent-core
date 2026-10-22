import time
from dataclasses import dataclass
from typing import Callable, List, Optional
from .cache import QueryCache
from .context import ContextSnapshot
from .fast_path import FastPathResolver
from .fence import PromptSafetyFence, FencedPrompt
from .formatter import MinecraftTextFormatter, ChatComponent
from .rate_limiter import PlayerRateLimiter


@dataclass(frozen=True)
class QueryResult:
    raw_answer: str
    suggested_command: Optional[str]
    category: str
    is_fast_path: bool
    components: List[ChatComponent]
    processing_time_ms: float


class AsyncQueryDispatcher:
    def __init__(
        self,
        llm_invoker: Optional[Callable[[FencedPrompt], str]] = None,
        cache: Optional[QueryCache] = None,
        rate_limiter: Optional[PlayerRateLimiter] = None,
    ):
        self.llm_invoker = (
            llm_invoker
            if llm_invoker
            else (lambda p: f"LLM Mock: Received prompt with {len(p.user_prompt)} chars.")
        )
        self.cache = cache if cache is not None else QueryCache(capacity=256, ttl_millis=600_000)
        self.rate_limiter = rate_limiter if rate_limiter is not None else PlayerRateLimiter(min_interval_ms=2000, burst_capacity=2)

    def dispatch(
        self,
        raw_query: str,
        context: Optional[ContextSnapshot] = None,
        player_id: str = "player",
    ) -> QueryResult:
        start_time = time.perf_counter()

        # 1. Rate Limiting Check
        if self.rate_limiter is not None:
            limit = self.rate_limiter.check_and_consume(player_id)
            if not limit.is_allowed:
                components = MinecraftTextFormatter.parse_components(limit.message, None)
                return QueryResult(
                    raw_answer=limit.message,
                    suggested_command=None,
                    category="RATE_LIMITED",
                    is_fast_path=True,
                    components=components,
                    processing_time_ms=0.0,
                )

        # 2. Query Cache Check
        cache_key = (raw_query or "").strip().lower() + (f"@{context.dimension}" if context and context.dimension else "")
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # 3. Fast Path
        fast_res = FastPathResolver.try_resolve(raw_query, context)
        if fast_res:
            components = MinecraftTextFormatter.parse_components(
                fast_res.text_response, fast_res.suggested_command
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            query_result = QueryResult(
                raw_answer=fast_res.text_response,
                suggested_command=fast_res.suggested_command,
                category=fast_res.category,
                is_fast_path=True,
                components=components,
                processing_time_ms=elapsed_ms,
            )
            if self.cache is not None:
                self.cache.put(cache_key, query_result)
            return query_result

        # 4. Build Fenced Prompt
        fenced = PromptSafetyFence.build(raw_query, context)

        # 5. LLM Inference
        llm_resp = self.llm_invoker(fenced)

        # 6. Format
        components = MinecraftTextFormatter.parse_components(llm_resp, None)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        query_result = QueryResult(
            raw_answer=llm_resp,
            suggested_command=None,
            category="LLM_INFERENCE",
            is_fast_path=False,
            components=components,
            processing_time_ms=elapsed_ms,
        )
        if self.cache is not None:
            self.cache.put(cache_key, query_result)
        return query_result
