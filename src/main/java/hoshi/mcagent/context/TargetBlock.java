package hoshi.mcagent.context;

import java.util.Collections;
import java.util.Map;

/**
 * Represents the block targeted by the player's crosshair (Raycast HitResult).
 */
public record TargetBlock(
        String blockId,
        int x,
        int y,
        int z,
        int blockLight,
        int skyLight,
        float hardness,
        String requiredTool,
        Map<String, String> properties
) {
    public TargetBlock {
        if (properties == null) {
            properties = Collections.emptyMap();
        }
    }

    public boolean isAir() {
        return blockId == null || blockId.equals("minecraft:air") || blockId.equals("minecraft:cave_air") || blockId.equals("minecraft:void_air");
    }

    public int totalLight() {
        return Math.max(blockLight, skyLight);
    }

    public String toSummary() {
        if (isAir()) {
            return "None (Looking at air / open sky)";
        }
        return String.format("%s at [%d, %d, %d] (Light: block=%d, sky=%d, Hardness: %.1f, Tool: %s)",
                blockId, x, y, z, blockLight, skyLight, hardness, requiredTool != null ? requiredTool : "None");
    }
}
