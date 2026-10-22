package hoshi.mcagent.crafting;

import hoshi.mcagent.context.InventorySnapshot;

import java.util.*;

/**
 * Checks player inventory readiness against survival and redstone crafting recipes,
 * calculating missing materials, craftable quantities, and actionable instructions.
 */
public final class CraftingReadinessChecker {

    public record IngredientStatus(
            String itemId,
            int requiredCount,
            int currentCount,
            boolean isSufficient
    ) {
        public int missingCount() {
            return Math.max(0, requiredCount - currentCount);
        }
    }

    public record CraftingReport(
            boolean isKnownRecipe,
            CraftingRecipe recipe,
            boolean isReady,
            int maxCraftable,
            List<IngredientStatus> ingredientStatuses,
            String formattedMessage,
            String suggestedCommand
    ) {}

    private static final Map<String, CraftingRecipe> RECIPES = new LinkedHashMap<>();

    static {
        register(new CraftingRecipe("hopper", "漏斗", "REDSTONE", 1,
                Map.of("iron_ingot", 5, "chest", 1),
                "漏斗支持漏斗矿车与全自动物流，铁锭不够可用原木现合箱子"));

        register(new CraftingRecipe("piston", "普通活塞", "REDSTONE", 1,
                Map.of("oak_planks", 3, "cobblestone", 4, "iron_ingot", 1, "redstone", 1),
                "木板可使用任意原木合成，圆石需使用镐子挖掘"));

        register(new CraftingRecipe("sticky_piston", "粘性活塞", "REDSTONE", 1,
                Map.of("piston", 1, "slime_ball", 1),
                "粘性活塞可在沼泽或史莱姆区块击杀史莱姆获取粘液球"));

        register(new CraftingRecipe("observer", "侦测器", "REDSTONE", 1,
                Map.of("cobblestone", 6, "redstone", 2, "quartz", 1),
                "下界石英需前往下界地狱挖掘，侦测器可检测方块状态更新并输出 1-tick 脉冲"));

        register(new CraftingRecipe("comparator", "红石比较器", "REDSTONE", 1,
                Map.of("stone", 3, "redstone_torch", 3, "quartz", 1),
                "注意底座必须是平滑石头(Stone)，圆石烧制后方可使用！不可直接用圆石！"));

        register(new CraftingRecipe("repeater", "红石中继器", "REDSTONE", 1,
                Map.of("stone", 3, "redstone_torch", 2, "redstone", 1),
                "同样必须使用烧制石头(Stone)，右键可调节 1~4 档延迟 (2~8 ticks)"));

        register(new CraftingRecipe("enchanting_table", "附魔台", "MAGIC", 1,
                Map.of("book", 1, "diamond", 2, "obsidian", 4),
                "需要 1 本书、2 颗钻石与 4 块黑曜石；满级附魔需周围摆放 15 个书架"));

        register(new CraftingRecipe("beacon", "信标", "UTILITY", 1,
                Map.of("nether_star", 1, "obsidian", 3, "glass", 5),
                "击败凋灵掉落下界之星；基座需由 9~164 块铁/金/绿宝石/钻石/下界合金块搭建"));

        register(new CraftingRecipe("brewing_stand", "酿造台", "POTION", 1,
                Map.of("blaze_rod", 1, "cobblestone", 3),
                "烈焰棒需在下界要塞击杀烈焰人获取，酿造时需消耗烈焰粉作为燃料"));

        register(new CraftingRecipe("conduit", "潮涌核心", "OCEAN", 1,
                Map.of("heart_of_the_sea", 1, "nautilus_shell", 8),
                "海洋之心在埋藏的宝藏箱中获取，鹦鹉螺壳通过钓鱼或击杀溺尸获取"));

        register(new CraftingRecipe("anvil", "铁砧", "SURVIVAL", 1,
                Map.of("iron_block", 3, "iron_ingot", 4),
                "总计需消耗 31 块铁锭 (3个铁块=27铁锭 + 4铁锭)"));

        register(new CraftingRecipe("shield", "盾牌", "COMBAT", 1,
                Map.of("oak_planks", 6, "iron_ingot", 1),
                "手持右键可格挡 100% 近战与箭矢伤害，受到斧头劈砍会被破盾 5 秒"));

        register(new CraftingRecipe("bow", "弓", "COMBAT", 1,
                Map.of("stick", 3, "string", 3),
                "蜘蛛掉落线，合成弓后可在铁砧敲上力量/无限/火矢附魔"));

        register(new CraftingRecipe("crossbow", "弩", "COMBAT", 1,
                Map.of("stick", 3, "string", 2, "iron_ingot", 1, "tripwire_hook", 1),
                "射程更远更平直，可附魔多重射击与快速装填，装填烟花火箭射击"));

        register(new CraftingRecipe("lightning_rod", "避雷针", "UTILITY", 1,
                Map.of("copper_ingot", 3),
                "3 根铜锭垂直排列合成，引雷半径 128 格，被雷劈中输出 15 级红石信号"));

        register(new CraftingRecipe("tnt", "TNT", "UTILITY", 1,
                Map.of("gunpowder", 5, "sand", 4),
                "苦力怕掉落火药，可用于矿井爆破或制作 TNT 复制推挤机"));

        register(new CraftingRecipe("dispenser", "发射器", "REDSTONE", 1,
                Map.of("cobblestone", 7, "bow", 1, "redstone", 1),
                "中间需放入一把完好或破损的弓，可发射箭矢、水桶、烟花等实体"));
    }

