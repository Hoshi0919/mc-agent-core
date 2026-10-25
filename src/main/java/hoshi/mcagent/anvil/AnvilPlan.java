package hoshi.mcagent.anvil;

import java.util.Collections;
import java.util.List;

public class AnvilPlan {
    private final String gearName;
    private final List<AnvilMergeStep> steps;
    private final int totalCostLevels;
    private final int maxStepCost;
    private final int finalWorkCount;
    private final boolean tooExpensive;
    private final List<String> warnings;

    public AnvilPlan(String gearName, List<AnvilMergeStep> steps, int totalCostLevels, int maxStepCost, int finalWorkCount, boolean tooExpensive, List<String> warnings) {
        this.gearName = gearName;
        this.steps = steps != null ? steps : Collections.emptyList();
        this.totalCostLevels = totalCostLevels;
        this.maxStepCost = maxStepCost;
        this.finalWorkCount = finalWorkCount;
        this.tooExpensive = tooExpensive;
        this.warnings = warnings != null ? warnings : Collections.emptyList();
    }

    public String getGearName() { return gearName; }
    public List<AnvilMergeStep> getSteps() { return steps; }
    public int getTotalCostLevels() { return totalCostLevels; }
    public int getMaxStepCost() { return maxStepCost; }
    public int getFinalWorkCount() { return finalWorkCount; }
    public boolean isTooExpensive() { return tooExpensive; }
    public List<String> getWarnings() { return warnings; }

    public String formatReport() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("§6【铁砧附魔合并优化方案：%s】§r\n", gearName));
        if (tooExpensive) {
            sb.append("§c⚠️ 警告：检测到存在单步消耗 >= 40 级，生存模式将提示【过于昂贵！】无法锻造！§r\n");
        } else {
            sb.append("§a✔ 状态：二叉树优化已就绪，所有单步均低于 39 级生存上限！§r\n");
        }
        sb.append(String.format("§7- 合并总步数: %d 步 | 总等级消耗: %d 级 | 单步最高: %d 级 | 最终装备惩罚次数: %d (惩罚: %d 级)§r\n",
                steps.size(), totalCostLevels, maxStepCost, finalWorkCount, (1 << finalWorkCount) - 1));

        if (!warnings.isEmpty()) {
            for (String w : warnings) {
                sb.append(String.format("§e- 附魔提示: %s§r\n", w));
            }
        }

        sb.append("§b锻造执行工序：§r\n");
        for (AnvilMergeStep step : steps) {
            sb.append(String.format("  §e%d.§r 左槽 §f%s§r + 右槽 §f%s§r ➔ §a%s§r §7(消耗: %d 级)§r\n",
                    step.getStepNumber(), step.getLeftItem(), step.getRightItem(), step.getResultItem(), step.getCostLevels()));
        }
        return sb.toString();
    }
}
