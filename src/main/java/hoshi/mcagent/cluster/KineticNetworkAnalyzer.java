package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Topological analyzer for Create mod kinetic networks.
 * Detects kinetic jamming, opposing rotation collisions, and ratio mismatch locks in 0ms.
 */
public final class KineticNetworkAnalyzer {

    public record KineticReport(
            boolean isHealthy,
            boolean isJammed,
            int totalComponents,
            List<String> conflicts,
            String primaryDiagnosis,
            String actionableRemediation
    ) {
        public static KineticReport healthy(int count, String desc) {
            return new KineticReport(true, false, count, Collections.emptyList(), desc, "动力网络拓扑健康，传动顺畅无冲突。");
        }

        public static KineticReport empty() {
            return new KineticReport(true, false, 0, Collections.emptyList(), "未检测到机械动力组件", "");
        }
    }

    private record NodeState(double speedRatio, int sign, BlockPos source) {}

    public static KineticReport analyze(LocalMachineCluster cluster) {
        if (cluster == null || cluster.isEmpty()) {
            return KineticReport.empty();
        }

        List<LocalBlock> kinetics = cluster.getConnectedKinetics();
        if (kinetics.isEmpty()) {
            return KineticReport.empty();
        }

        // Map pos to block
        Map<BlockPos, LocalBlock> kMap = new HashMap<>();
        for (LocalBlock b : kinetics) {
            kMap.put(b.pos(), b);
        }

        // BFS / DFS propagation of rotation state
        Map<BlockPos, NodeState> stateMap = new HashMap<>();
        List<String> conflicts = new ArrayList<>();

        for (LocalBlock start : kinetics) {
            if (stateMap.containsKey(start.pos())) {
                continue;
            }

            // Start a new connected component with base speed 1.0, sign +1
            Queue<BlockPos> queue = new ArrayDeque<>();
            queue.add(start.pos());
            stateMap.put(start.pos(), new NodeState(1.0, 1, start.pos()));

            while (!queue.isEmpty()) {
                BlockPos currentPos = queue.poll();
                LocalBlock currentBlock = kMap.get(currentPos);
                NodeState currentState = stateMap.get(currentPos);

                for (BlockPos neighborPos : currentPos.getDirectNeighbors()) {
                    LocalBlock neighbor = kMap.get(neighborPos);
                    if (neighbor == null) continue;

                    // Evaluate kinetic connection
                    Transmission transmission = evaluateTransmission(currentBlock, neighbor);
                    if (!transmission.isConnected) continue;

                    double expectedSpeed = currentState.speedRatio * transmission.speedMultiplier;
                    int expectedSign = currentState.sign * transmission.signFlip;

                    if (!stateMap.containsKey(neighborPos)) {
                        stateMap.put(neighborPos, new NodeState(expectedSpeed, expectedSign, currentPos));
                        queue.add(neighborPos);
                    } else {
                        // Check for conflict!
                        NodeState existing = stateMap.get(neighborPos);
                        boolean signConflict = existing.sign != expectedSign;
                        boolean speedConflict = Math.abs(existing.speedRatio - expectedSpeed) > 1e-4;

                        if (signConflict || speedConflict) {
                            String conflictDesc = String.format("动力冲突: %s 与 %s 啮合矛盾 (方向冲突=%b, 转速比矛盾: 现有=%.2fx, 传入=%.2fx)",
                                    currentBlock.blockId() + " " + currentPos,
                                    neighbor.blockId() + " " + neighborPos,
                                    signConflict, existing.speedRatio, expectedSpeed);
                            if (!conflicts.contains(conflictDesc)) {
                                conflicts.add(conflictDesc);
                            }
                        }
                    }
                }
            }
        }

        if (!conflicts.isEmpty()) {
            String primary = String.format("⚡ [动力网卡死 JAMMED] 检测到 %d 处机械传动冲突导致整线锁死！", conflicts.size());
            String remediation = "排查建议：相邻齿轮之间形成了奇数环路或反向啮合回环。请拆除冲突处的任一从动齿轮，或接入换向齿轮箱 (Gearbox) 进行相位配平！";
            return new KineticReport(false, true, kinetics.size(), conflicts, primary, remediation);
        }

        return KineticReport.healthy(kinetics.size(), String.format("✔ 动力网络包含 %d 个机械动力组件，全部转速比与啮合方向完全匹配自洽。", kinetics.size()));
    }

    private record Transmission(boolean isConnected, double speedMultiplier, int signFlip) {}

    private static Transmission evaluateTransmission(LocalBlock a, LocalBlock b) {
        String axisA = a.axis();
        String axisB = b.axis();
        int dx = b.pos().x() - a.pos().x();
        int dy = b.pos().y() - a.pos().y();
        int dz = b.pos().z() - a.pos().z();

        // 1. Axial shaft connection (same axis, separated along that axis)
        boolean isCollinear = false;
        if ("x".equals(axisA) && "x".equals(axisB) && dy == 0 && dz == 0 && Math.abs(dx) == 1) isCollinear = true;
        if ("y".equals(axisA) && "y".equals(axisB) && dx == 0 && dz == 0 && Math.abs(dy) == 1) isCollinear = true;
        if ("z".equals(axisA) && "z".equals(axisB) && dx == 0 && dy == 0 && Math.abs(dz) == 1) isCollinear = true;

        if (isCollinear) {
            // Shafts and gears aligned on same axis rotate at identical speed and direction
            return new Transmission(true, 1.0, 1);
        }

        // 2. Spur Gear Mesh (same parallel axis, touching along perpendicular plane)
        boolean parallelAxis = axisA.equals(axisB);
        boolean perpendicularTouch = false;
        if ("y".equals(axisA) && dy == 0 && (Math.abs(dx) + Math.abs(dz) == 1)) perpendicularTouch = true;
        if ("x".equals(axisA) && dx == 0 && (Math.abs(dy) + Math.abs(dz) == 1)) perpendicularTouch = true;
        if ("z".equals(axisA) && dz == 0 && (Math.abs(dx) + Math.abs(dy) == 1)) perpendicularTouch = true;

        if (parallelAxis && perpendicularTouch) {
            boolean aSmall = a.isCogwheel();
            boolean bSmall = b.isCogwheel();
            boolean aLarge = a.isLargeCogwheel();
            boolean bLarge = b.isLargeCogwheel();

            // Small to small
            if (aSmall && bSmall) {
                return new Transmission(true, 1.0, -1); // 1:1, inverted direction
            }
            // Large to large
            if (aLarge && bLarge) {
                return new Transmission(true, 1.0, -1); // 1:1, inverted direction
            }
            // Small to large (large spins half as fast)
            if (aSmall && bLarge) {
                return new Transmission(true, 0.5, -1);
            }
            // Large to small (small spins twice as fast)
            if (aLarge && bSmall) {
                return new Transmission(true, 2.0, -1);
            }
        }

        return new Transmission(false, 1.0, 1);
    }
}