    private static void register(CraftingRecipe recipe) {
        RECIPES.put(recipe.recipeId(), recipe);
    }

    public static Map<String, CraftingRecipe> getKnownRecipes() {
        return Collections.unmodifiableMap(RECIPES);
    }

    /**
     * Finds a matching recipe by user query string or item id.
     */
    public static Optional<CraftingRecipe> findRecipe(String query) {
        if (query == null || query.isBlank()) return Optional.empty();
        String q = query.toLowerCase().replace("minecraft:", "").trim();

        for (Map.Entry<String, CraftingRecipe> entry : RECIPES.entrySet()) {
            if (q.contains(entry.getKey()) || q.contains(entry.getValue().displayName().toLowerCase())) {
                return Optional.of(entry.getValue());
            }
        }
        return Optional.empty();
    }

    /**
     * Evaluates crafting readiness against player's inventory snapshot.
     */
    public static CraftingReport evaluate(String query, InventorySnapshot inventory) {
        Optional<CraftingRecipe> opt = findRecipe(query);
        if (opt.isEmpty()) {
            return new CraftingReport(false, null, false, 0, Collections.emptyList(),
                    "§c[Hoshi] 未找到匹配的合成配方。支持查询：漏斗、活塞、比较器、中继器、侦测器、信标、附魔台、潮涌核心、铁砧、盾牌、弓等。",
                    "/hoshi craft hopper");
        }

        CraftingRecipe recipe = opt.get();
        List<IngredientStatus> statuses = new ArrayList<>();
        boolean allReady = true;
        int maxCraft = Integer.MAX_VALUE;

        for (Map.Entry<String, Integer> ing : recipe.ingredients().entrySet()) {
            String ingId = ing.getKey();
            int req = ing.getValue();

            // Check inventory count (with special fallback alias: e.g. oak_planks matches any planks)
            int have = countWithFallback(inventory, ingId);
            boolean ok = have >= req;
            if (!ok) {
                allReady = false;
            }
            int craftableFromThis = req > 0 ? (have / req) : 0;
            if (craftableFromThis < maxCraft) {
                maxCraft = craftableFromThis;
            }
            statuses.add(new IngredientStatus(ingId, req, have, ok));
        }

        if (!allReady) {
            maxCraft = 0;
        }

        StringBuilder sb = new StringBuilder();
        if (allReady) {
            sb.append(String.format("§a✔【材料齐全！可合成 %s】§r\n", recipe.displayName()));
            sb.append(String.format("▸ 当前背包原料最多可连续合成：§e%d 个§r\n", maxCraft * recipe.outputCount()));
            sb.append("▸ 消耗清单：");
            List<String> parts = new ArrayList<>();
            for (IngredientStatus st : statuses) {
                parts.add(String.format("%s × %d (背包存量: %d)", st.itemId(), st.requiredCount(), st.currentCount()));
            }
            sb.append(String.join(", ", parts)).append("\n");
            sb.append(String.format("▸ 专家提示：%s", recipe.craftTip()));
        } else {
            sb.append(String.format("§c✖【材料不足！无法合成 %s】§r\n", recipe.displayName()));
            sb.append("▸ 缺失材料明细：\n");
            for (IngredientStatus st : statuses) {
                if (!st.isSufficient()) {
                    sb.append(String.format("  §c✗ %s: 缺少 %d 个 (当前: %d / 需求: %d)§r\n",
                            st.itemId(), st.missingCount(), st.currentCount(), st.requiredCount()));
                } else {
                    sb.append(String.format("  §a✓ %s: 满足 (当前: %d / 需求: %d)§r\n",
                            st.itemId(), st.currentCount(), st.requiredCount()));
                }
            }
            sb.append(String.format("▸ 建议：%s", recipe.craftTip()));
        }

        return new CraftingReport(true, recipe, allReady, maxCraft, statuses, sb.toString(), null);
    }

    private static int countWithFallback(InventorySnapshot inv, String ingId) {
        if (inv == null) return 0;
        int direct = inv.countItem(ingId);
        if (direct > 0) return direct;

        // Fallbacks: oak_planks -> count any wood planks
        if (ingId.contains("planks")) {
            int totalPlanks = 0;
            for (String wood : List.of("oak_planks", "spruce_planks", "birch_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "mangrove_planks", "cherry_planks", "bamboo_planks", "crimson_planks", "warped_planks")) {
                totalPlanks += inv.countItem(wood);
            }
            return totalPlanks;
        }
        return 0;
    }
}
