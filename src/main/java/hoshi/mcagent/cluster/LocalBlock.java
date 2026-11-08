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

    public boolean isPiston() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return (id.contains("piston") || id.equals("minecraft:piston") || id.equals("minecraft:sticky_piston"))
                && !id.contains("piston_head");
    }

    public boolean isStickyPiston() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("sticky_piston");
    }

    public boolean isExtended() {
        return "true".equalsIgnoreCase(getProperty("extended", "false"));
    }

    public boolean isSlimeBlock() {
        return blockId != null && blockId.toLowerCase().contains("slime_block");
    }

    public boolean honeyBlock() {
        return isHoneyBlock();
    }

    public boolean isHoneyBlock() {
        return blockId != null && blockId.toLowerCase().contains("honey_block");
    }

    public boolean isGlazedTerracotta() {
        return blockId != null && blockId.toLowerCase().contains("glazed_terracotta");
    }

    public boolean isImmovable() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        if (id.contains("bedrock") || id.contains("obsidian") || id.contains("crying_obsidian") ||
            id.contains("nether_portal") || id.contains("end_portal") || id.contains("reinforced_deepslate") ||
            id.contains("piston_head")) {
            return true;
        }
        if (id.contains("chest") || id.contains("barrel") || id.contains("shulker_box") ||
            id.contains("furnace") || id.contains("smoker") || id.contains("blast_furnace") ||
            id.contains("hopper") || id.contains("dispenser") || id.contains("dropper") ||
            id.contains("brewing_stand") || id.contains("crafter") || id.contains("beacon") ||
            id.contains("enchanting_table") || id.contains("spawner") || id.contains("sculk_sensor") ||
            id.contains("sculk_catalyst") || id.contains("sculk_shrieker")) {
            return true;
        }
        return false;
    }

    public boolean isRedstonePowerSource() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        if (id.contains("redstone_block")) return true;
        if (id.contains("redstone_torch") && !"false".equalsIgnoreCase(getProperty("lit", "true"))) return true;
        if (isRedstoneWire() && (!"0".equals(getProperty("power", "0")) || isPowered())) return true;
        if ((id.contains("lever") || id.contains("button") || id.contains("pressure_plate")) && isPowered()) return true;
        if (isRepeater() && isPowered()) return true;
        if (isComparator() && isPowered()) return true;
        if (id.contains("observer") && isPowered()) return true;
        return isPowered();
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

    public boolean isRedstoneTorch() {
        return blockId != null && (blockId.toLowerCase().contains("redstone_torch") || blockId.toLowerCase().contains("redstone_wall_torch"));
    }

    public boolean isObserver() {
        return blockId != null && blockId.toLowerCase().contains("observer");
    }

    public boolean isTransparent() {
        if (blockId == null || isAir()) return true;
        String id = blockId.toLowerCase();
        return id.contains("glass") || id.contains("slab") || id.contains("stairs") ||
               id.contains("glowstone") || id.contains("leaves") || id.contains("ice") ||
               id.contains("hopper") || id.contains("chest") || id.contains("fence") ||
               id.contains("wall") || id.contains("piston") || id.contains("door") ||
               id.contains("trapdoor") || id.contains("wire") || isRedstoneTorch() ||
               isRepeater() || isComparator();
    }

    public boolean isSolidConductiveBlock() {
        if (blockId == null || isAir() || isTransparent()) return false;
        String id = blockId.toLowerCase();
        return !id.contains("redstone") && !id.contains("torch") && !id.contains("lever") &&
               !id.contains("button") && !id.contains("pressure_plate");
    }

    public boolean isCopperBulb() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("copper_bulb");
    }

    public boolean isCopperBulbLit() {
        return isCopperBulb() && "true".equalsIgnoreCase(getProperty("lit", "false"));
    }

    public boolean isButton() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("button");
    }

    public boolean isLever() {
        if (blockId == null) return false;
        String id = blockId.toLowerCase();
        return id.contains("lever");
    }

    public boolean isAir() {
        return blockId == null || blockId.equals("minecraft:air") || blockId.equals("minecraft:cave_air") || blockId.equals("minecraft:void_air");
    }
}
