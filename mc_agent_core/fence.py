import re
from dataclasses import dataclass
from typing import Optional
from .context import ContextSnapshot
from .rules import (
    MOB_SPAWNING_RULE,
    NETHERITE_UPGRADE_RULE,
    VERSION_1_21_MECHANICS,
    ENCHANTMENT_CONFLICT_RULES,
    VILLAGER_RULES,
    BEACON_RULES,
    OMINOUS_AND_TRIAL_RULES,
    WARDEN_SCULK_RULES,
    COPPER_AND_WAXING_RULES,
    COMPARATOR_CONTAINER_RULES,
    ANVIL_PENALTY_RULES,
    BREWING_POTION_RULES,
    IRON_GOLEM_SPAWN_RULES,
    PORTAL_LINKING_RULES,
    END_DRAGON_AND_GATEWAY_RULES,
    CONDUIT_STRUCTURE_RULES,
    RAID_AND_VILLAGE_RULES,
    PIGLIN_BARTERING_RULES,
    ENCHANTING_TABLE_RULES,
    JAVA_BEDROCK_DIFFERENCES_RULES,
    SUGAR_CANE_FARM_RULES,
    STONE_GENERATOR_RULES,
    REDSTONE_CLOCK_RULES,
    PUMPKIN_MELON_FARM_RULES,
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
)

INJECTION_PATTERNS = re.compile(
    r"(?i)(ignore\s+(all\s+)?(previous|prior|above)\s+instructions|system\s+prompt|give\s+me\s+op|/op\s+|gamemode\s+creative|execute\s+as|discard\s+safety)"
)


@dataclass(frozen=True)
class FencedPrompt:
    system_prompt: str
    user_prompt: str
    flagged_as_suspicious: bool


class PromptSafetyFence:
    @staticmethod
    def build(raw_query: str, context: Optional[ContextSnapshot]) -> FencedPrompt:
        sanitized = PromptSafetyFence.sanitize(raw_query)
        suspicious = bool(INJECTION_PATTERNS.search(raw_query))

        system_prompt = (
            "You are Hoshi, an intelligent and grounded in-game assistant inside Minecraft (Version 1.21.x).\n\n"
            "Rules:\n"
            "1. Always prioritize factual accuracy for Minecraft 1.18~1.21. Never hallucinate outdated mechanics "
            "(e.g. 1.20+ requires Smithing Template for netherite, 1.18+ diamond optimal at Y=-58, monster spawning requires block light 0).\n"
            "2. Keep responses concise, clear, and direct. The player is reading this in a Minecraft chatbox or small HUD overlay. Maximum 3 to 4 compact sentences.\n"
            "3. Do NOT execute destructive server commands or claim you have OP privileges.\n"
            "4. When suggesting in-game coordinates or commands, place them cleanly so the player can copy or click them."
        )

        blocks = []
        if context is not None:
            blocks.append(context.to_prompt_block())

        blocks.append(
            "<canonical_rules>\n"
            f"{MOB_SPAWNING_RULE}\n\n"
            f"{NETHERITE_UPGRADE_RULE}\n\n"
            f"{VERSION_1_21_MECHANICS}\n\n"
            f"{ENCHANTMENT_CONFLICT_RULES}\n\n"
            f"{VILLAGER_RULES}\n\n"
            f"{BEACON_RULES}\n\n"
            f"{OMINOUS_AND_TRIAL_RULES}\n\n"
            f"{WARDEN_SCULK_RULES}\n\n"
            f"{COPPER_AND_WAXING_RULES}\n\n"
            f"{COMPARATOR_CONTAINER_RULES}\n\n"
            f"{ANVIL_PENALTY_RULES}\n\n"
            f"{BREWING_POTION_RULES}\n\n"
            f"{IRON_GOLEM_SPAWN_RULES}\n\n"
            f"{PORTAL_LINKING_RULES}\n\n"
            f"{END_DRAGON_AND_GATEWAY_RULES}\n\n"
            f"{CONDUIT_STRUCTURE_RULES}\n\n"
            f"{RAID_AND_VILLAGE_RULES}\n\n"
            f"{PIGLIN_BARTERING_RULES}\n\n"
            f"{ENCHANTING_TABLE_RULES}\n\n"
            f"{JAVA_BEDROCK_DIFFERENCES_RULES}\n\n"
            f"{SUGAR_CANE_FARM_RULES}\n\n"
            f"{STONE_GENERATOR_RULES}\n\n"
            f"{REDSTONE_CLOCK_RULES}\n\n"
            f"{PUMPKIN_MELON_FARM_RULES}\n\n"
            f"{VILLAGER_BREEDING_RULES}\n\n"
            f"{VILLAGER_CROP_FARM_RULES}\n\n"
            f"{SMELTING_FUEL_EFFICIENCY_RULES}\n\n"
            f"{ZOMBIE_VILLAGER_CURE_RULES}\n\n"
            f"{IRON_GOLEM_REPAIR_RULES}\n\n"
            f"{ARMADILLO_WOLF_ARMOR_RULES}\n\n"
            f"{TRIAL_SPAWNER_BREEZE_RULES}\n\n"
            f"{HOPPER_LOGISTICS_SORTING_RULES}\n\n"
            f"{COMPARATOR_SUBTRACTION_ALGEBRA_RULES}\n\n"
            f"{WATER_BUBBLE_COLUMN_ELEVATOR_RULES}\n\n"
            f"{OBSERVER_PULSE_CLOCKS_RULES}\n\n"
            f"{CONDUIT_MULTIBLOCK_ACTIVATION_RULES}\n\n"
            f"{NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD_RULES}\n\n"
            f"{SMELTING_ARRAY_THROUGHPUT_BOTTLENECK_RULES}\n\n"
            f"{HOPPER_MINECART_UNLOADER_DYNAMICS_RULES}\n\n"
            f"{HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES_RULES}\n\n"
            f"{SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION_RULES}\n\n"
            f"{IRON_FARM_PANIC_AND_LOS_SLEEP_RULES}\n\n"
            f"{VILLAGER_WORKSTATION_PATHING_AND_RESTOCK_RULES}\n"
            "</canonical_rules>"
        )

        blocks.append(f"<player_query>\n{sanitized}\n</player_query>")

        return FencedPrompt(
            system_prompt=system_prompt,
            user_prompt="\n\n".join(blocks),
            flagged_as_suspicious=suspicious,
        )

    @staticmethod
    def sanitize(raw_input: str) -> str:
        if not raw_input:
            return ""
        # Strip potential delimiter breaks and control characters
        cleaned = raw_input.replace("<canonical_rules>", "")
        cleaned = cleaned.replace("</canonical_rules>", "")
        cleaned = cleaned.replace("<player_query>", "")
        cleaned = cleaned.replace("</player_query>", "")
        cleaned = cleaned.replace("<context_snapshot>", "")
        cleaned = cleaned.replace("</context_snapshot>", "")
        cleaned = cleaned.replace("<player_context>", "")
        cleaned = cleaned.replace("</player_context>", "")
        return cleaned.strip()
