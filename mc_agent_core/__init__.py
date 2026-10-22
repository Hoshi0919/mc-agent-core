"""
mc_agent_core: Grounded, Non-blocking In-Game AI Assistant Core for Minecraft (1.18 ~ 1.21.x)
"""

from .context import ContextSnapshot, TargetBlock, ItemInstance, InventorySnapshot, TargetEntity
from .rules import (
    LocalGameRules,
    VILLAGER_BREEDING_RULES,
    VILLAGER_CROP_FARM_RULES,
    SMELTING_FUEL_EFFICIENCY_RULES,
    ZOMBIE_VILLAGER_CURE_RULES,
    IRON_GOLEM_REPAIR_RULES,
    ARMADILLO_WOLF_ARMOR_RULES,
    TRIAL_SPAWNER_BREEZE_RULES,
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
from .crafting import CraftingRecipe, CraftingReadinessChecker

__all__ = [
    "ContextSnapshot",
    "TargetBlock",
    "ItemInstance",
    "InventorySnapshot",
    "TargetEntity",
    "LocalGameRules",
    "VILLAGER_BREEDING_RULES",
    "VILLAGER_CROP_FARM_RULES",
    "SMELTING_FUEL_EFFICIENCY_RULES",
    "ZOMBIE_VILLAGER_CURE_RULES",
    "IRON_GOLEM_REPAIR_RULES",
    "ARMADILLO_WOLF_ARMOR_RULES",
    "TRIAL_SPAWNER_BREEZE_RULES",
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
    "CraftingRecipe",
    "CraftingReadinessChecker",
]
