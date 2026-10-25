package hoshi.mcagent.anvil;

public class AnvilMergeStep {
    private final int stepNumber;
    private final String leftItem;
    private final String rightItem;
    private final String resultItem;
    private final int costLevels;
    private final int priorPenalty;
    private final int resultWorkCount;

    public AnvilMergeStep(int stepNumber, String leftItem, String rightItem, String resultItem, int costLevels, int priorPenalty, int resultWorkCount) {
        this.stepNumber = stepNumber;
        this.leftItem = leftItem;
        this.rightItem = rightItem;
        this.resultItem = resultItem;
        this.costLevels = costLevels;
        this.priorPenalty = priorPenalty;
        this.resultWorkCount = resultWorkCount;
    }

    public int getStepNumber() { return stepNumber; }
    public String getLeftItem() { return leftItem; }
    public String getRightItem() { return rightItem; }
    public String getResultItem() { return resultItem; }
    public int getCostLevels() { return costLevels; }
    public int getPriorPenalty() { return priorPenalty; }
    public int getResultWorkCount() { return resultWorkCount; }

    @Override
    public String toString() {
        return String.format("步骤 %d: [%s] + [%s] ➔ [%s] (消耗: %d级, 惩罚: %d, 累计次数: %d)",
                stepNumber, leftItem, rightItem, resultItem, costLevels, priorPenalty, resultWorkCount);
    }
}
