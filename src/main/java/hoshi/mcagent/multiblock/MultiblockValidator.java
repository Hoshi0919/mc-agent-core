package hoshi.mcagent.multiblock;

import hoshi.mcagent.context.InventorySnapshot;

import java.util.*;

/**
 * Multiblock Blueprint Validator and Assembly Guide for modern Minecraft.
 * Supports Conduit, Beacon, Nether Portal, End Portal, Wither and Golem structures.
 */
public class MultiblockValidator {

    private static final Map<String, MultiblockBlueprint> BLUEPRINTS = new LinkedHashMap<>();

    static {
        // 1. Conduit 3-Ring Full Power (5x5x5)
        Map<String, Integer> conduitReq = new LinkedHashMap<>();
        conduitReq.put("minecraft:prismarine", 42); // Prismarine blocks (prismarine, dark prismarine, prismarine bricks, sea lantern)
        conduitReq.put("minecraft:conduit", 1);
        List<String[]> conduitLayers = List.of(
                new String[]{"  #  ", " ### ", "#####", " ### ", "  #  "},
                new String[]{" # # ", "#   #", "#   #", "#   #", " # # "},
                new String[]{"##C##", "#   #", "# C #", "#   #", "##C##"},
                new String[]{" # # ", "#   #", "#   #", "#   #", " # # "},
                new String[]{"  #  ", " ### ", "#####", " ### ", "  #  "}
        );
        register(new MultiblockBlueprint(
                "conduit",
                "潮涌核心满级三环 (Conduit 3-Ring Frame)",
                5, 5, 5,
                conduitReq,
                conduitLayers,
                "中心潮涌核心必须被 3x3x3 范围内的水体（水源/流水/含水方块）完全包裹；外部海晶石框架不可接触空气",
                "满级 42 块海晶石激活：潮涌能量范围达到最大 96 格半径（水下呼吸、夜视、极速挖掘），且对 8 格内敌对生物每 2 秒施加 4 点电击伤害"
        ));

        // 2. Beacon Tier 4 Full Pyramid (9x9 base, 4 layers)
        Map<String, Integer> beaconReq = new LinkedHashMap<>();
        beaconReq.put("minecraft:iron_block", 164); // or gold/emerald/diamond/netherite
        beaconReq.put("minecraft:beacon", 1);
        List<String[]> beaconLayers = List.of(
                new String[]{"9x9 实心矿物块 (81 块)"},
                new String[]{"7x7 实心矿物块 (49 块)"},
                new String[]{"5x5 实心矿物块 (25 块)"},
                new String[]{"3x3 实心矿物块 (9 块)"},
                new String[]{"中心放置信标方块 (1 块)"}
        );
        register(new MultiblockBlueprint(
                "beacon_tier4",
                "四级信标金字塔 (Tier 4 Beacon Pyramid)",
                9, 5, 9,
                beaconReq,
                beaconLayers,
                "信标正上方必须直视天空（高度 320），严禁有任何不透明实体方块阻挡（玻璃、水、栅栏等透明方块允许）",
                "四层完整金字塔 (164 矿物块)：激活急迫 II (Haste II) 与生命恢复 (Regeneration)，影响半径 50 格，持下界合金镐可实现秒挖深板岩"
        ));

        // 3. Beacon Tier 1 Basic Pyramid (3x3 base)
        Map<String, Integer> beaconT1Req = new LinkedHashMap<>();
        beaconT1Req.put("minecraft:iron_block", 9);
        beaconT1Req.put("minecraft:beacon", 1);
        register(new MultiblockBlueprint(
                "beacon_tier1",
                "一级信标基座 (Tier 1 Beacon)",
                3, 2, 3,
                beaconT1Req,
                List.of(
                        new String[]{"3x3 实心矿物块 (9 块)"},
                        new String[]{"中心放置信标方块 (1 块)"}
                ),
                "信标正上方直视天空无遮挡",
                "一层基座 (9 矿物块)：基础速度 I 或急迫 I，影响半径 20 格"
        ));

        // 4. Nether Portal Standard (4x5)
        Map<String, Integer> portalReq = new LinkedHashMap<>();
        portalReq.put("minecraft:obsidian", 14); // 10 blocks without corners, 14 with corners
        portalReq.put("minecraft:flint_and_steel", 1);
        List<String[]> portalLayers = List.of(
                new String[]{"#### (底座 4 块，四角可留空为 2 块)"},
                new String[]{"#  # (立柱第 1 层)"},
                new String[]{"#  # (立柱第 2 层)"},
                new String[]{"#  # (立柱第 3 层)"},
                new String[]{"#### (顶梁 4 块，四角可留空为 2 块)"}
        );
        register(new MultiblockBlueprint(
                "nether_portal",
                "下界传送门标准框架 (Nether Portal 4x5)",
                4, 5, 1,
                portalReq,
                portalLayers,
                "黑曜石框架内空至少 2x3，最大 21x21；内部使用打火石、火弹或引燃火焰即可激活紫光帷幕",
                "跨维度穿梭：主界与下界水平坐标 8:1 欧氏映射；投掷物/实体穿过可触发目标区块瞬时 15 秒强加载"
        ));

        // 5. End Portal Frame (3x3 inner, 5x5 total)
        Map<String, Integer> endPortalReq = new LinkedHashMap<>();
        endPortalReq.put("minecraft:end_portal_frame", 12);
        endPortalReq.put("minecraft:ender_eye", 12);
        List<String[]> endPortalLayers = List.of(
                new String[]{" FFF "},
                new String[]{"F   F"},
                new String[]{"F   F"},
                new String[]{"F   F"},
                new String[]{" FFF "}
        );
        register(new MultiblockBlueprint(
                "end_portal",
                "末地传送门悬空环 (End Portal Ring)",
                5, 1, 5,
                endPortalReq,
                endPortalLayers,
                "所有 12 个末地传送门框架的正面朝向 (facing) 必须向内朝向中心；每个框架嵌入末影之眼后激活 3x3 星空传送门",
                "单向传送至末地中心岛黑曜石平台 (100, 49, 0)；通往末影龙主战场"
        ));

        // 6. Wither Assembly
        Map<String, Integer> witherReq = new LinkedHashMap<>();
        witherReq.put("minecraft:soul_sand", 4); // or soul_soil
        witherReq.put("minecraft:wither_skeleton_skull", 3);
        register(new MultiblockBlueprint(
                "wither",
                "凋灵召唤构架 (Wither Boss Assembly)",
                3, 3, 1,
                witherReq,
                List.of(
                        new String[]{"底座：1 块灵魂沙/灵魂土"},
                        new String[]{"中层：3 块横向灵魂沙/灵魂土 (T 字型)"},
                        new String[]{"顶层：3 颗凋灵骷髅头颅 (最后放置第 3 颗触发苏醒)"}
                ),
                "必须保证头颅最后安放，且周围无草丛或积雪阻挡空气；生成后拥有数秒充能无敌期并释放巨大爆炸",
                "击败掉落下界之星 (Nether Star)，用于合成信标"
        ));

        // 7. Iron Golem Assembly
        Map<String, Integer> golemReq = new LinkedHashMap<>();
        golemReq.put("minecraft:iron_block", 4);
        golemReq.put("minecraft:carved_pumpkin", 1);
        register(new MultiblockBlueprint(
                "iron_golem",
                "铁傀儡装配构架 (Iron Golem Assembly)",
                3, 3, 1,
                golemReq,
                List.of(
                        new String[]{"底座：1 块铁块"},
                        new String[]{"中层：3 块横向铁块 (T 字型)"},
                        new String[]{"顶层：中心 1 块雕刻南瓜/南瓜灯 (最后放置)"}
                ),
                "南瓜必须最后放置，且傀儡生成空间 2x3x2 内不得有其他实体阻挡",
                "生成 100 HP 强力守卫；手持铁锭可右键回血修复"
        ));
    }

