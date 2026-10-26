package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Diagnostic analyzer for hopper logistics pipelines, circular deadlocks, backpressure, and item sorter bleed.
 */
public final class HopperNetworkAnalyzer {

    public record HopperReport(
            boolean isHealthy,
            boolean hasDeadlock,
            boolean hasBackpressure,
            boolean hasBleedRisk,
            int totalHoppers,
            List<String> deadlocks,
            List<String> stalledHoppers,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static HopperReport healthy(int count, String desc) {
            return new HopperReport(true, false, false, false, count,
                    Collections.emptyList(), Collections.emptyList(), Collections.emptyList(),
                    desc, "漏斗流水线拓扑健康，物流顺畅无死锁。");
        }

        public static HopperReport empty() {
            return new HopperReport(true, false, false, false, 0,
                    Collections.emptyList(), Collections.emptyList(), Collections.emptyList(),
                    "未检测到漏斗物流组件", "");
        }
    }

    public static HopperReport analyze(LocalMachineCluster cluster) {
        if (cluster == null || cluster.isEmpty()) {
            return HopperNetworkReportEmpty();
        }

        List<LocalBlock> hoppers = cluster.getConnectedHoppers();
        if (hoppers.isEmpty()) {
            return HopperNetworkReportEmpty();
        }

        Map<BlockPos, LocalBlock> hMap = new HashMap<>();
        Map<BlockPos, BlockPos> forwardEdges = new HashMap<>();
        List<String> stalled = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        for (LocalBlock h : hoppers) {
            hMap.put(h.pos(), h);
            String facing = h.facing();
            BlockPos targetPos = h.pos().offset(facing);
            forwardEdges.put(h.pos(), targetPos);

            // Check if locked by redstone
            if (!h.isEnabled() || h.isPowered()) {
                stalled.add(String.format("漏斗 %s 被红石锁定 (locked=true)", h.pos()));
            }

            // Check target block
            LocalBlock targetBlock = cluster.getBlock(targetPos);
            if (targetBlock != null) {
                if ("true".equalsIgnoreCase(targetBlock.getProperty("full", "false"))) {
                    stalled.add(String.format("漏斗 %s 下游容器 %s 已满引发背压堵塞", h.pos(), targetBlock.pos()));
                }
            }
        }

        // Detect Directed Cycles (Circular Deadlocks) via DFS
        List<String> deadlocks = new ArrayList<>();
        Set<BlockPos> visited = new HashSet<>();
        Set<BlockPos> recStack = new HashSet<>();

        for (BlockPos start : hMap.keySet()) {
            if (!visited.contains(start)) {
                findCycles(start, forwardEdges, hMap, visited, recStack, new ArrayList<>(), deadlocks);
            }
        }

        // Sorter Signal Bleed Check: look for comparators reading hoppers
        List<LocalBlock> comparators = cluster.getBlocksByType("comparator");
        boolean hasBleedRisk = false;
        for (LocalBlock comp : comparators) {
            String compFacing = comp.facing();
            // Comparator reads block directly behind it
            BlockPos sourcePos = comp.pos().offset(getOppositeFacing(compFacing));
            LocalBlock sourceBlock = cluster.getBlock(sourcePos);
            if (sourceBlock != null && sourceBlock.isHopper()) {
                String itemCountStr = sourceBlock.getProperty("item_count", "0");
                try {
                    int count = Integer.parseInt(itemCountStr);
                    // Standard hopper has 5 slots (320 items max).
                    // Signal = floor(1 + (count / 320.0) * 14)
                    // If count >= 46, signal level becomes >= 3, which leaks into adjacent 1-wide tile slices!
                    if (count >= 46) {
                        hasBleedRisk = true;
                        warnings.add(String.format("分类器串线警报: 漏斗 %s 容纳 %d 物品导致比较器输出 ≥3 级信号，将击穿相邻切片红石线！",
                                sourcePos, count));
                    }
                } catch (NumberFormatException ignored) {}
            }
        }

        boolean hasDeadlock = !deadlocks.isEmpty();
        boolean hasBackpressure = !stalled.isEmpty();
        boolean isHealthy = !hasDeadlock && !hasBackpressure && !hasBleedRisk;

        if (hasDeadlock) {
            String diag = String.format("⚡ [漏斗死锁 DEADLOCK] 检测到 %d 处闭环死循环回路！物料卡在环中无法送达终端。", deadlocks.size());
            String advice = "解决建议：断开死循环回路。将闭环中的某个漏斗朝向重定向至主存储箱或下行干线！";
            return new HopperReport(false, true, hasBackpressure, hasBleedRisk, hoppers.size(),
                    deadlocks, stalled, warnings, diag, advice);
        }

        if (hasBleedRisk) {
            String diag = "⚡ [分类器串线击穿风险] 过滤漏斗物品积压超标，相邻物品分类切片有被误锁或抽空的风险！";
            String advice = "解决建议：恢复标准 41+1+1+1+1 (防串线) 或 18+1+1+1+1 布局，确保信号等级严格维持在 1~2 级！";
            return new HopperReport(false, false, hasBackpressure, true, hoppers.size(),
                    deadlocks, stalled, warnings, diag, advice);
        }

        if (hasBackpressure) {
            String diag = String.format("⚠ [背压停滞 BACKPRESSURE] 检测到 %d 处堵塞停顿点！", stalled.size());
            String advice = "排查建议：检查下游容器是否堆满，或解除上游红石意外充能锁定。";
            return new HopperReport(false, false, true, false, hoppers.size(),
                    deadlocks, stalled, warnings, diag, advice);
        }

        return HopperReport.healthy(hoppers.size(), String.format("✔ 漏斗网络包含 %d 个漏斗，流向拓扑无死锁、无背压积压、无串线风险。", hoppers.size()));
    }

    private static HopperReport HopperNetworkReportEmpty() {
        return HopperReport.empty();
    }

    private static void findCycles(
            BlockPos current,
            Map<BlockPos, BlockPos> edges,
            Map<BlockPos, LocalBlock> hMap,
            Set<BlockPos> visited,
            Set<BlockPos> recStack,
            List<BlockPos> currentPath,
            List<String> deadlocks
    ) {
        visited.add(current);
        recStack.add(current);
        currentPath.add(current);

        BlockPos next = edges.get(current);
        if (next != null && hMap.containsKey(next)) {
            if (!visited.contains(next)) {
                findCycles(next, edges, hMap, visited, recStack, currentPath, deadlocks);
            } else if (recStack.contains(next)) {
                // Cycle detected!
                int idx = currentPath.indexOf(next);
                if (idx >= 0) {
                    StringBuilder sb = new StringBuilder("死锁闭环: ");
                    for (int i = idx; i < currentPath.size(); i++) {
                        sb.append(currentPath.get(i)).append(" -> ");
                    }
                    sb.append(next);
                    deadlocks.add(sb.toString());
                }
            }
        }

        recStack.remove(current);
        currentPath.remove(currentPath.size() - 1);
    }

    private static String getOppositeFacing(String facing) {
        return switch (facing.toLowerCase()) {
            case "north" -> "south";
            case "south" -> "north";
            case "west" -> "east";
            case "east" -> "west";
            case "up" -> "down";
            default -> "up";
        };
    }
}
