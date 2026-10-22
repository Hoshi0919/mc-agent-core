package hoshi.mcagent.context;

import java.util.Collections;
import java.util.List;

/**
 * Represents an individual item stack in the player's inventory or container.
 */
public record ItemInstance(
        String itemId,
        int count,
        int durability,
        int maxDurability,
        String customName,
        List<String> enchantments
) {
    public ItemInstance {
        if (enchantments == null) {
            enchantments = Collections.emptyList();
        }
    }

    public static ItemInstance of(String itemId, int count) {
        return new ItemInstance(itemId, count, 0, 0, null, Collections.emptyList());
    }

    public static ItemInstance tool(String itemId, int durability, int maxDurability) {
        return new ItemInstance(itemId, 1, durability, maxDurability, null, Collections.emptyList());
    }

    public boolean isEmpty() {
        return itemId == null || itemId.isEmpty() || itemId.equals("minecraft:air") || count <= 0;
    }

    public boolean isPickaxe() {
        return itemId != null && itemId.contains("pickaxe");
    }

    public boolean isAxe() {
        return itemId != null && itemId.contains("axe") && !itemId.contains("pickaxe");
    }

    public boolean isShovel() {
        return itemId != null && itemId.contains("shovel");
    }

    public boolean isHoe() {
        return itemId != null && itemId.contains("hoe");
    }

    public boolean isSword() {
        return itemId != null && itemId.contains("sword");
    }

    /**
     * Harvest mining tier: 0=None/Hand, 1=Wood/Gold, 2=Stone, 3=Iron, 4=Diamond, 5=Netherite
     */
    public int getHarvestTier() {
        if (itemId == null) return 0;
        String id = itemId.toLowerCase();
        if (id.contains("netherite")) return 5;
        if (id.contains("diamond")) return 4;
        if (id.contains("iron")) return 3;
        if (id.contains("stone")) return 2;
        if (id.contains("golden") || id.contains("wooden")) return 1;
        return 0;
    }
}
