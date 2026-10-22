package hoshi.mcagent.context;

import java.util.Collections;
import java.util.List;

/**
 * Immutable snapshot of player, inventory, targeted blocks/entities, and world state captured on the main tick thread.
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
        boolean isThundering,
        InventorySnapshot inventory,
        TargetEntity targetEntity
) {
    public ContextSnapshot {
        if (activeEffects == null) {
            activeEffects = Collections.emptyList();
        }
    }

    /**
     * Backward-compatible 17-argument constructor for legacy callers and tests.
     */
    public ContextSnapshot(
            String playerName, String dimension, double x, double y, double z,
            float yaw, float pitch, String biome, TargetBlock targetBlock,
            String mainHandItem, String offHandItem, float health, int hunger,
            List<String> activeEffects, long worldTimeTicks, boolean isRaining, boolean isThundering
    ) {
        this(playerName, dimension, x, y, z, yaw, pitch, biome, targetBlock,
                mainHandItem, offHandItem, health, hunger, activeEffects, worldTimeTicks,
                isRaining, isThundering, null, null);
    }

    public static Builder builder() {
        return new Builder();
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
        if (inventory != null) {
            sb.append(String.format("Inventory State: %s\n", inventory.toSummary()));
        }
        if (!activeEffects.isEmpty()) {
            sb.append(String.format("Active Effects: %s\n", String.join(", ", activeEffects)));
        }
        sb.append(String.format("Environment: TimeTicks=%d (%s) | Rain=%b | Thunder=%b\n",
                timeOfDayTicks(), isNight() ? "Night" : "Day", isRaining, isThundering));
        if (targetBlock != null && !targetBlock.isAir()) {
            sb.append("Target Block: ").append(targetBlock.toSummary()).append("\n");
            if (inventory != null) {
                var harvest = targetBlock.evaluateHarvest(inventory);
                sb.append("  Harvest Drop Capable: ").append(harvest.canHarvestWithDrops()).append(" | Advice: ").append(harvest.advice()).append("\n");
            }
        }
        if (targetEntity != null) {
            sb.append("Target Entity: ").append(targetEntity.toSummary()).append("\n");
        }
        sb.append("</player_context>");
        return sb.toString();
    }

    public static class Builder {
        private String playerName = "Player";
        private String dimension = "minecraft:overworld";
        private double x = 0.0, y = 64.0, z = 0.0;
        private float yaw = 0.0f, pitch = 0.0f;
        private String biome = "minecraft:plains";
        private TargetBlock targetBlock = TargetBlock.air();
        private String mainHandItem = "minecraft:air";
        private String offHandItem = "minecraft:air";
        private float health = 20.0f;
        private int hunger = 20;
        private List<String> activeEffects = Collections.emptyList();
        private long worldTimeTicks = 1000L;
        private boolean isRaining = false;
        private boolean isThundering = false;
        private InventorySnapshot inventory = InventorySnapshot.empty();
        private TargetEntity targetEntity = null;

        public Builder player(String name) { this.playerName = name; return this; }
        public Builder dimension(String dim) { this.dimension = dim; return this; }
        public Builder position(double x, double y, double z) { this.x = x; this.y = y; this.z = z; return this; }
        public Builder rotation(float yaw, float pitch) { this.yaw = yaw; this.pitch = pitch; return this; }
        public Builder biome(String b) { this.biome = b; return this; }
        public Builder targetBlock(TargetBlock tb) { this.targetBlock = tb; return this; }
        public Builder targetEntity(TargetEntity te) { this.targetEntity = te; return this; }
        public Builder mainHand(String item) { this.mainHandItem = item; return this; }
        public Builder offHand(String item) { this.offHandItem = item; return this; }
        public Builder vitals(float hp, int food) { this.health = hp; this.hunger = food; return this; }
        public Builder effects(List<String> fx) { this.activeEffects = fx; return this; }
        public Builder worldTime(long ticks) { this.worldTimeTicks = ticks; return this; }
        public Builder weather(boolean rain, boolean thunder) { this.isRaining = rain; this.isThundering = thunder; return this; }
        public Builder inventory(InventorySnapshot inv) { this.inventory = inv; return this; }

        public ContextSnapshot build() {
            return new ContextSnapshot(playerName, dimension, x, y, z, yaw, pitch, biome,
                    targetBlock, mainHandItem, offHandItem, health, hunger, activeEffects,
                    worldTimeTicks, isRaining, isThundering, inventory, targetEntity);
        }
    }
}
