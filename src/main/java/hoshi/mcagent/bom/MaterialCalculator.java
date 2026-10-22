package hoshi.mcagent.bom;

import java.util.*;

/**
 * Deterministic Bill of Materials (BOM) calculator for Minecraft farms, redstone contraptions, and structures.
 */
public class MaterialCalculator {

    public static final String ID_SUGAR_CANE_FARM = "SUGAR_CANE_FARM";
    public static final String ID_PUMPKIN_MELON_FARM = "PUMPKIN_MELON_FARM";
    public static final String ID_BEACON_STRUCTURE = "BEACON_STRUCTURE";
    public static final String ID_STONE_GENERATOR = "STONE_GENERATOR";
    public static final String ID_ITEM_SORTER = "ITEM_SORTER_MODULE";
    public static final String ID_ETHO_CLOCK = "ETHO_HOPPER_CLOCK";

    public static BlueprintBOM getSugarCaneFarmBOM(int modules) {
        int n = Math.max(1, modules);
        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:piston", "普通活塞", n));
        comps.add(new ItemStack("minecraft:observer", "侦测器 (Observer)", n));
        comps.add(new ItemStack("minecraft:redstone", "红石粉", n));
        comps.add(new ItemStack("minecraft:sugar_cane", "甘蔗", n));
        comps.add(new ItemStack("minecraft:dirt", "泥土/沙子", n));
        comps.add(new ItemStack("minecraft:stone_bricks", "实心建筑方块", n * 2));
        comps.add(new ItemStack("minecraft:water_bucket", "水桶", Math.max(1, (n + 7) / 8)));
        comps.add(new ItemStack("minecraft:hopper", "漏斗", 1));
        comps.add(new ItemStack("minecraft:chest", "箱子", 2));

        List<ItemStack> raw = new ArrayList<>();
        raw.add(new ItemStack("minecraft:iron_ingot", "铁锭 (活塞+漏斗)", n + 5));
        raw.add(new ItemStack("minecraft:redstone", "红石粉总消耗", n * 3));
        raw.add(new ItemStack("minecraft:nether_quartz", "下界石英 (侦测器)", n));
        raw.add(new ItemStack("minecraft:cobblestone", "圆石 (活塞+侦测器)", n * 10));
        raw.add(new ItemStack("minecraft:oak_planks", "木板 (活塞+箱子+漏斗)", n * 3 + 16));

        return new BlueprintBOM(ID_SUGAR_CANE_FARM, "全自动甘蔗/竹子机", n, comps, raw);
    }

    public static BlueprintBOM getPumpkinMelonFarmBOM(int modules) {
        int n = Math.max(1, modules);
        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:piston", "普通活塞", n));
        comps.add(new ItemStack("minecraft:observer", "侦测器 (Observer)", n));
        comps.add(new ItemStack("minecraft:redstone", "红石粉", n));
        comps.add(new ItemStack("minecraft:pumpkin_seeds", "南瓜/西瓜种子", n));
        comps.add(new ItemStack("minecraft:stone_bricks", "实心建筑方块", n * 3));
        comps.add(new ItemStack("minecraft:hopper_minecart", "漏斗矿车", 1));
        comps.add(new ItemStack("minecraft:rail", "普通铁轨", Math.max(2, n)));
        comps.add(new ItemStack("minecraft:powered_rail", "充能铁轨", 2));
        comps.add(new ItemStack("minecraft:hopper", "漏斗", 1));
        comps.add(new ItemStack("minecraft:chest", "箱子", 2));

        List<ItemStack> raw = new ArrayList<>();
        raw.add(new ItemStack("minecraft:iron_ingot", "铁锭", n + 16));
        raw.add(new ItemStack("minecraft:redstone", "红石粉总消耗", n * 3 + 2));
        raw.add(new ItemStack("minecraft:nether_quartz", "下界石英", n));
        raw.add(new ItemStack("minecraft:cobblestone", "圆石", n * 10));

        return new BlueprintBOM(ID_PUMPKIN_MELON_FARM, "全自动南瓜/西瓜机", n, comps, raw);
    }

    public static BlueprintBOM getBeaconBOM(int tier) {
        int t = Math.max(1, Math.min(4, tier));
        int blocks;
        switch (t) {
            case 1: blocks = 9; break;
            case 2: blocks = 34; break;
            case 3: blocks = 83; break;
            case 4: default: blocks = 164; break;
        }

        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:beacon", "信标", 1));
        comps.add(new ItemStack("minecraft:iron_block", "矿物方块 (铁/金/绿宝石/钻石块)", blocks));

        List<ItemStack> raw = new ArrayList<>();
        raw.add(new ItemStack("minecraft:iron_ingot", "对应矿物原锭 (9 倍)", blocks * 9));
        raw.add(new ItemStack("minecraft:nether_star", "下界之星 (信标合成)", 1));
        raw.add(new ItemStack("minecraft:obsidian", "黑曜石 (信标合成)", 3));
        raw.add(new ItemStack("minecraft:glass", "玻璃 (信标合成)", 5));

        return new BlueprintBOM(ID_BEACON_STRUCTURE, t + " 级信标金字塔底座", t, comps, raw);
    }

