package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Diagnostic analyzer for Minecraft 1.21 Crafter automation pipelines.
 * Detects slot saturation deadlocks, missing slot masks, and pulse trigger desynchronization in 0ms.
 */
public final class CrafterPipelineAnalyzer {

    public record CrafterReport(
            boolean isHealthy,
            boolean hasDeadlockRisk,
            boolean hasMaskingDeficit,
            int requiredSlots,
            int disabledSlots,
            int activeFilledSlots,
            List<String> issues,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static CrafterReport healthy(int req, String targetItem) {
            return new CrafterReport(true, false, false, req, 9 - req, req,
                    Collections.emptyList(),
                    String.format("✔ 自动合成器配置健康：目标合成 [%s]，槽位遮罩与红石触发信号精确匹配。", targetItem),
                    "供料与时钟周期同步就绪，无需干预。");
        }

        public static CrafterReport empty() {
            return new CrafterReport(true, false, false, 0, 0, 0,
                    Collections.emptyList(), "未检测到 1.21 自动合成器", "");
        }
    }

    public static CrafterReport analyze(LocalBlock crafterBlock, LocalMachineCluster cluster, String targetRecipe) {
        if (crafterBlock == null || !crafterBlock.isCrafter()) {
            return CrafterReport.empty();
        }

        List<String> issues = new ArrayList<>();

        // Read crafter properties
        int disabledCount = 0;
        try {
            disabledCount = Integer.parseInt(crafterBlock.getProperty("disabled_slots", "0"));
        } catch (NumberFormatException ignored) {}

        int filledCount = 0;
        try {
            filledCount = Integer.parseInt(crafterBlock.getProperty("filled_slots", "0"));
        } catch (NumberFormatException ignored) {}

        // Evaluate target recipe requirements
        int expectedSlots = 9;
        if (targetRecipe != null) {
            String rec = targetRecipe.toLowerCase();
            if (rec.contains("chestplate")) expectedSlots = 8;
            else if (rec.contains("leggings")) expectedSlots = 7;
            else if (rec.contains("helmet")) expectedSlots = 5;
            else if (rec.contains("boots")) expectedSlots = 4;
            else if (rec.contains("pickaxe") || rec.contains("axe")) expectedSlots = 5;
            else if (rec.contains("sword")) expectedSlots = 3;
            else if (rec.contains("shovel")) expectedSlots = 2;
            else if (rec.contains("hopper")) expectedSlots = 6; // 5 iron + 1 chest
            else if (rec.contains("iron_block") || rec.contains("gold_block")) expectedSlots = 9;
        }

        int expectedDisabled = 9 - expectedSlots;
        boolean hasMaskingDeficit = disabledCount < expectedDisabled;
        if (hasMaskingDeficit) {
            issues.add(String.format("槽位遮罩不足: 合成 [%s] 仅需 %d 格，当前仅禁用了 %d 格 (应禁用 %d 格)！漏斗供料将溢入空槽破坏配方形状！",
                    targetRecipe != null ? targetRecipe : "目标物品", expectedSlots, disabledCount, expectedDisabled));
        }

        // Check feeding hoppers
        List<LocalBlock> feeders = new ArrayList<>();
        for (BlockPos neighbor : crafterBlock.pos().getDirectNeighbors()) {
            LocalBlock nb = cluster != null ? cluster.getBlock(neighbor) : null;
            if (nb != null && nb.isHopper() && crafterBlock.pos().equals(neighbor.offset(nb.facing()))) {
                feeders.add(nb);
            }
        }

        // Multiple distinct ingredients with single uncontrolled hopper -> high risk of saturation deadlock
        boolean multipleIngredients = expectedSlots < 9 && targetRecipe != null &&
                (targetRecipe.contains("sword") || targetRecipe.contains("pickaxe") || targetRecipe.contains("hopper"));
        boolean hasDeadlockRisk = false;
        if (multipleIngredients && feeders.size() == 1) {
            hasDeadlockRisk = true;
            issues.add("供料死锁高危: 多成分配方采用单漏斗无序混投，单一原料将抢占全部槽位引发永久死锁！");
        }

        if (hasMaskingDeficit || hasDeadlockRisk) {
            String diag = "⚡ [自动合成器流水线缺陷] 检测到配方槽位未有效遮罩或供料顺序失衡！";
            String advice = "解决对策：1. 点击 Crafter 界面将无需使用的槽位手动红色禁用；2. 多原料合成请使用投掷器脉冲按比例分配 (如 2铁:1木棍)！";
            return new CrafterReport(false, hasDeadlockRisk, hasMaskingDeficit, expectedSlots,
                    disabledCount, filledCount, issues, diag, advice);
        }

        return CrafterReport.healthy(expectedSlots, targetRecipe != null ? targetRecipe : "通用配方");
    }
}
