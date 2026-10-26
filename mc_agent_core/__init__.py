from .cluster import (
    BlockPos,
    LocalBlock,
    LocalMachineCluster,
    KineticNetworkAnalyzer,
    HopperNetworkAnalyzer,
    CrafterPipelineAnalyzer,
    KineticReport as ClusterKineticReport,
    HopperReport,
    CrafterReport,
)
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
    HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES_RULES,
    SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION_RULES,
    IRON_FARM_PANIC_AND_LOS_SLEEP_RULES,
    VILLAGER_WORKSTATION_PATHING_AND_RESTOCK_RULES,
    ANVIL_PENALTY_AND_BINARY_TREE_OPTIMIZER_RULES,
    ENCHANTMENT_COMPATIBILITY_AND_GEAR_RULES,
    CREATE_STRESS_CAPACITY_AND_KINETICS_RULES,
    PORTAL_PERMALOADER_AND_CHUNK_TICKING_RULES,
)
from .anvil import EnchantmentEntry, AnvilItem, AnvilMergeStep, AnvilPlan, optimize_anvil_tree, calculate_penalty, get_enchantment
from .create_kinetics import MachineEntry, KineticReport, analyze_create_network, resolve_impact_factor
from .chunkload import AlignmentResult, PermaloaderReport, evaluate_portal_alignment, analyze_permaloader
from .farm import DespawnZone, FarmReport, SpawnerReport, evaluate_mob_farm, evaluate_spawner
from .villager import FarmType as VillagerFarmType, VillagerReport, diagnose_iron_farm, diagnose_breeder, diagnose_trading
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
    "HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES_RULES",
    "SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION_RULES",
    "IRON_FARM_PANIC_AND_LOS_SLEEP_RULES",
    "VILLAGER_WORKSTATION_PATHING_AND_RESTOCK_RULES",
    "DespawnZone",
    "FarmReport",
    "SpawnerReport",
    "evaluate_mob_farm",
    "evaluate_spawner",
    "VillagerFarmType",
    "VillagerReport",
    "diagnose_iron_farm",
    "diagnose_breeder",
    "diagnose_trading",
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
    "ANVIL_PENALTY_AND_BINARY_TREE_OPTIMIZER_RULES",
    "ENCHANTMENT_COMPATIBILITY_AND_GEAR_RULES",
    "CREATE_STRESS_CAPACITY_AND_KINETICS_RULES",
    "PORTAL_PERMALOADER_AND_CHUNK_TICKING_RULES",
    "EnchantmentEntry",
    "AnvilItem",
    "AnvilMergeStep",
    "AnvilPlan",
    "optimize_anvil_tree",
    "calculate_penalty",
    "get_enchantment",
    "MachineEntry",
    "KineticReport",
    "analyze_create_network",
    "resolve_impact_factor",
    "AlignmentResult",
    "PermaloaderReport",
    "evaluate_portal_alignment",
    "analyze_permaloader",
]

__version__ = "2.0.0"
