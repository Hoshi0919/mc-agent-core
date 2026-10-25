package hoshi.mcagent.anvil;

import java.util.*;

public class EnchantmentEntry {
    private final String id;
    private final String nameZh;
    private final int maxLevel;
    private final int itemMultiplier;
    private final int bookMultiplier;
    private final String targetType;
    private final Set<String> conflicts;

    public EnchantmentEntry(String id, String nameZh, int maxLevel, int itemMultiplier, int bookMultiplier, String targetType, Set<String> conflicts) {
        this.id = id;
        this.nameZh = nameZh;
        this.maxLevel = maxLevel;
        this.itemMultiplier = itemMultiplier;
        this.bookMultiplier = bookMultiplier;
        this.targetType = targetType;
        this.conflicts = conflicts != null ? conflicts : Collections.emptySet();
    }

    public String getId() { return id; }
    public String getNameZh() { return nameZh; }
    public int getMaxLevel() { return maxLevel; }
    public int getItemMultiplier() { return itemMultiplier; }
    public int getBookMultiplier() { return bookMultiplier; }
    public String getTargetType() { return targetType; }
    public Set<String> getConflicts() { return conflicts; }

    public boolean conflictsWith(String otherId) {
        if (otherId == null) return false;
        return conflicts.contains(otherId.toLowerCase());
    }

    public boolean isCompatibleWithGear(String gearType) {
        if (gearType == null || targetType.equals("all")) return true;
        String g = gearType.toLowerCase();
        if (targetType.equals("armor")) {
            return g.contains("helmet") || g.contains("chestplate") || g.contains("leggings") || g.contains("boots") || g.contains("armor") || g.contains("头盔") || g.contains("胸甲") || g.contains("护腿") || g.contains("靴子");
        }
        if (targetType.equals("helmet")) return g.contains("helmet") || g.contains("头盔");
        if (targetType.equals("chestplate")) return g.contains("chestplate") || g.contains("胸甲") || g.contains("elytra") || g.contains("鞘翅");
        if (targetType.equals("leggings")) return g.contains("leggings") || g.contains("护腿");
        if (targetType.equals("boots")) return g.contains("boots") || g.contains("靴子");
        if (targetType.equals("sword")) return g.contains("sword") || g.contains("剑");
        if (targetType.equals("tool")) return g.contains("pickaxe") || g.contains("axe") || g.contains("shovel") || g.contains("hoe") || g.contains("镐") || g.contains("斧") || g.contains("锹") || g.contains("锄");
        if (targetType.equals("bow")) return g.contains("bow") || g.contains("弓");
        if (targetType.equals("crossbow")) return g.contains("crossbow") || g.contains("弩");
        if (targetType.equals("trident")) return g.contains("trident") || g.contains("三叉戟");
        if (targetType.equals("mace")) return g.contains("mace") || g.contains("重锤");
        return true;
    }

    private static final Map<String, EnchantmentEntry> REGISTRY = new LinkedHashMap<>();

    private static void register(String id, String nameZh, int maxLevel, int itemMult, int bookMult, String target, String... confs) {
        Set<String> confSet = new HashSet<>(Arrays.asList(confs));
        EnchantmentEntry entry = new EnchantmentEntry(id, nameZh, maxLevel, itemMult, bookMult, target, confSet);
        REGISTRY.put(id.toLowerCase(), entry);
        REGISTRY.put(nameZh.toLowerCase(), entry);
    }

    static {
        // Swords & Axes
        register("sharpness", "锋利", 5, 1, 1, "sword", "smite", "bane_of_arthropods");
        register("smite", "亡灵杀手", 5, 2, 1, "sword", "sharpness", "bane_of_arthropods");
        register("bane_of_arthropods", "节肢杀手", 5, 2, 1, "sword", "sharpness", "smite");
        register("looting", "抢夺", 3, 4, 2, "sword");
        register("sweeping_edge", "横扫之刃", 3, 4, 2, "sword");
        register("fire_aspect", "火焰附加", 2, 4, 2, "sword");
        register("knockback", "击退", 2, 2, 1, "sword");

        // Tools
        register("efficiency", "效率", 5, 1, 1, "tool");
        register("fortune", "时运", 3, 4, 2, "tool", "silk_touch");
        register("silk_touch", "精准采集", 1, 8, 4, "tool", "fortune");

        // Universal
        register("unbreaking", "耐久", 3, 2, 1, "all");
        register("mending", "经验修补", 1, 4, 2, "all", "infinity");

        // Armor
        register("protection", "保护", 4, 1, 1, "armor", "fire_protection", "blast_protection", "projectile_protection");
        register("fire_protection", "火焰保护", 4, 2, 1, "armor", "protection", "blast_protection", "projectile_protection");
        register("blast_protection", "爆炸保护", 4, 4, 2, "armor", "protection", "fire_protection", "projectile_protection");
        register("projectile_protection", "弹射物保护", 4, 2, 1, "armor", "protection", "fire_protection", "blast_protection");
        register("thorns", "荆棘", 3, 8, 4, "armor");

        // Boots
        register("feather_falling", "摔落保护", 4, 2, 1, "boots");
        register("depth_strider", "深海行者", 3, 4, 2, "boots", "frost_walker");
        register("frost_walker", "冰霜行者", 2, 4, 2, "boots", "depth_strider");
        register("soul_speed", "灵魂疾行", 3, 8, 4, "boots");

        // Helmet & Leggings
        register("respiration", "水下呼吸", 3, 4, 2, "helmet");
        register("aqua_affinity", "水下速掘", 1, 4, 2, "helmet");
        register("swift_sneak", "迅捷潜行", 3, 8, 4, "leggings");

        // Bow & Crossbow
        register("power", "力量", 5, 1, 1, "bow");
        register("punch", "冲击", 2, 4, 2, "bow");
        register("flame", "火矢", 1, 4, 2, "bow");
        register("infinity", "无限", 1, 8, 4, "bow", "mending");
        register("quick_charge", "快速装填", 3, 2, 1, "crossbow");
        register("multishot", "多重射击", 1, 4, 2, "crossbow", "piercing");
        register("piercing", "穿透", 4, 1, 1, "crossbow", "multishot");

        // Trident & Mace
        register("loyalty", "忠诚", 3, 1, 1, "trident", "riptide");
        register("channeling", "引雷", 1, 8, 4, "trident", "riptide");
        register("riptide", "激流", 3, 4, 2, "trident", "loyalty", "channeling");
        register("impaling", "穿刺", 5, 4, 2, "trident");
        register("wind_burst", "风爆", 3, 4, 2, "mace");
        register("density", "致密", 5, 2, 1, "mace");
        register("breach", "破甲", 4, 4, 2, "mace");
    }

    public static EnchantmentEntry get(String key) {
        if (key == null) return null;
        String normalized = key.trim().toLowerCase().replace(" ", "_");
        return REGISTRY.get(normalized);
    }

    public static Collection<EnchantmentEntry> getAll() {
        return Collections.unmodifiableCollection(REGISTRY.values());
    }
}
