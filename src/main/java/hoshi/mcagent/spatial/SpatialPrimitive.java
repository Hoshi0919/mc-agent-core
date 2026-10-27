package hoshi.mcagent.spatial;

import hoshi.mcagent.cluster.BlockPos;

import java.util.Collections;
import java.util.Map;

/**
 * Geometric render primitive for in-world holographic guides, bounding boxes, arrows, and ghost blocks.
 */
public record SpatialPrimitive(
        PrimitiveType type,
        BlockPos minPos,
        BlockPos maxPos,
        BlockPos pos,
        String blockId,
        Map<String, String> properties,
        BlockPos fromPos,
        BlockPos toPos,
        double centerX,
        double centerY,
        double centerZ,
        double radius,
        String label,
        SpatialColor color,
        int durationTicks
) {

    public enum PrimitiveType {
        BOX_OUTLINE,
        GHOST_BLOCK,
        FLOW_ARROW,
        SPHERE_BOUNDARY,
        BILLBOARD
    }

    public SpatialPrimitive {
        if (properties == null) {
            properties = Collections.emptyMap();
        }
        if (color == null) {
            color = SpatialColor.WHITE;
        }
    }

    public static SpatialPrimitive boxOutline(BlockPos pos, SpatialColor color, String label, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.BOX_OUTLINE, pos, pos, pos, null, null, null, null,
                0, 0, 0, 0, label, color, durationTicks
        );
    }

    public static SpatialPrimitive boxOutline(BlockPos min, BlockPos max, SpatialColor color, String label, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.BOX_OUTLINE, min, max, min, null, null, null, null,
                0, 0, 0, 0, label, color, durationTicks
        );
    }

    public static SpatialPrimitive ghostBlock(BlockPos pos, String blockId, Map<String, String> properties, SpatialColor color, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.GHOST_BLOCK, pos, pos, pos, blockId, properties, null, null,
                0, 0, 0, 0, blockId, color, durationTicks
        );
    }

    public static SpatialPrimitive ghostBlock(BlockPos pos, String blockId, SpatialColor color, int durationTicks) {
        return ghostBlock(pos, blockId, Collections.emptyMap(), color, durationTicks);
    }

    public static SpatialPrimitive flowArrow(BlockPos from, BlockPos to, SpatialColor color, String label, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.FLOW_ARROW, from, to, from, null, null, from, to,
                0, 0, 0, 0, label, color, durationTicks
        );
    }

    public static SpatialPrimitive sphereBoundary(double cx, double cy, double cz, double r, SpatialColor color, String label, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.SPHERE_BOUNDARY, null, null, null, null, null, null, null,
                cx, cy, cz, r, label, color, durationTicks
        );
    }

    public static SpatialPrimitive billboard(BlockPos pos, String label, SpatialColor color, int durationTicks) {
        return new SpatialPrimitive(
                PrimitiveType.BILLBOARD, pos, pos, pos, null, null, null, null,
                0, 0, 0, 0, label, color, durationTicks
        );
    }

    public String toJson() {
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"type\":\"").append(type.name()).append("\",");
        sb.append("\"color\":").append(color.toJson()).append(",");
        sb.append("\"duration\":").append(durationTicks);

        if (label != null && !label.isEmpty()) {
            sb.append(",\"label\":\"").append(escapeJson(label)).append("\"");
        }
        if (pos != null) {
            sb.append(",\"pos\":{\"x\":").append(pos.x()).append(",\"y\":").append(pos.y()).append(",\"z\":").append(pos.z()).append("}");
        }
        if (minPos != null && maxPos != null) {
            sb.append(",\"min\":{\"x\":").append(minPos.x()).append(",\"y\":").append(minPos.y()).append(",\"z\":").append(minPos.z()).append("}");
            sb.append(",\"max\":{\"x\":").append(maxPos.x()).append(",\"y\":").append(maxPos.y()).append(",\"z\":").append(maxPos.z()).append("}");
        }
        if (blockId != null) {
            sb.append(",\"blockId\":\"").append(escapeJson(blockId)).append("\"");
        }
        if (!properties.isEmpty()) {
            sb.append(",\"properties\":{");
            boolean first = true;
            for (var entry : properties.entrySet()) {
                if (!first) sb.append(",");
                sb.append("\"").append(escapeJson(entry.getKey())).append("\":\"").append(escapeJson(entry.getValue())).append("\"");
                first = false;
            }
            sb.append("}");
        }
        if (fromPos != null && toPos != null) {
            sb.append(",\"from\":{\"x\":").append(fromPos.x()).append(",\"y\":").append(fromPos.y()).append(",\"z\":").append(fromPos.z()).append("}");
            sb.append(",\"to\":{\"x\":").append(toPos.x()).append(",\"y\":").append(toPos.y()).append(",\"z\":").append(toPos.z()).append("}");
        }
        if (type == PrimitiveType.SPHERE_BOUNDARY) {
            sb.append(",\"sphere\":{\"cx\":").append(centerX).append(",\"cy\":").append(centerY).append(",\"cz\":").append(centerZ).append(",\"radius\":").append(radius).append("}");
        }
        sb.append("}");
        return sb.toString();
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
