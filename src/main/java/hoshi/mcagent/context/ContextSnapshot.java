package hoshi.mcagent.context;

import java.util.Collections;
import java.util.List;

/**
 * Immutable snapshot of player and world state captured on the main tick thread.
 */
public record ContextSnapshot(
        String playerName,
        String dimension,
        double x,
        double y,
        double z,
        float yaw,
        float pitch,
        String biome,
        TargetBlock targetBlock,
        String mainHandItem,
        String offHandItem,
        float health,
        int hunger,
        List<String> activeEffects,
        long worldTimeTicks,
        boolean isRaining,
        boolean isThundering
) {
    public ContextSnapshot {
        if (activeEffects == null) {
            activeEffects = Collections.emptyList();
        }
    }

    public boolean isOverworld() {
        return "minecraft:overworld".equalsIgnoreCase(dimension) || "overworld".equalsIgnoreCase(dimension);
    }

    public boolean isNether() {
        return "minecraft:the_nether".equalsIgnoreCase(dimension) || "the_nether".equalsIgnoreCase(dimension) || "nether".equalsIgnoreCase(dimension);
    }

    public boolean isEnd() {
        return "minecraft:the_end".equalsIgnoreCase(dimension) || "the_end".equalsIgnoreCase(dimension) || "end".equalsIgnoreCase(dimension);
    }

    public int blockX() {
        return (int) Math.floor(x);
    }

    public int blockY() {
        return (int) Math.floor(y);
    }

    public int blockZ() {
        return (int) Math.floor(z);
    }

    public long timeOfDayTicks() {
        return worldTimeTicks % 24000L;
    }

    public boolean isNight() {
        long t = timeOfDayTicks();
        return t >= 13000L && t <= 23000L;
    }

    public int[] getNetherEquivalentCoords() {
        return new int[]{
                (int) Math.floor(x / 8.0),
                blockY(),
                (int) Math.floor(z / 8.0)
        };
    }

    public int[] getOverworldEquivalentCoords() {
        return new int[]{
                (int) Math.floor(x * 8.0),
                blockY(),
                (int) Math.floor(z * 8.0)
        };
    }

    public String toPromptBlock() {
        StringBuilder sb = new StringBuilder();
        sb.append("<player_context>\n");
        sb.append(String.format("Player: %s | Health: %.1f/20 | Hunger: %d/20\n", playerName, health, hunger));
        sb.append(String.format("Dimension: %s | Biome: %s\n", dimension, biome));
        sb.append(String.format("Position: X=%.1f, Y=%.1f, Z=%.1f (Block: [%d, %d, %d])\n", x, y, z, blockX(), blockY(), blockZ()));
        sb.append(String.format("Facing: Yaw=%.1f, Pitch=%.1f\n", yaw, pitch));
        sb.append(String.format("Main Hand: %s | Off Hand: %s\n", mainHandItem, offHandItem));
        if (!activeEffects.isEmpty()) {
            sb.append(String.format("Active Effects: %s\n", String.join(", ", activeEffects)));
        }
        sb.append(String.format("Environment: TimeTicks=%d (%s) | Rain=%b | Thunder=%b\n",
                timeOfDayTicks(), isNight() ? "Night" : "Day", isRaining, isThundering));
        if (targetBlock != null) {
            sb.append("Target Block: ").append(targetBlock.toSummary()).append("\n");
        }
        sb.append("</player_context>");
        return sb.toString();
    }
}