    public static BlueprintBOM getStoneGeneratorBOM() {
        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:water_bucket", "水桶", 1));
        comps.add(new ItemStack("minecraft:lava_bucket", "岩浆桶", 1));
        comps.add(new ItemStack("minecraft:piston", "普通活塞", 1));
        comps.add(new ItemStack("minecraft:observer", "侦测器", 1));
        comps.add(new ItemStack("minecraft:redstone", "红石粉", 2));
        comps.add(new ItemStack("minecraft:stone_bricks", "耐火建筑方块", 16));
        comps.add(new ItemStack("minecraft:hopper", "漏斗", 1));
        comps.add(new ItemStack("minecraft:chest", "箱子", 2));

        return new BlueprintBOM(ID_STONE_GENERATOR, "安全高效刷石机", 1, comps, Collections.emptyList());
    }

    public static BlueprintBOM getItemSorterBOM(int modules) {
        int n = Math.max(1, modules);
        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:hopper", "漏斗", n * 3));
        comps.add(new ItemStack("minecraft:comparator", "红石比较器", n));
        comps.add(new ItemStack("minecraft:repeater", "红石中继器", n));
        comps.add(new ItemStack("minecraft:redstone_torch", "红石火把", n));
        comps.add(new ItemStack("minecraft:redstone", "红石粉", n * 3));
        comps.add(new ItemStack("minecraft:chest", "箱子", n * 2));
        comps.add(new ItemStack("minecraft:stone_bricks", "实心方块", n * 8));

        List<ItemStack> raw = new ArrayList<>();
        raw.add(new ItemStack("minecraft:iron_ingot", "铁锭 (漏斗)", n * 15));
        raw.add(new ItemStack("minecraft:redstone", "红石粉总消耗", n * 6));
        raw.add(new ItemStack("minecraft:nether_quartz", "下界石英", n));
        raw.add(new ItemStack("minecraft:oak_planks", "木板", n * 30));

        return new BlueprintBOM(ID_ITEM_SORTER, "22物品标准漏斗分类机", n, comps, raw);
    }

    public static BlueprintBOM getEthoClockBOM() {
        List<ItemStack> comps = new ArrayList<>();
        comps.add(new ItemStack("minecraft:hopper", "漏斗", 2));
        comps.add(new ItemStack("minecraft:comparator", "红石比较器", 2));
        comps.add(new ItemStack("minecraft:sticky_piston", "粘性活塞", 2));
        comps.add(new ItemStack("minecraft:redstone_block", "红石块", 1));
        comps.add(new ItemStack("minecraft:redstone", "红石粉", 2));
        comps.add(new ItemStack("minecraft:stone_bricks", "实心方块", 2));
        comps.add(new ItemStack("minecraft:cobblestone", "计时填充物品 (如圆石)", 64));

        return new BlueprintBOM(ID_ETHO_CLOCK, "Etho 双漏斗长周期时钟", 1, comps, Collections.emptyList());
    }

    public static BlueprintBOM getBOM(String blueprintId, int scale) {
        if (blueprintId == null) return getSugarCaneFarmBOM(8);
        String id = blueprintId.trim().toUpperCase();
        if (id.contains("SUGAR_CANE") || id.contains("甘蔗") || id.contains("竹子")) {
            return getSugarCaneFarmBOM(scale <= 0 ? 8 : scale);
        } else if (id.contains("PUMPKIN") || id.contains("MELON") || id.contains("南瓜") || id.contains("西瓜")) {
            return getPumpkinMelonFarmBOM(scale <= 0 ? 4 : scale);
        } else if (id.contains("BEACON") || id.contains("信标")) {
            return getBeaconBOM(scale <= 0 ? 4 : scale);
        } else if (id.contains("STONE") || id.contains("刷石") || id.contains("造石")) {
            return getStoneGeneratorBOM();
        } else if (id.contains("SORT") || id.contains("分类")) {
            return getItemSorterBOM(scale <= 0 ? 1 : scale);
        } else if (id.contains("CLOCK") || id.contains("时钟") || id.contains("ETHO")) {
            return getEthoClockBOM();
        }
        return getSugarCaneFarmBOM(scale <= 0 ? 8 : scale);
    }

    /**
     * Parses human natural language query to match relevant blueprint BOM.
     */
    public static Optional<BlueprintBOM> matchBOM(String query) {
        if (query == null) return Optional.empty();
        String q = query.trim().toLowerCase();
        boolean isMaterialQuery = q.contains("材料") || q.contains("原料") || q.contains("清单") ||
                q.contains("要多少") || q.contains("需要什么") || q.contains("需要多少") || q.contains("bom");

        if (!isMaterialQuery) return Optional.empty();

        if (q.contains("甘蔗") || q.contains("竹子")) {
            return Optional.of(getSugarCaneFarmBOM(8));
        }
        if (q.contains("南瓜") || q.contains("西瓜")) {
            return Optional.of(getPumpkinMelonFarmBOM(4));
        }
        if (q.contains("信标") || q.contains("金字塔")) {
            int tier = 4;
            if (q.contains("1级") || q.contains("一级")) tier = 1;
            else if (q.contains("2级") || q.contains("二级")) tier = 2;
            else if (q.contains("3级") || q.contains("三级")) tier = 3;
            return Optional.of(getBeaconBOM(tier));
        }
        if (q.contains("刷石") || q.contains("造石") || q.contains("圆石")) {
            return Optional.of(getStoneGeneratorBOM());
        }
        if (q.contains("分类机") || q.contains("分类漏斗") || q.contains("物品分类")) {
            return Optional.of(getItemSorterBOM(1));
        }
        if (q.contains("时钟") || q.contains("漏斗时钟") || q.contains("etho")) {
            return Optional.of(getEthoClockBOM());
        }

        return Optional.empty();
    }
}
