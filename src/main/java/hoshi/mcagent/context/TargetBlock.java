package hoshi.mcagent.context;

import java.util.Collections;
import java.util.Map;
import java.util.Optional;

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
    public record HarvestReport(
            boolean canHarvestWithDrops,
            String toolRequirementName,
            int minTier,
            String currentToolStatus,
            Optional<Integer> hotbarAlternativeSlot,
            String advice
    ) {}

    public TargetBlock {
        if (properties == null) {
            properties = Collections.emptyMap();
        }
    }

    public static TargetBlock air() {
        return new TargetBlock("minecraft:air", 0, 0, 0, 0, 15, 0.0f, null, Collections.emptyMap());
    }

    public boolean isAir() {
        return blockId == null || blockId.equals("minecraft:air") || blockId.equals("minecraft:cave_air") || blockId.equals("minecraft:void_air");
    }

    public int totalLight() {
        return Math.max(blockLight, skyLight);
    }

    /**
     * Minimum harvest mining tier required for drops:
     * 0 = Hand / Any, 1 = Wood / Gold, 2 = Stone, 3 = Iron, 4 = Diamond / Netherite
     */
    public int getMinMiningTier() {
        if (blockId == null) return 0;
        String id = blockId.toLowerCase();
        if (id.contains("ancient_debris") || id.contains("obsidian") || id.contains("respawn_anchor")) {
            return 4; // Diamond or Netherite pickaxe
        }
        if (id.contains("diamond_ore") || id.contains("emerald_ore") || id.contains("gold_ore") || id.contains("redstone_ore")) {
            return 3; // Iron pickaxe
        }
        if (id.contains("iron_ore") || id.contains("copper_ore") || id.contains("lapis_ore")) {
            return 2; // Stone pickaxe
        }
        if (id.contains("stone") || id.contains("cobblestone") || id.contains("deepslate") || id.contains("sandstone") || id.contains("netherrack")) {
            return 1; // Wooden pickaxe
        }
        return 0;
    }

    /**
     * Determines the canonical tool type required for this block.
     */
    public String getRequiredToolType() {
        if (requiredTool != null && !requiredTool.isEmpty()) {
            return requiredTool.toLowerCase();
        }
        if (blockId == null) return "none";
        String id = blockId.toLowerCase();
        if (id.contains("ore") || id.contains("stone") || id.contains("deepslate") || id.contains("obsidian") || id.contains("debris") || id.contains("brick")) {
            return "pickaxe";
        }
        if (id.contains("log") || id.contains("wood") || id.contains("planks") || id.contains("chest") || id.contains("fence")) {
            return "axe";
        }
        if (id.contains("dirt") || id.contains("sand") || id.contains("gravel") || id.contains("clay") || id.contains("soul_")) {
            return "shovel";
        }
        if (id.contains("leaves") || id.contains("hay_block") || id.contains("sculk")) {
            return "hoe";
        }
        return "none";
    }

    /**
     * Evaluates whether the player's current held tool can harvest this block with item drops,
     * or suggests switching to an appropriate tool in their hotbar.
     */
    public HarvestReport evaluateHarvest(InventorySnapshot inventory) {
        if (isAir()) {
            return new HarvestReport(true, "无", 0, "准星对准空气", Optional.empty(), "无需工具");
        }

        int minTier = getMinMiningTier();
        String toolType = getRequiredToolType();
        ItemInstance held = inventory != null ? inventory.mainHand() : null;

        // Blocks that drop when broken by bare hand (tier 0 and toolType is none or leaves/wood where hand still drops)
        boolean dropsByHand = minTier == 0 && (toolType.equals("none") || toolType.equals("shovel") || toolType.equals("axe"));

        int heldTier = held != null ? held.getHarvestTier() : 0;
        boolean matchesType = held != null && matchesType(held, toolType);

        if (dropsByHand || (matchesType && heldTier >= minTier)) {
            return new HarvestReport(
                    true,
                    toolType.toUpperCase() + " (Tier " + minTier + "+)",
                    minTier,
                    held != null ? held.itemId() : "空手",
                    Optional.empty(),
                    "当前手持工具符合挖掘与掉落要求"
            );
        }

        // Current tool cannot harvest with drops! Look for a capable tool in hotbar
        Optional<Integer> hotbarAlt = inventory != null ? inventory.findHotbarTool(toolType, minTier) : Optional.empty();

        String advice;
        if (hotbarAlt.isPresent()) {
            advice = String.format("警告：当前手持无法正常掉落！请按 [%d] 切换至快捷栏第 %d 格的可用工具！",
                    hotbarAlt.get() + 1, hotbarAlt.get() + 1);
        } else {
            advice = String.format("严重警告：该方块需要 %s (等级 ≥ %d)，当前手持破坏将不会掉落任何物品！",
                    toolType.toUpperCase(), minTier);
        }

        return new HarvestReport(
                false,
                toolType.toUpperCase() + " (Tier " + minTier + "+)",
                minTier,
                held != null ? held.itemId() : "空手",
                hotbarAlt,
                advice
        );
    }

    private static boolean matchesType(ItemInstance tool, String requiredType) {
        if (tool == null) return false;
        String req = requiredType.toLowerCase();
        if (req.contains("pickaxe")) return tool.isPickaxe();
        if (req.contains("axe")) return tool.isAxe();
        if (req.contains("shovel")) return tool.isShovel();
        if (req.contains("hoe")) return tool.isHoe();
        return false;
    }

    public String toSummary() {
        if (isAir()) {
            return "None (Looking at air / open sky)";
        }
        return String.format("%s at [%d, %d, %d] (Light: block=%d, sky=%d, Hardness: %.1f, Tool: %s, MinTier: %d)",
                blockId, x, y, z, blockLight, skyLight, hardness, getRequiredToolType(), getMinMiningTier());
    }
}
