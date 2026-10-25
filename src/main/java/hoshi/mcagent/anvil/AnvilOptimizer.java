package hoshi.mcagent.anvil;

import java.util.*;

public class AnvilOptimizer {

    public static int calculatePenalty(int workCount) {
        if (workCount <= 0) return 0;
        if (workCount >= 30) return Integer.MAX_VALUE;
        return (1 << workCount) - 1;
    }

    public static class AnvilItem {
        public final String name;
        public final boolean isGear;
        public int workCount;
        public final Map<String, Integer> enchantments; // id -> level

        public AnvilItem(String name, boolean isGear, int workCount, Map<String, Integer> enchants) {
            this.name = name;
            this.isGear = isGear;
            this.workCount = workCount;
            this.enchantments = new LinkedHashMap<>(enchants);
        }

        public int getPenalty() {
            return calculatePenalty(workCount);
        }

        public String getEnchantSummary() {
            if (enchantments.isEmpty()) return "无附魔";
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<String, Integer> e : enchantments.entrySet()) {
                if (sb.length() > 0) sb.append("+");
                EnchantmentEntry entry = EnchantmentEntry.get(e.getKey());
                String name = entry != null ? entry.getNameZh() : e.getKey();
                sb.append(name).append(toRoman(e.getValue()));
            }
            return sb.toString();
        }
    }

    private static String toRoman(int level) {
        switch (level) {
            case 1: return "I";
            case 2: return "II";
            case 3: return "III";
            case 4: return "IV";
            case 5: return "V";
            default: return String.valueOf(level);
        }
    }

    public static AnvilPlan optimize(String gearName, Map<String, Integer> requestedEnchants) {
        List<String> warnings = new ArrayList<>();
        List<AnvilMergeStep> steps = new ArrayList<>();

        if (requestedEnchants == null || requestedEnchants.isEmpty()) {
            return new AnvilPlan(gearName, steps, 0, 0, 0, false, Collections.singletonList("未指定任何附魔"));
        }

        // 1. Conflict & Compatibility checks
        List<String> enchantIds = new ArrayList<>(requestedEnchants.keySet());
        for (int i = 0; i < enchantIds.size(); i++) {
            String idA = enchantIds.get(i);
            EnchantmentEntry entryA = EnchantmentEntry.get(idA);
            if (entryA != null) {
                if (!entryA.isCompatibleWithGear(gearName)) {
                    warnings.add(String.format("附魔 [%s] 通常不能直接赋予装备 [%s]", entryA.getNameZh(), gearName));
                }
                for (int j = i + 1; j < enchantIds.size(); j++) {
                    String idB = enchantIds.get(j);
                    if (entryA.conflictsWith(idB)) {
                        EnchantmentEntry entryB = EnchantmentEntry.get(idB);
                        String nameB = entryB != null ? entryB.getNameZh() : idB;
                        warnings.add(String.format("冲突警报：[%s] 与 [%s] 互斥，铁砧无法共存！", entryA.getNameZh(), nameB));
                    }
                }
            }
        }

        // 2. Create Base Gear item and Individual Book items
        AnvilItem gear = new AnvilItem(gearName, true, 0, Collections.emptyMap());
        List<AnvilItem> books = new ArrayList<>();

        // Sort enchantments by multiplier descending so expensive books get combined at lower tree levels
        List<Map.Entry<String, Integer>> sortedEnchants = new ArrayList<>(requestedEnchants.entrySet());
        sortedEnchants.sort((a, b) -> {
            EnchantmentEntry ea = EnchantmentEntry.get(a.getKey());
            EnchantmentEntry eb = EnchantmentEntry.get(b.getKey());
            int ma = ea != null ? ea.getBookMultiplier() * a.getValue() : a.getValue();
            int mb = eb != null ? eb.getBookMultiplier() * b.getValue() : b.getValue();
            return Integer.compare(mb, ma);
        });

        for (Map.Entry<String, Integer> entry : sortedEnchants) {
            Map<String, Integer> single = new HashMap<>();
            single.put(entry.getKey(), entry.getValue());
            EnchantmentEntry ee = EnchantmentEntry.get(entry.getKey());
            String nameZh = ee != null ? ee.getNameZh() : entry.getKey();
            books.add(new AnvilItem("附魔书(" + nameZh + toRoman(entry.getValue()) + ")", false, 0, single));
        }

        int totalCost = 0;
        int maxStepCost = 0;
        boolean tooExpensive = false;
        int stepIndex = 1;

        // 3. Binary Tree Merging of Books
        Queue<AnvilItem> queue = new ArrayDeque<>(books);
        while (queue.size() > 1) {
            AnvilItem b1 = queue.poll();
            AnvilItem b2 = queue.poll();

            int stepCost = calculateStepCost(b1, b2);
            totalCost += stepCost;
            if (stepCost > maxStepCost) maxStepCost = stepCost;
            if (stepCost >= 40) tooExpensive = true;

            int newWorkCount = Math.max(b1.workCount, b2.workCount) + 1;
            Map<String, Integer> mergedEnchants = new LinkedHashMap<>(b1.enchantments);
            mergedEnchants.putAll(b2.enchantments);

            String resName = "复合书(" + b1.getEnchantSummary() + "+" + b2.getEnchantSummary() + ")";
            steps.add(new AnvilMergeStep(stepIndex++, b1.name, b2.name, resName, stepCost, b1.getPenalty() + b2.getPenalty(), newWorkCount));

            AnvilItem mergedBook = new AnvilItem(resName, false, newWorkCount, mergedEnchants);
            queue.offer(mergedBook);
        }

        // 4. Merge the final composite book onto the Gear
        if (!queue.isEmpty()) {
            AnvilItem finalBook = queue.poll();
            int stepCost = calculateStepCost(gear, finalBook);
            totalCost += stepCost;
            if (stepCost > maxStepCost) maxStepCost = stepCost;
            if (stepCost >= 40) tooExpensive = true;

            int newWorkCount = Math.max(gear.workCount, finalBook.workCount) + 1;
            Map<String, Integer> finalEnchants = new LinkedHashMap<>(gear.enchantments);
            finalEnchants.putAll(finalBook.enchantments);

            String finalGearName = "神装·" + gearName;
            steps.add(new AnvilMergeStep(stepIndex, gear.name, finalBook.name, finalGearName, stepCost, gear.getPenalty() + finalBook.getPenalty(), newWorkCount));
            gear.workCount = newWorkCount;
        }

        return new AnvilPlan(gearName, steps, totalCost, maxStepCost, gear.workCount, tooExpensive, warnings);
    }

    private static int calculateStepCost(AnvilItem target, AnvilItem sacrifice) {
        int penaltyCost = target.getPenalty() + sacrifice.getPenalty();
        int enchantCost = 0;

        for (Map.Entry<String, Integer> e : sacrifice.enchantments.entrySet()) {
            String id = e.getKey();
            int sacLevel = e.getValue();
            EnchantmentEntry entry = EnchantmentEntry.get(id);
            int multiplier = 1;
            if (entry != null) {
                multiplier = sacrifice.isGear ? entry.getItemMultiplier() : entry.getBookMultiplier();
            }

            Integer targetLevel = target.enchantments.get(id);
            if (targetLevel == null) {
                enchantCost += sacLevel * multiplier;
            } else if (targetLevel < sacLevel) {
                enchantCost += sacLevel * multiplier;
            } else if (targetLevel == sacLevel) {
                int maxLvl = entry != null ? entry.getMaxLevel() : 5;
                int resultingLevel = Math.min(sacLevel + 1, maxLvl);
                enchantCost += resultingLevel * multiplier;
            } else {
                enchantCost += 1;
            }
        }

        return penaltyCost + Math.max(1, enchantCost);
    }
}
