package hoshi.mcagent.engine;

import hoshi.mcagent.context.ContextSnapshot;

import java.util.regex.Pattern;

/**
 * Defends against prompt injection and delimiters leaks in multiplayer chat.
 */
public final class PromptSafetyFence {

    private static final Pattern INJECTION_PATTERNS = Pattern.compile(
            "(?i)(ignore\\s+(all\\s+)?(previous|prior|above)\\s+instructions|system\\s+prompt|give\\s+me\\s+op|/op\\s+|gamemode\\s+creative|execute\\s+as|discard\\s+safety)"
    );

    public record FencedPrompt(
            String systemPrompt,
            String userPrompt,
            boolean flaggedAsSuspicious
    ) {}

    public static FencedPrompt build(String rawQuery, ContextSnapshot context) {
        String sanitized = sanitize(rawQuery);
        boolean suspicious = INJECTION_PATTERNS.matcher(rawQuery).find();

        String systemPrompt = """
                You are Hoshi, an intelligent and grounded in-game assistant inside Minecraft (Version 1.21.x).
                
                Rules:
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
        userPrompt.append(LocalGameRules.VERSION_1_21_MECHANICS).append("\n");
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
