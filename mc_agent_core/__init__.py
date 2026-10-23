"""
mc_agent_core: Grounded, Non-blocking In-Game AI Assistant Core for Minecraft (1.18 ~ 1.21.x)
"""

from .context import ContextSnapshot, TargetBlock, ItemInstance, InventorySnapshot, TargetEntity, LogisticsReport
from .rules import (
    LocalGameRules,
    VILLAGER_BREEDING_RULES,
    VILLAGER_CROP_FARM_RULES,
    SMELTING_FUEL_EFFICIENCY_RULES,
    ZOMBIE_VILLAGER_CURE_RULES,
    IRON_GOLEM_REPAIR_RULES,
    ARMADILLO_WOLF_ARMOR_RULES,
    TRIAL_SPAWNER_BREEZE_RULES,
    HOPPER_LOGISTICS_SORTING_RULES,
    COMPARATOR_SUBTRACTION_ALGEBRA_RULES,
    WATER_BUBBLE_COLUMN_ELEVATOR_RULES,
    OBSERVER_PULSE_CLOCKS_RULES,
    CONDUIT_MULTIBLOCK_ACTIVATION_RULES,
    NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD_RULES,
    SMELTING_ARRAY_THROUGHPUT_BOTTLENECK_RULES,
    HOPPER_MINECART_UNLOADER_DYNAMICS_RULES,
)
from .multiblock import MultiblockBlueprint, MultiblockReport, find_blueprint, validate_inventory
from .pipeline import PipelineReport, analyze_smelting_array
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
    "LogisticsReport",
    "LocalGameRules",
    "VILLAGER_BREEDING_RULES",
    "VILLAGER_CROP_FARM_RULES",
    "SMELTING_FUEL_EFFICIENCY_RULES",
    "ZOMBIE_VILLAGER_CURE_RULES",
    "IRON_GOLEM_REPAIR_RULES",
    "ARMADILLO_WOLF_ARMOR_RULES",
    "TRIAL_SPAWNER_BREEZE_RULES",
    "HOPPER_LOGISTICS_SORTING_RULES",
    "COMPARATOR_SUBTRACTION_ALGEBRA_RULES",
    "WATER_BUBBLE_COLUMN_ELEVATOR_RULES",
    "OBSERVER_PULSE_CLOCKS_RULES",
    "CONDUIT_MULTIBLOCK_ACTIVATION_RULES",
    "NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD_RULES",
    "SMELTING_ARRAY_THROUGHPUT_BOTTLENECK_RULES",
    "HOPPER_MINECART_UNLOADER_DYNAMICS_RULES",
    "MultiblockBlueprint",
    "MultiblockReport",
    "find_blueprint",
    "validate_inventory",
    "PipelineReport",
    "analyze_smelting_array",
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
