package hoshi.mcagent.context;

import java.util.*;

/**
 * Immutable snapshot of the player's full inventory, armor, and hotbar state.
 */
public record InventorySnapshot(
        ItemInstance mainHand,
        ItemInstance offHand,
        ItemInstance helmet,
        ItemInstance chestplate,
        ItemInstance leggings,
        ItemInstance boots,
        Map<Integer, ItemInstance> hotbar,
        Map<Integer, ItemInstance> mainInventory
) {
    public InventorySnapshot {
        if (hotbar == null) hotbar = Collections.emptyMap();
        if (mainInventory == null) mainInventory = Collections.emptyMap();
    }

    public static InventorySnapshot empty() {
        return new InventorySnapshot(null, null, null, null, null, null, Collections.emptyMap(), Collections.emptyMap());
    }

    /**
     * Counts total number of items with given ID across mainhand, offhand, armor, and all slots.
     */
    public int countItem(String itemId) {
        if (itemId == null || itemId.isEmpty()) return 0;
        String target = normalizeId(itemId);
        int total = 0;

        if (mainHand != null && matchesId(mainHand.itemId(), target)) total += mainHand.count();
        if (offHand != null && matchesId(offHand.itemId(), target)) total += offHand.count();
        if (helmet != null && matchesId(helmet.itemId(), target)) total += helmet.count();
        if (chestplate != null && matchesId(chestplate.itemId(), target)) total += chestplate.count();
        if (leggings != null && matchesId(leggings.itemId(), target)) total += leggings.count();
        if (boots != null && matchesId(boots.itemId(), target)) total += boots.count();

        for (ItemInstance item : hotbar.values()) {
            if (item != null && matchesId(item.itemId(), target)) {
                total += item.count();
            }
        }
        for (ItemInstance item : mainInventory.values()) {
            if (item != null && matchesId(item.itemId(), target)) {
                total += item.count();
            }
        }
        return total;
    }

    public boolean hasItem(String itemId, int minimumCount) {
        return countItem(itemId) >= minimumCount;
    }

    /**
     * Finds hotbar slot index (0~8) containing an item matching itemId.
     */
    public Optional<Integer> findHotbarSlot(String itemId) {
        String target = normalizeId(itemId);
        for (Map.Entry<Integer, ItemInstance> entry : hotbar.entrySet()) {
            if (entry.getValue() != null && matchesId(entry.getValue().itemId(), target)) {
                return Optional.of(entry.getKey());
            }
        }
        return Optional.empty();
    }

    /**
     * Finds hotbar slot index (0~8) for a tool of given type meeting or exceeding minimum harvest tier.
     */
    public Optional<Integer> findHotbarTool(String toolType, int minTier) {
        for (Map.Entry<Integer, ItemInstance> entry : hotbar.entrySet()) {
            ItemInstance item = entry.getValue();
            if (item != null && !item.isEmpty()) {
                if (matchesToolType(item, toolType) && item.getHarvestTier() >= minTier) {
                    return Optional.of(entry.getKey());
                }
            }
        }
        return Optional.empty();
    }

    /**
     * Checks if player is wearing any piece of gold armor (to prevent Piglin hostility).
     */
    public boolean isWearingGoldArmor() {
        for (ItemInstance armor : Arrays.asList(helmet, chestplate, leggings, boots)) {
            if (armor != null && armor.itemId() != null && armor.itemId().toLowerCase().contains("golden_")) {
                return true;
            }
        }
        return false;
    }

    /**
     * Calculates total equipped armor protection defense points (0 ~ 20).
     */
    public int totalArmorPoints() {
        int score = 0;
        for (ItemInstance armor : Arrays.asList(helmet, chestplate, leggings, boots)) {
            if (armor != null && armor.itemId() != null) {
                score += estimateArmorValue(armor.itemId());
            }
        }
        return Math.min(20, score);
    }

    private static int estimateArmorValue(String id) {
        String s = id.toLowerCase();
        if (s.contains("netherite") || s.contains("diamond")) {
            if (s.contains("chestplate")) return 8;
            if (s.contains("leggings")) return 6;
            if (s.contains("helmet")) return 3;
            if (s.contains("boots")) return 3;
        } else if (s.contains("iron")) {
            if (s.contains("chestplate")) return 6;
            if (s.contains("leggings")) return 5;
            if (s.contains("helmet")) return 2;
            if (s.contains("boots")) return 2;
        } else if (s.contains("chainmail") || s.contains("golden")) {
            if (s.contains("chestplate")) return 5;
            if (s.contains("leggings")) return 3;
            if (s.contains("helmet")) return 2;
            if (s.contains("boots")) return 1;
        } else if (s.contains("leather")) {
            if (s.contains("chestplate")) return 3;
            if (s.contains("leggings")) return 2;
            if (s.contains("helmet")) return 1;
            if (s.contains("boots")) return 1;
        }
        return 1;
    }

    private static boolean matchesToolType(ItemInstance item, String toolType) {
        if (toolType == null) return false;
        String t = toolType.toLowerCase();
        if (t.contains("pickaxe")) return item.isPickaxe();
        if (t.contains("axe")) return item.isAxe();
        if (t.contains("shovel")) return item.isShovel();
        if (t.contains("hoe")) return item.isHoe();
        if (t.contains("sword")) return item.isSword();
        return false;
    }

    private static String normalizeId(String id) {
        if (id == null) return "";
        return id.toLowerCase().replace("minecraft:", "").trim();
    }

    private static boolean matchesId(String fullId, String target) {
        if (fullId == null) return false;
        return normalizeId(fullId).equals(target);
    }

    public String toSummary() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("Armor: %d/20 defense (Gold: %b) | ", totalArmorPoints(), isWearingGoldArmor()));
        sb.append("Hotbar: [");
        List<String> items = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            ItemInstance it = hotbar.get(i);
            if (it != null && !it.isEmpty()) {
                items.add(String.format("%d:%s x%d", i, it.itemId().replace("minecraft:", ""), it.count()));
            }
        }
        sb.append(String.join(", ", items));
        sb.append("]");
        return sb.toString();
    }
}
