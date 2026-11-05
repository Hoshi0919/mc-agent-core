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

    public boolean isAe2() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("ae2:") || id.contains("appliedenergistics2:") ||
               id.contains("controller") || id.contains("cable") || id.contains("me_p2p") ||
               id.contains("storage_bus") || id.contains("import_bus") || id.contains("export_bus") ||
               id.contains("terminal") || id.contains("drive") || id.contains("interface") ||
               id.contains("pattern_provider");
    }

    public boolean isAe2Controller() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.equals("ae2:controller") || id.equals("appliedenergistics2:controller") || id.endsWith(":controller");
    }

    public boolean isAe2DenseCable() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("dense") && (id.contains("cable") || id.contains("glass") || id.contains("smart"));
    }

    public boolean isAe2Cable() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return (id.contains("cable") || id.contains("glass_cable") || id.contains("smart_cable") || id.contains("covered_cable"))
                && !isAe2DenseCable();
    }

    public boolean isAe2P2PTunnel() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("p2p") || id.contains("me_p2p_tunnel");
    }

    public boolean isAe2Device() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        if (isAe2Controller() || isAe2Cable() || isAe2DenseCable()) return false;
        return id.contains("bus") || id.contains("drive") || id.contains("terminal") ||
               id.contains("interface") || id.contains("pattern_provider") || id.contains("assembler") ||
               id.contains("level_emitter") || id.contains("cell_workbench") || id.contains("io_port") ||
               id.contains("security_station") || isAe2P2PTunnel();
    }

    public boolean isAir() {
        return blockId == null || blockId.equals("minecraft:air") || blockId.equals("minecraft:cave_air") || blockId.equals("minecraft:void_air");
    }
}