    private static void register(MultiblockBlueprint bp) {
        BLUEPRINTS.put(bp.id().toLowerCase(), bp);
    }

    public static Collection<MultiblockBlueprint> getAllBlueprints() {
        return Collections.unmodifiableCollection(BLUEPRINTS.values());
    }

    public static Optional<MultiblockBlueprint> findBlueprint(String query) {
        if (query == null || query.trim().isEmpty()) {
            return Optional.empty();
        }
        String clean = query.trim().toLowerCase()
                .replace(" ", "_")
                .replace("minecraft:", "");

        // 1. Direct key
        if (BLUEPRINTS.containsKey(clean)) {
            return Optional.of(BLUEPRINTS.get(clean));
        }

        // 2. Alias mapping
        if (clean.contains("conduit") || clean.contains("潮涌") || clean.contains("海晶")) {
            return Optional.of(BLUEPRINTS.get("conduit"));
        }
        if (clean.equals("beacon") || clean.contains("信标") || clean.contains("金字塔")) {
            return Optional.of(BLUEPRINTS.get("beacon_tier4"));
        }
        if (clean.contains("beacon_t1") || clean.contains("一级信标")) {
            return Optional.of(BLUEPRINTS.get("beacon_tier1"));
        }
        if (clean.contains("portal") || clean.contains("地狱门") || clean.contains("传送门") || clean.contains("下界门")) {
            return Optional.of(BLUEPRINTS.get("nether_portal"));
        }
        if (clean.contains("end_portal") || clean.contains("末地门") || clean.contains("末地传送门")) {
            return Optional.of(BLUEPRINTS.get("end_portal"));
        }
        if (clean.contains("wither") || clean.contains("凋灵") || clean.contains("凋零")) {
            return Optional.of(BLUEPRINTS.get("wither"));
        }
        if (clean.contains("golem") || clean.contains("铁傀儡")) {
            return Optional.of(BLUEPRINTS.get("iron_golem"));
        }

        // 3. Fallback search
        for (MultiblockBlueprint bp : BLUEPRINTS.values()) {
            if (bp.id().contains(clean) || bp.name().toLowerCase().contains(clean)) {
                return Optional.of(bp);
            }
        }
        return Optional.empty();
    }

