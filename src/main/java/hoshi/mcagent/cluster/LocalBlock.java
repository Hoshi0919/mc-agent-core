package hoshi.mcagent.cluster;

import java.util.Collections;
import java.util.Map;

/**
 * Node representation of an individual block within a local machine cluster subgraph.
 */
public record LocalBlock(
        BlockPos pos,
        String blockId,
        Map<String, String> properties
) {
    public LocalBlock {
        if (properties == null) {
            properties = Collections.emptyMap();
        }
    }

    public static LocalBlock of(int x, int y, int z, String blockId, Map<String, String> properties) {
        return new LocalBlock(new BlockPos(x, y, z), blockId, properties);
    }

    public static LocalBlock of(int x, int y, int z, String blockId) {
        return new LocalBlock(new BlockPos(x, y, z), blockId, Collections.emptyMap());
    }

    public String getProperty(String key, String defaultVal) {
        return properties.getOrDefault(key, defaultVal);
    }

    public String facing() {
        return getProperty("facing", "down").toLowerCase();
    }

    public String axis() {
        return getProperty("axis", "y").toLowerCase();
    }

    public boolean isPowered() {
        return "true".equalsIgnoreCase(getProperty("powered", "false"));
    }

    public boolean isEnabled() {
        return !"false".equalsIgnoreCase(getProperty("enabled", "true"));
    }

    public boolean isHopper() {
        return blockId != null && blockId.toLowerCase().contains("hopper");
    }

    public boolean isContainer() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("chest") || id.contains("shulker_box") || id.contains("barrel") ||
               id.contains("dropper") || id.contains("dispenser") || id.contains("crafter") ||
               id.contains("furnace") || id.contains("hopper");
    }

    public boolean isCreateKinetics() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("cogwheel") || id.contains("shaft") || id.contains("gearbox") ||
               id.contains("clutch") || id.contains("gearshift") || id.contains("water_wheel") ||
               id.contains("windmill_bearing") || id.contains("steam_engine");
    }

    public boolean isCogwheel() {
        return blockId != null && blockId.toLowerCase().contains("cogwheel") && !blockId.toLowerCase().contains("large");
    }

    public boolean isLargeCogwheel() {
        return blockId != null && blockId.toLowerCase().contains("large_cogwheel");
    }

    public boolean isShaft() {
        return blockId != null && blockId.toLowerCase().endsWith("shaft") && !blockId.toLowerCase().contains("gear");
    }

    public boolean isGearbox() {
        return blockId != null && blockId.toLowerCase().contains("gearbox");
    }

    public boolean isComparator() {
        return blockId != null && blockId.toLowerCase().contains("comparator");
    }

    public boolean isRepeater() {
        return blockId != null && blockId.toLowerCase().contains("repeater");
    }

    public boolean isRedstoneWire() {
        return blockId != null && (blockId.toLowerCase().contains("redstone_wire") || blockId.toLowerCase().equals("minecraft:redstone"));
    }

    public boolean isCrafter() {
        return blockId != null && blockId.toLowerCase().contains("crafter");
    }

    public boolean isAir() {
        return blockId == null || blockId.equals("minecraft:air") || blockId.equals("minecraft:cave_air") || blockId.equals("minecraft:void_air");
    }
}
