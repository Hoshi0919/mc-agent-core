package hoshi.mcagent.engine;

import hoshi.mcagent.context.ContextSnapshot;
import java.util.regex.Pattern;

/**
 * System prompt safety fencer and prompt injection firewall.
 * Injects canonical game mechanics into the LLM system prompt so the model
 * cannot be gaslit or jailbroken into reciting outdated/hallucinated rules.
 */
public final class PromptSafetyFence {

    private static final Pattern INJECTION_PATTERNS = Pattern.compile(
            "(?i)(ignore\\s+(all\\s+)?(previous|prior|above)\\s+instructions|system\\s+prompt|give\\s+me\\s+op|/op\\s+|gamemode\\s+creative|execute\\s+as|discard\\s+safety)"
    );

    public record FencedPrompt(String systemPrompt, String userPrompt, boolean flaggedAsSuspicious) {}

    public static FencedPrompt build(String rawUserQuery, ContextSnapshot context) {
        String sanitized = sanitize(rawUserQuery);
        boolean suspicious = INJECTION_PATTERNS.matcher(rawUserQuery).find();

        String systemPrompt = """
                You are Hoshi, an expert in-game Minecraft companion and mechanics advisor.
                Strictly adhere to the canonical Minecraft rules provided below.
                
                Rules of engagement:
                1. Always prioritize factual accuracy for Minecraft 1.18~1.21. Never hallucinate outdated mechanics (e.g. 1.20+ requires Smithing Template for netherite, 1.18+ diamond optimal at Y=-58, monster spawning requires block light 0).
                2. Keep responses concise, clear, and direct. The player is reading this in a Minecraft chatbox or small HUD overlay. Maximum 3 to 4 compact sentences.
                3. Do NOT execute destructive server commands or claim you have OP privileges.
                4. When suggesting in-game coordinates or commands, place them cleanly so the player can copy or click them.
                """;

        StringBuilder userPrompt = new StringBuilder();
        if (context != null) {
            userPrompt.append(context.toPromptBlock()).append("\n\n");
        }

        userPrompt.append("<canonical_rules>\n");
        userPrompt.append(LocalGameRules.MOB_SPAWNING_RULE).append("\n\n");
        userPrompt.append(LocalGameRules.NETHERITE_UPGRADE_RULE).append("\n\n");
        userPrompt.append(LocalGameRules.VERSION_1_21_MECHANICS).append("\n\n");
        userPrompt.append(LocalGameRules.ENCHANTMENT_CONFLICT_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.VILLAGER_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.BEACON_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.OMINOUS_AND_TRIAL_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.WARDEN_SCULK_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.COPPER_AND_WAXING_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.COMPARATOR_CONTAINER_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ANVIL_PENALTY_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.BREWING_POTION_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.IRON_GOLEM_SPAWN_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.PORTAL_LINKING_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.END_DRAGON_AND_GATEWAY_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.CONDUIT_STRUCTURE_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.RAID_AND_VILLAGE_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.PIGLIN_BARTERING_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ENCHANTING_TABLE_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.JAVA_BEDROCK_DIFFERENCES_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.SUGAR_CANE_FARM_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.STONE_GENERATOR_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.REDSTONE_CLOCK_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.PUMPKIN_MELON_FARM_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.VILLAGER_BREEDING_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.VILLAGER_CROP_FARM_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.SMELTING_FUEL_EFFICIENCY_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ZOMBIE_VILLAGER_CURE_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.IRON_GOLEM_REPAIR_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ARMADILLO_WOLF_ARMOR_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.TRIAL_SPAWNER_BREEZE_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.HOPPER_LOGISTICS_SORTING_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.COMPARATOR_SUBTRACTION_ALGEBRA_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.WATER_BUBBLE_COLUMN_ELEVATOR_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.OBSERVER_PULSE_CLOCKS_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.CONDUIT_MULTIBLOCK_ACTIVATION_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.SMELTING_ARRAY_THROUGHPUT_BOTTLENECK_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.HOPPER_MINECART_UNLOADER_DYNAMICS_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.IRON_FARM_PANIC_AND_LOS_SLEEP_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.VILLAGER_WORKSTATION_PATHING_AND_RESTOCK_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ANVIL_PENALTY_AND_BINARY_TREE_OPTIMIZER_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.ENCHANTMENT_COMPATIBILITY_AND_GEAR_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.CREATE_STRESS_CAPACITY_AND_KINETICS_RULES).append("\n\n");
        userPrompt.append(LocalGameRules.PORTAL_PERMALOADER_AND_CHUNK_TICKING_RULES).append("\n");
        userPrompt.append("</canonical_rules>\n\n");

        userPrompt.append("<player_query>\n");
        userPrompt.append(sanitized).append("\n");
        userPrompt.append("</player_query>");

        return new FencedPrompt(systemPrompt, userPrompt.toString(), suspicious);
    }

    public static String sanitize(String input) {
        if (input == null) return "";
        // Strip XML-like delimiter spoofing
        String clean = input.replace("<player_context>", "")
                .replace("</player_context>", "")
                .replace("<player_query>", "")
                .replace("</player_query>", "")
                .replace("<canonical_rules>", "")
                .replace("</canonical_rules>", "");
        return clean.trim();
    }

    private PromptSafetyFence() {}
}
