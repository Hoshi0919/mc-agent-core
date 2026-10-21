package hoshi.mcagent.format;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Formats LLM and rule responses into Minecraft chat-ready text components.
 * Supports Markdown to Section-Sign (§) formatting, coordinate highlights, and click actions.
 */
public final class MinecraftTextFormatter {

    public record ChatComponent(
            String text,
            String color,
            boolean bold,
            boolean italic,
            String clickAction,
            String clickValue,
            String hoverText
    ) {}

    public static final String PREFIX = "§b[Hoshi]§r ";

    private static final Pattern BOLD_PATTERN = Pattern.compile("\\*\\*(.*?)\\*\\*");
    private static final Pattern CODE_PATTERN = Pattern.compile("`(.*?)`");
    private static final Pattern COORD_PATTERN = Pattern.compile("\\[(-?\\d+),\\s*(-?\\d+),\\s*(-?\\d+)\\]");

    /**
     * Converts raw text or markdown into Minecraft Section-Sign (§) formatted string.
     */
    public static String toSectionString(String text) {
        if (text == null) return "";

        String result = text;
        // Replace bold **text** -> §ltext§r
        result = BOLD_PATTERN.matcher(result).replaceAll("§l$1§r");
        // Replace code `cmd` -> §e§ncmd§r
        result = CODE_PATTERN.matcher(result).replaceAll("§e$1§r");

        return result;
    }

    /**
     * Parses a text into a list of structured ChatComponents suitable for Fabric Text / Adventure Component.
     */
    public static List<ChatComponent> parseComponents(String rawText, String defaultSuggestedCommand) {
        List<ChatComponent> components = new ArrayList<>();
        if (rawText == null || rawText.isEmpty()) {
            return components;
        }

        // Add prefix
        components.add(new ChatComponent("[Hoshi] ", "aqua", true, false, null, null, "AI In-Game Assistant"));

        // Match coordinates to make them clickable
        Matcher matcher = COORD_PATTERN.matcher(rawText);
        int lastEnd = 0;

        while (matcher.find()) {
            if (matcher.start() > lastEnd) {
                String segment = rawText.substring(lastEnd, matcher.start());
                components.add(new ChatComponent(segment, "white", false, false, null, null, null));
            }

            String coordStr = matcher.group(0);
            int x = Integer.parseInt(matcher.group(1));
            int y = Integer.parseInt(matcher.group(2));
            int z = Integer.parseInt(matcher.group(3));
            String tpCmd = String.format("/tp %d %d %d", x, y, z);

            components.add(new ChatComponent(
                    coordStr,
                    "gold",
                    true,
                    false,
                    "SUGGEST_COMMAND",
                    tpCmd,
                    "点击将传送指令填入聊天框: " + tpCmd
            ));

            lastEnd = matcher.end();
        }

        if (lastEnd < rawText.length()) {
            String remainder = rawText.substring(lastEnd);
            components.add(new ChatComponent(remainder, "white", false, false, null, null, null));
        }

        // If there is an associated suggested command, append an interactive button
        if (defaultSuggestedCommand != null && !defaultSuggestedCommand.isEmpty()) {
            components.add(new ChatComponent("\n", "white", false, false, null, null, null));
            components.add(new ChatComponent(
                    " [▸ 点击执行/填入: " + defaultSuggestedCommand + "]",
                    "green",
                    true,
                    false,
                    "SUGGEST_COMMAND",
                    defaultSuggestedCommand,
                    "点击填入指令: " + defaultSuggestedCommand
            ));
        }

        return components;
    }

    private MinecraftTextFormatter() {}
}
