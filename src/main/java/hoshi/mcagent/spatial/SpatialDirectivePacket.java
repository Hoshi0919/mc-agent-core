package hoshi.mcagent.spatial;

import hoshi.mcagent.format.MinecraftTextFormatter;
import hoshi.mcagent.format.TellrawJsonBuilder;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Encapsulated network packet and domain model for transmitting 3D in-world visual overlays to Fabric/Forge clients.
 */
public record SpatialDirectivePacket(
        String channel,
        String id,
        String category,
        List<SpatialPrimitive> primitives,
        String hudTitle,
        String hudDescription,
        boolean clearPrevious,
        long timestamp
) {

    public static final String DEFAULT_CHANNEL = "hoshi:spatial_overlay";

    public SpatialDirectivePacket {
        if (channel == null || channel.isEmpty()) {
            channel = DEFAULT_CHANNEL;
        }
        if (primitives == null) {
            primitives = Collections.emptyList();
        }
    }

    public static SpatialDirectivePacket of(String id, String category, List<SpatialPrimitive> primitives, String hudTitle, String hudDesc) {
        return new SpatialDirectivePacket(
                DEFAULT_CHANNEL,
                id,
                category,
                primitives != null ? List.copyOf(primitives) : Collections.emptyList(),
                hudTitle,
                hudDesc,
                true,
                System.currentTimeMillis()
        );
    }

    public static SpatialDirectivePacket clear(String category) {
        return new SpatialDirectivePacket(
                DEFAULT_CHANNEL,
                "clear-" + category,
                category,
                Collections.emptyList(),
                null,
                null,
                true,
                System.currentTimeMillis()
        );
    }

    public static SpatialDirectivePacket empty() {
        return new SpatialDirectivePacket(
                DEFAULT_CHANNEL,
                "empty",
                "NONE",
                Collections.emptyList(),
                null,
                null,
                false,
                System.currentTimeMillis()
        );
    }

    public boolean isEmpty() {
        if ("NONE".equals(category) && !clearPrevious) return true;
        return primitives.isEmpty() && (hudTitle == null || hudTitle.isEmpty()) && !clearPrevious;
    }

    public int size() {
        return primitives.size();
    }

    public String toJson() {
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"channel\":\"").append(escapeJson(channel)).append("\",");
        sb.append("\"id\":\"").append(escapeJson(id)).append("\",");
        sb.append("\"category\":\"").append(escapeJson(category)).append("\",");
        sb.append("\"clearPrevious\":").append(clearPrevious).append(",");
        sb.append("\"timestamp\":").append(timestamp);

        if (hudTitle != null) {
            sb.append(",\"hudTitle\":\"").append(escapeJson(hudTitle)).append("\"");
        }
        if (hudDescription != null) {
            sb.append(",\"hudDescription\":\"").append(escapeJson(hudDescription)).append("\"");
        }

        sb.append(",\"primitives\":[");
        for (int i = 0; i < primitives.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(primitives.get(i).toJson());
        }
        sb.append("]}");
        return sb.toString();
    }

    /**
     * Fallback to vanilla Minecraft tellraw command for players without the holographic client mod installed.
     */
    public String toTellrawFallback() {
        List<MinecraftTextFormatter.ChatComponent> list = new ArrayList<>();
        list.add(new MinecraftTextFormatter.ChatComponent("[HOSHI OVERLAY] ", "gold", true, false, null, null, null));

        if (hudTitle != null && !hudTitle.isEmpty()) {
            list.add(new MinecraftTextFormatter.ChatComponent(hudTitle + "\\n", "yellow", true, false, null, null, null));
        }
        if (hudDescription != null && !hudDescription.isEmpty()) {
            list.add(new MinecraftTextFormatter.ChatComponent(hudDescription + "\\n", "gray", false, false, null, null, null));
        }

        int count = 0;
        for (SpatialPrimitive p : primitives) {
            if (p.pos() != null) {
                list.add(new MinecraftTextFormatter.ChatComponent("  • " + p.type() + " at ", "white", false, false, null, null, null));
                String coordsText = String.format("[%d, %d, %d]", p.pos().x(), p.pos().y(), p.pos().z());
                String tpCmd = String.format("/tp %d %d %d", p.pos().x(), p.pos().y(), p.pos().z());
                list.add(new MinecraftTextFormatter.ChatComponent(coordsText, "green", true, false, "suggest_command", tpCmd, "点击填入传送指令"));
                if (p.label() != null && !p.label().isEmpty()) {
                    list.add(new MinecraftTextFormatter.ChatComponent(" (" + p.label() + ")", "aqua", false, false, null, null, null));
                }
                list.add(new MinecraftTextFormatter.ChatComponent("\\n", "white", false, false, null, null, null));
                count++;
                if (count >= 5) {
                    if (primitives.size() > 5) {
                        list.add(new MinecraftTextFormatter.ChatComponent("  ... 以及其余 " + (primitives.size() - 5) + " 处高亮点\\n", "dark_gray", false, false, null, null, null));
                    }
                    break;
                }
            }
        }
        return TellrawJsonBuilder.toJson(list);
    }

    private static String escapeJson(String s) {
        if (s == null) return "";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"') sb.append("\\\"");
            else if (c == '\\') sb.append("\\\\");
            else if (c == '\n') sb.append("\\n");
            else if (c == '\r') sb.append("\\r");
            else if (c == '\t') sb.append("\\t");
            else sb.append(c);
        }
        return sb.toString();
    }
}