    public record MaterialGap(
            String itemId,
            int requiredCount,
            int availableCount,
            int missingCount
    ) {
        public boolean isSatisfied() {
            return missingCount <= 0;
        }
    }

    public record MultiblockReport(
            MultiblockBlueprint blueprint,
            boolean isFullyReady,
            double completionRate,
            List<MaterialGap> gaps,
            String summaryText
    ) {
        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("§6【多方块装配蓝图：%s】§r\n", blueprint.name()));
            sb.append(String.format("▸ §7几何规格§r：%d×%d×%d | 方块总量: §e%d 块§r | 背包满足度: §%s%.1f%%§r\n",
                    blueprint.widthX(), blueprint.heightY(), blueprint.depthZ(),
                    blueprint.totalBlockCount(), isFullyReady ? "a" : "c", completionRate * 100));

            sb.append("▸ §b原料核验§r：\n");
            for (MaterialGap gap : gaps) {
                String status = gap.isSatisfied()
                        ? String.format("§a✔ %s: %d/%d§r", gap.itemId(), gap.availableCount(), gap.requiredCount())
                        : String.format("§c✘ %s: %d/%d (还缺 %d 个)§r", gap.itemId(), gap.availableCount(), gap.requiredCount(), gap.missingCount());
                sb.append("  ").append(status).append("\n");
            }

            sb.append(String.format("▸ §e激活条件§r：%s\n", blueprint.coreActivationCondition()));
            sb.append(String.format("▸ §a增益效果§r：%s\n", blueprint.perksAndRange()));

            if (isFullyReady) {
                sb.append("§a[Hoshi 校验] 恭喜！当前背包材料已 100% 齐备，可直接开工搭建！§r");
            } else {
                sb.append("§e[Hoshi 提示] 材料尚未完全备齐，请收集齐上述红叉原料后再行封顶激活。§r");
            }
            return sb.toString();
        }
    }

    public static MultiblockReport validateInventory(MultiblockBlueprint bp, InventorySnapshot inventory) {
        Objects.requireNonNull(bp, "blueprint");
        List<MaterialGap> gaps = new ArrayList<>();
        int satisfiedTypes = 0;
        int totalRequiredBlocks = 0;
        int totalAvailableCount = 0;

        for (Map.Entry<String, Integer> entry : bp.requiredBlocks().entrySet()) {
            String itemId = entry.getKey();
            int req = entry.getValue();
            totalRequiredBlocks += req;

            int available = 0;
            if (inventory != null) {
                available = inventory.countItem(itemId);
                // Smart alias for prismarine: allow prismarine_bricks / dark_prismarine / sea_lantern
                if (itemId.equals("minecraft:prismarine")) {
                    available += inventory.countItem("minecraft:prismarine_bricks");
                    available += inventory.countItem("minecraft:dark_prismarine");
                    available += inventory.countItem("minecraft:sea_lantern");
                }
                // Smart alias for beacon mineral blocks: iron, gold, emerald, diamond, netherite
                if (itemId.equals("minecraft:iron_block")) {
                    available += inventory.countItem("minecraft:gold_block");
                    available += inventory.countItem("minecraft:emerald_block");
                    available += inventory.countItem("minecraft:diamond_block");
                    available += inventory.countItem("minecraft:netherite_block");
                }
                // Smart alias for soul sand: allow soul soil
                if (itemId.equals("minecraft:soul_sand")) {
                    available += inventory.countItem("minecraft:soul_soil");
                }
                // Smart alias for carved pumpkin: allow jack_o_lantern
                if (itemId.equals("minecraft:carved_pumpkin")) {
                    available += inventory.countItem("minecraft:jack_o_lantern");
                }
            }

            int missing = Math.max(0, req - available);
            gaps.add(new MaterialGap(itemId, req, available, missing));
            totalAvailableCount += Math.min(available, req);
            if (missing == 0) {
                satisfiedTypes++;
            }
        }

        boolean fullyReady = satisfiedTypes == bp.requiredBlocks().size();
        double rate = totalRequiredBlocks > 0 ? (double) totalAvailableCount / totalRequiredBlocks : 1.0;
        return new MultiblockReport(bp, fullyReady, rate, gaps, fullyReady ? "MATERIALS_READY" : "MATERIALS_MISSING");
    }
}
