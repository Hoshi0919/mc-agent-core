"""
mc_agent_core: Grounded, Non-blocking In-Game AI Assistant Core for Minecraft (1.18 ~ 1.21.x)
"""

from .context import ContextSnapshot, TargetBlock
from .rules import (
    LocalGameRules,
    VILLAGER_BREEDING_RULES,
    VILLAGER_CROP_FARM_RULES,
    SMELTING_FUEL_EFFICIENCY_RULES,
)
from .fast_path import FastPathResolver, Resolution
from .fence import PromptSafetyFence, FencedPrompt
from .formatter import MinecraftTextFormatter, ChatComponent
from .tellraw import TellrawJsonBuilder
from .paginator import ChatPaginator, PagedResult
from .cache import QueryCache, CacheStats
from .rate_limiter import PlayerRateLimiter, RateLimitResult
from .dispatcher import AsyncQueryDispatcher, QueryResult
from .bom import ItemStack, BlueprintBOM, MaterialCalculator
from .session import Turn, PlayerSession, PlayerSessionManager
from .command import CommandResult, CommandRouter

__all__ = [
    "ContextSnapshot",
    "TargetBlock",
    "LocalGameRules",
    "VILLAGER_BREEDING_RULES",
    "VILLAGER_CROP_FARM_RULES",
    "SMELTING_FUEL_EFFICIENCY_RULES",
    "FastPathResolver",
    "Resolution",
    "PromptSafetyFence",
    "FencedPrompt",
    "MinecraftTextFormatter",
    "ChatComponent",
    "TellrawJsonBuilder",
    "ChatPaginator",
    "PagedResult",
    "QueryCache",
    "CacheStats",
    "PlayerRateLimiter",
    "RateLimitResult",
    "AsyncQueryDispatcher",
    "QueryResult",
    "ItemStack",
    "BlueprintBOM",
    "MaterialCalculator",
    "Turn",
    "PlayerSession",
    "PlayerSessionManager",
    "CommandResult",
    "CommandRouter",
]
