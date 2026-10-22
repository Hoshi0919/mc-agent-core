package hoshi.mcagent.format;

import java.util.List;

/**
 * Serializes Minecraft text components into standard Vanilla /tellraw JSON format.
 * Zero external dependencies, compatible with Minecraft 1.16 through 1.21.x.
 */
public final class TellrawJsonBuilder {

    /**
     * Converts a list of ChatComponents into a Minecraft /tellraw JSON string.
     * e.g. {"text":"","extra":[{"text":"[Hoshi] ","color":"aqua","bold":true}, ...]}
     */
    public static String toJson(List<MinecraftTextFormatter.ChatComponent> components) {
        if (components == null || components.isEmpty()) {
            return "{\"text\":\"\"}";
        }

        StringBuilder sb = new StringBuilder();
        sb.append("{\"text\":\"\",\"extra\":[");

        boolean first = true;
        for (MinecraftTextFormatter.ChatComponent c : components) {
            if (!first) {
                sb.append(",");
            }
            first = false;

            sb.append("{");
            sb.append("\"text\":\"").append(escapeJson(c.text())).append("\"");

            if (c.color() != null && !c.color().isEmpty()) {
                sb.append(",\"color\":\"").append(escapeJson(c.color().toLowerCase())).append("\"");
            }
            if (c.bold()) {
                sb.append(",\"bold\":true");
            }
            if (c.italic()) {
                sb.append(",\"italic\":true");
            }

            // Click Event
            if (c.clickAction() != null && c.clickValue() != null) {
                String action = c.clickAction().toLowerCase();
                sb.append(",\"clickEvent\":{");
                sb.append("\"action\":\"").append(escapeJson(action)).append("\",");
                sb.append("\"value\":\"").append(escapeJson(c.clickValue())).append("\"");
                sb.append("}");
            }

            // Hover Event (show_text)
            if (c.hoverText() != null && !c.hoverText().isEmpty()) {
                sb.append(",\"hoverEvent\":{");
                sb.append("\"action\":\"show_text\",");
                sb.append("\"contents\":\"").append(escapeJson(c.hoverText())).append("\"");
                sb.append("}");
            }

            sb.append("}");
        }

        sb.append("]}");
        return sb.toString();
    }

    /**
     * Constructs a full runnable /tellraw command for Minecraft console, RCON, or server dispatcher.
     * e.g. /tellraw @p {"text":"","extra":[...]}
     */
    public static String toTellrawCommand(String targetSelector, List<MinecraftTextFormatter.ChatComponent> components) {
        String target = (targetSelector == null || targetSelector.trim().isEmpty()) ? "@s" : targetSelector.trim();
        return "/tellraw " + target + " " + toJson(components);
    }

    /**
     * Convenience method to convert raw text into a tellraw command.
     */
    public static String toTellrawFromText(String targetSelector, String rawText) {
        var components = MinecraftTextFormatter.parseComponents(rawText, null);
        return toTellrawCommand(targetSelector, components);
    }

    /**
     * Escapes special characters for strict JSON compliance.
     */
    public static String escapeJson(String input) {
        if (input == null) return "";
        StringBuilder sb = new StringBuilder(input.length() + 16);
        for (int i = 0; i < input.length(); i++) {
            char ch = input.charAt(i);
            switch (ch) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\b' -> sb.append("\\b");
                case '\f' -> sb.append("\\f");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (ch < ' ') {
                        String hex = Integer.toHexString(ch);
                        sb.append("\\u");
                        sb.append("0".repeat(4 - hex.length())).append(hex);
                    } else {
                        sb.append(ch);
                    }
                }
            }
        }
        return sb.toString();
    }

    private TellrawJsonBuilder() {}
}
