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

    public record LogisticsReport(
            boolean isLogisticsOrRedstone,
            String componentType,
            String stateDetails,
            String actionableAdvice
    ) {
        public static LogisticsReport none() {
            return new LogisticsReport(false, "NONE", "非红石/物流交互方块", "");
        }
    }

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

    /**
     * Evaluates in-depth Redstone & Logistics mechanics when looking at automation blocks.
     */
    public LogisticsReport evaluateLogisticsOrRedstone() {
        if (isAir() || blockId == null) {
            return LogisticsReport.none();
        }
        String id = blockId.toLowerCase();

        // 1. Hopper
        if (id.contains("hopper")) {
            String facing = properties.getOrDefault("facing", "down");
            String enabledStr = properties.getOrDefault("enabled", "true");
            boolean locked = "false".equalsIgnoreCase(enabledStr);

            String state = locked
                    ? String.format("⚡ [已锁定 LOCKED] 漏斗被红石信号强充能锁定！当前朝向: %s", facing)
                    : String.format("✔ [流通就绪 UNLOCKED] 漏斗处于正常非锁定流通状态。当前朝向: %s", facing);

            String advice = locked
                    ? "警告：红石充能导致停止吸取与漏出物品！请检查紧邻红石粉、红石火把或强充能方块。"
                    : (facing.equals("down")
                        ? "传输速率: 2.5 组/秒 (4红石刻/个)。物品分类器推荐 41+1+1+1+1 (防串线) 或 18+1+1+1+1 布局。"
                        : "朝向侧方推入容器。若需向下传输请调整漏斗放置对准底部。");

            return new LogisticsReport(true, "HOPPER", state, advice);
        }

        // 2. Comparator
        if (id.contains("comparator")) {
            String mode = properties.getOrDefault("mode", "compare");
            boolean isSubtract = "subtract".equalsIgnoreCase(mode);

            String state = isSubtract
                    ? "⚡ [减法模式 SUBTRACT (前置火把点亮)] 输出 = max(0, 后端信号 - max(左侧信号, 右侧信号))"
                    : "✔ [比较模式 COMPARE (前置火把熄灭)] 若后端输入 ≥ 两侧最大输入则输出后端信号，否则输出 0";

            String advice = "容器满度公式: 信号强度 = floor(1 + (当前物品数 / (格数 × 64)) × 14)。只要有 1 个物品至少输出 1 格信号。";
            return new LogisticsReport(true, "COMPARATOR", state, advice);
        }

        // 3. Repeater
        if (id.contains("repeater")) {
            String delayStr = properties.getOrDefault("delay", "1");
            int delay = 1;
            try { delay = Integer.parseInt(delayStr); } catch (NumberFormatException ignored) {}
            String lockedStr = properties.getOrDefault("locked", "false");
            boolean isLocked = "true".equalsIgnoreCase(lockedStr);

            String state = String.format("%s延迟: %d 红石刻 (%d 游戏刻 / %.1fs)",
                    isLocked ? "🔒 [锁存锁定 LATCHED] " : "✔ [正常传导] ",
                    delay, delay * 2, delay * 0.1);

            String advice = isLocked
                    ? "侧向通电的中继器正将此前状态锁存锁定！解除侧向信号方可恢复动态传导。"
                    : "满格 15 级信号强中继输出；右键可循环调节 1~4 刻延迟。";
            return new LogisticsReport(true, "REPEATER", state, advice);
        }

        // 4. Observer
        if (id.contains("observer")) {
            String facing = properties.getOrDefault("facing", "south");
            String poweredStr = properties.getOrDefault("powered", "false");
            boolean isPowered = "true".equalsIgnoreCase(poweredStr);

            String state = String.format("侦测面朝向: %s | 当前脉冲状态: %s", facing, isPowered ? "发射中 (ACTIVE)" : "待命 (IDLE)");
            String advice = "感应前方方块状态更新 (BlockState Update)，后侧输出持续 1 红石刻 (2 游戏刻 / 0.1s) 瞬时脉冲。双侦测器面迎面相对可构成 2-tick 超高频时钟。";
            return new LogisticsReport(true, "OBSERVER", state, advice);
        }

        // 5. Crafter (1.21)
        if (id.contains("crafter")) {
            String triggeredStr = properties.getOrDefault("triggered", "false");
            String orientation = properties.getOrDefault("orientation", "north_up");
            String state = String.format("1.21 自动合成器 | 朝向: %s | 触发状态: %s", orientation, triggeredStr);
            String advice = "接收红石上升沿脉冲瞬时合成并弹出成品！配合比较器可读取被禁用或有物品的槽位数 (0~9)。";
            return new LogisticsReport(true, "CRAFTER", state, advice);
        }

        // 6. Daylight Detector
        if (id.contains("daylight_detector")) {
            String invertedStr = properties.getOrDefault("inverted", "false");
            boolean inverted = "true".equalsIgnoreCase(invertedStr);
            String state = inverted ? "🌙 [夜间/反转模式 (月光探测)]" : "☀️ [白昼/正常模式 (日光探测)]";
            String advice = inverted
                    ? "黑夜与雷雨天光照降低时输出高电平，常用于全自动路灯与夜间警报。"
                    : "白昼正午输出最高 15 级强电平，随太阳高度角升降动态衰减。右键可切换为反转模式。";
            return new LogisticsReport(true, "DAYLIGHT_DETECTOR", state, advice);
        }

        // 7. Sculk Sensor
        if (id.contains("sculk_sensor")) {
            boolean calibrated = id.contains("calibrated");
            String phase = properties.getOrDefault("sculk_sensor_phase", "inactive");
            String state = String.format("%s幽匿感测体 | 状态: %s", calibrated ? "💎 [校准型] " : "📡 [标准型] ", phase);
            String advice = calibrated
                    ? "通过后方/侧方红石信号 (1~15) 过滤单一频率 (1=移动, 6=装填, 12=受击, 13=死亡)；羊毛可 100% 阻隔振动传导。"
                    : "感应半径 8 格内振动波，输出强度对应振动频率 (1~15)；羊毛可 100% 隔音。";
            return new LogisticsReport(true, "SCULK_SENSOR", state, advice);
        }

        // 8. Bubble Column (Soul sand & Magma)
        if (id.contains("soul_sand") || id.contains("magma_block")) {
            boolean isSoul = id.contains("soul_sand");
            String state = isSoul ? "🫧 [上升气泡柱基座]" : "🌀 [下沉涡流基座]";
            String advice = isSoul
                    ? "上方水域生成极速上升气泡柱 (约 11 格/秒) 并补充氧气。前置关键：垂直水柱每一格必须全部为【水源 (Water Source)】，可用海带顺水种植一键转化！"
                    : "上方水域生成极速向下涡流并消耗氧气。前置关键：垂直水柱每一格必须全部为【水源】。";
            return new LogisticsReport(true, isSoul ? "SOUL_SAND_BUBBLE" : "MAGMA_BUBBLE", state, advice);
        }

        // 9. Dropper & Dispenser
        if (id.contains("dropper") || id.contains("dispenser")) {
            boolean isDispenser = id.contains("dispenser");
            String state = isDispenser ? "🏹 [发射器 (Dispenser)]" : "📦 [投掷器 (Dropper)]";
            String advice = isDispenser
                    ? "具备专属执行逻辑：射箭/药水、装填护甲/鞘翅、放置水桶岩浆、剪羊毛、点燃 TNT 等。不可用于常规无损物品管道！"
                    : "无论盛装何物，均以掉落物实体 (Item Entity) 吐出。适合垂直级联搭建投掷器物品升降机。";
            return new LogisticsReport(true, isDispenser ? "DISPENSER" : "DROPPER", state, advice);
        }

        return LogisticsReport.none();
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
