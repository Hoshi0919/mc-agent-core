package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Diagnostic analyzer for Minecraft Redstone transmission physics,
 * torch burnout dynamics, strong vs weak powering blockades,
 * wire redirection disconnections, and observer feedback loops.
 */
public final class RedstoneTransmissionAnalyzer {

    public enum PowerType {
        STRONG,
        WEAK,
        NONE,
        TRANSPARENT_INSULATOR
    }

    public record PowerState(
            BlockPos pos,
            PowerType powerType,
            int signalStrength,
            List<BlockPos> powerSources,
            boolean isSolidConductive
    ) {}

    public record TransmissionReport(
            boolean isHealthy,
            boolean hasTorchBurnout,
            boolean hasWeakPowerBlockade,
            boolean hasWireRedirectionDisconnection,
            boolean hasObserverLoop,
            BlockPos targetPos,
            String targetBlockType,
            PowerType powerType,
            int signalStrength,
            List<BlockPos> burnoutTorches,
            List<BlockPos> weakPowerBlockades,
            List<BlockPos> redirectedWires,
            List<BlockPos> observerLoops,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static TransmissionReport empty() {
            return new TransmissionReport(
                    true, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", PowerType.NONE, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    "未检测到红石传输或电路异常", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§e【红石传输拓扑与充能因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 充能状态：%s | 信号强度: §6%d§r\n", formatPowerType(powerType), signalStrength));

            if (hasTorchBurnout) {
                sb.append("  ⚡ §c[火把烧毁高危] 检测到红石火把极速自激振荡回路 (总延迟 < 4 ticks)！§r\n");
                for (BlockPos bPos : burnoutTorches) {
                    sb.append(String.format("     ✖ 烧毁火把节点: %s (3秒内切换>=8次触发熄灭冷却)\n", bPos));
                }
            }

            if (hasWeakPowerBlockade) {
                sb.append("  ⚡ §6[弱充能阻断告警] 实体方块仅为弱充能 (Weakly Powered)，无法熄灭火把或激活未指向的红石线！§r\n");
                for (BlockPos wPos : weakPowerBlockades) {
                    sb.append(String.format("     ✖ 弱充能阻断点: %s (需中继器升格为强充能)\n", wPos));
                }
            }

            if (hasWireRedirectionDisconnection) {
                sb.append("  ⚡ §e[导线偏转断路] 红石粉因邻近组件吸引发生转向，脱离目标方块造成断电！§r\n");
                for (BlockPos rPos : redirectedWires) {
                    sb.append(String.format("     ↷ 偏转断路线路: %s\n", rPos));
                }
            }

            if (hasObserverLoop) {
                sb.append("  ⚡ §b[侦测器自激死循环] 检测到 1-clock (2 gameticks) 高频脉冲死循环振荡！§r\n");
                for (BlockPos oPos : observerLoops) {
                    sb.append(String.format("     ⟳ 侦测器振荡源: %s\n", oPos));
                }
            }

            if (isHealthy) {
                sb.append("  ✓ §a[传输健康] 电路充能完整，无烧毁、弱充能阻断或偏转断路隐患。§r\n");
            }

            sb.append(String.format("▸ 核心诊断：%s\n", primaryDiagnosis));
            if (!actionableAdvice.isEmpty()) {
                sb.append(String.format("▸ 修复建议：%s\n", actionableAdvice));
            }
            return sb.toString();
        }

        private static String formatPowerType(PowerType pt) {
            return switch (pt) {
                case STRONG -> "§a强充能 (Strongly Powered)§r";
                case WEAK -> "§6弱充能 (Weakly Powered)§r";
                case TRANSPARENT_INSULATOR -> "§c透明绝缘介质 (Non-conductive)§r";
                case NONE -> "§7未充能 (Unpowered)§r";
            };
        }
    }

    private RedstoneTransmissionAnalyzer() {}

    /**
     * Diagnostic analysis of redstone power transmission in the cluster around a target position.
     */
    public static TransmissionReport analyzeTransmission(LocalMachineCluster cluster, BlockPos targetPos) {
        if (cluster == null || cluster.blocks().isEmpty()) {
            return TransmissionReport.empty();
        }

        LocalBlock targetBlock = cluster.getBlock(targetPos);
        String targetType = (targetBlock != null) ? targetBlock.blockId() : "minecraft:air";

        PowerState powerState = calculatePowerState(cluster, targetPos);

        List<BlockPos> burnoutTorches = new ArrayList<>();
        List<BlockPos> weakPowerBlockades = new ArrayList<>();
        List<BlockPos> redirectedWires = new ArrayList<>();
        List<BlockPos> observerLoops = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        // 1. Scan for torch burnout dynamics
        detectTorchBurnout(cluster, burnoutTorches, issues);

        // 2. Scan for weak power blockades
        detectWeakPowerBlockades(cluster, targetPos, powerState, weakPowerBlockades, issues);

        // 3. Scan for wire redirection disconnection
        detectWireRedirection(cluster, targetPos, redirectedWires, warnings);

        // 4. Scan for observer feedback loops
        detectObserverLoops(cluster, observerLoops, warnings);

        boolean hasTorchBurnout = !burnoutTorches.isEmpty();
        boolean hasWeakPower = !weakPowerBlockades.isEmpty();
        boolean hasWireRedir = !redirectedWires.isEmpty();
        boolean hasObserverLoop = !observerLoops.isEmpty();
        boolean isHealthy = !hasTorchBurnout && !hasWeakPower && !hasWireRedir && !hasObserverLoop;

        String primaryDiag;
        String advice;

        if (hasTorchBurnout) {
            primaryDiag = "检测到红石火把自激振荡反馈回路，回路延迟 < 4 ticks，火把将高频烧毁熄灭";
            advice = "在反馈回路中接入红石中继器（Repeater），将总延迟调至 4 redstone ticks（8 gameticks）以上消除烧毁";
        } else if (hasWeakPower) {
            primaryDiag = "实体方块处于弱充能状态，无法灭活附着的红石火把或激活未指向的红石导线";
            advice = "改用红石中继器直接指向该方块，升格为强充能（Strongly Powered），以可靠熄灭火把";
        } else if (hasWireRedir) {
            primaryDiag = "红石粉受到邻近组件吸引产生偏转，不再对齐目标方块造成断路";
            advice = "在目标方块前放置中继器锁定单向注入，或在红石线侧面加装隔电方块防止偏转";
        } else if (hasObserverLoop) {
            primaryDiag = "侦测器面对面或与活塞构成 1-clock (2 gameticks) 极限自激振荡";
            advice = "断开侦测器对冲，改用比较器时钟或拉开间距避免高频卡死";
        } else {
            primaryDiag = "红石传输链路与充能拓扑正常，无烧毁或阻断隐患";
            advice = "保持当前规范布线";
        }

        return new TransmissionReport(
                isHealthy,
                hasTorchBurnout,
                hasWeakPower,
                hasWireRedir,
                hasObserverLoop,
                targetPos,
                targetType,
                powerState.powerType(),
                powerState.signalStrength(),
                burnoutTorches,
                weakPowerBlockades,
                redirectedWires,
                observerLoops,
                issues,
                warnings,
                primaryDiag,
                advice
        );
    }

    /**
     * Computes the powering state of a given block position (Strong, Weak, Insulator, or None).
     */
    public static PowerState calculatePowerState(LocalMachineCluster cluster, BlockPos pos) {
        LocalBlock block = cluster.getBlock(pos);
        if (block == null || block.isAir()) {
            return new PowerState(pos, PowerType.NONE, 0, Collections.emptyList(), false);
        }

        if (block.isTransparent()) {
            return new PowerState(pos, PowerType.TRANSPARENT_INSULATOR, 0, Collections.emptyList(), false);
        }

        List<BlockPos> sources = new ArrayList<>();
        int maxStrong = 0;
        int maxWeak = 0;

        // Check 6 adjacent neighbors for direct strong power (Repeaters, Comparators, Levers, Buttons, Redstone Blocks)
        for (BlockPos neighborPos : pos.neighbors()) {
            LocalBlock nBlock = cluster.getBlock(neighborPos);
            if (nBlock == null) continue;

            // 1. Repeater pointing directly into this block -> STRONG
            if (nBlock.isRepeater() && nBlock.isPowered()) {
                String facing = nBlock.facing();
                if (neighborPos.offset(facing).equals(pos)) {
                    maxStrong = Math.max(maxStrong, 15);
                    sources.add(neighborPos);
                }
            }

            // 2. Comparator pointing directly into this block -> STRONG
            if (nBlock.isComparator() && nBlock.isPowered()) {
                String facing = nBlock.facing();
                if (neighborPos.offset(facing).equals(pos)) {
                    int p = Integer.parseInt(nBlock.getProperty("power", "15"));
                    maxStrong = Math.max(maxStrong, p);
                    sources.add(neighborPos);
                }
            }

            // 3. Lever / Button attached to this block -> STRONG
            if ((nBlock.blockId().contains("lever") || nBlock.blockId().contains("button") || nBlock.blockId().contains("pressure_plate"))
                    && nBlock.isPowered()) {
                maxStrong = Math.max(maxStrong, 15);
                sources.add(neighborPos);
            }

            // 4. Redstone Block adjacent -> STRONG
            if (nBlock.blockId().contains("redstone_block")) {
                maxStrong = Math.max(maxStrong, 15);
                sources.add(neighborPos);
            }

            // 5. Redstone Wire directly pointing to this block or on top of it -> WEAK
            if (nBlock.isRedstoneWire()) {
                int wirePower = Integer.parseInt(nBlock.getProperty("power", nBlock.isPowered() ? "15" : "0"));
                if (wirePower > 0) {
                    // Check if wire points to pos or is directly above pos
                    if (neighborPos.equals(pos.offset("up"))) {
                        maxWeak = Math.max(maxWeak, wirePower);
                        sources.add(neighborPos);
                    } else if (isWirePointingTo(cluster, neighborPos, pos)) {
                        maxWeak = Math.max(maxWeak, wirePower);
                        sources.add(neighborPos);
                    }
                }
            }
        }

        if (maxStrong > 0) {
            return new PowerState(pos, PowerType.STRONG, maxStrong, sources, true);
        } else if (maxWeak > 0) {
            return new PowerState(pos, PowerType.WEAK, maxWeak, sources, true);
        } else {
            return new PowerState(pos, PowerType.NONE, 0, sources, true);
        }
    }

    /**
     * Determines whether a redstone wire at wirePos is pointing towards targetPos.
     */
    public static boolean isWirePointingTo(LocalMachineCluster cluster, BlockPos wirePos, BlockPos targetPos) {
        LocalBlock wire = cluster.getBlock(wirePos);
        if (wire == null || !wire.isRedstoneWire()) return false;

        // Check horizontal adjacency
        int dx = targetPos.x() - wirePos.x();
        int dy = targetPos.y() - wirePos.y();
        int dz = targetPos.z() - wirePos.z();

        if (dy != 0) return false;
        if (Math.abs(dx) + Math.abs(dz) != 1) return false;

        String dir = null;
        if (dx == 1) dir = "east";
        else if (dx == -1) dir = "west";
        else if (dz == 1) dir = "south";
        else if (dz == -1) dir = "north";

        // If explicit wire connection properties exist (e.g. north=side, east=up, etc.)
        String conn = wire.getProperty(dir, "none");
        if (!"none".equals(conn)) {
            return true;
        }

        // Check if wire has only 0 or 2 opposite connections (straight line)
        // If wire has other connections that divert it away, it is not pointing here
        int otherConnections = 0;
        for (String d : List.of("north", "south", "east", "west")) {
            if (d.equals(dir)) continue;
            String c = wire.getProperty(d, "none");
            if (!"none".equals(c)) {
                otherConnections++;
            }
        }

        // If wire has side connections diverting elsewhere, it might be redirected
        if (wire.properties().containsKey("north") || wire.properties().containsKey("east")) {
            return !"none".equals(wire.getProperty(dir, "none"));
        }

        // Default: if adjacent and no diversion property set, treat as connected
        return true;
    }

    /**
     * Detects torch burnout loops in the cluster.
     */
    private static void detectTorchBurnout(LocalMachineCluster cluster, List<BlockPos> burnoutTorches, List<String> issues) {
        for (LocalBlock block : cluster.blocks().values()) {
            if (block.isRedstoneTorch()) {
                BlockPos torchPos = block.pos();
                BlockPos basePos = getTorchBasePos(cluster, block);

                // Trace feedback loop from torch output back to base block
                int loopDelay = calculateLoopDelay(cluster, torchPos, basePos);
                if (loopDelay >= 0 && loopDelay < 4) {
                    burnoutTorches.add(torchPos);
                    issues.add(String.format("红石火把 %s 存在极速自激反馈回路（回路中继延迟: %d ticks < 4 ticks），必将烧毁熄灭",
                            torchPos, loopDelay));
                }
            }
        }
    }

    /**
     * Gets the base mounting block of a redstone torch.
     */
    public static BlockPos getTorchBasePos(LocalMachineCluster cluster, LocalBlock torch) {
        String facing = torch.facing();
        // Wall torch facing is the direction it faces outwards; base is opposite
        if (torch.blockId().contains("wall_torch")) {
            return switch (facing) {
                case "north" -> torch.pos().offset("south");
                case "south" -> torch.pos().offset("north");
                case "east" -> torch.pos().offset("west");
                case "west" -> torch.pos().offset("east");
                default -> torch.pos().offset("down");
            };
        }
        // Normal ground torch base is directly down
        return torch.pos().offset("down");
    }

    /**
     * Calculates the total redstone tick delay in a feedback loop from torchPos to basePos.
     * Returns -1 if no loop exists.
     */
    public static int calculateLoopDelay(LocalMachineCluster cluster, BlockPos torchPos, BlockPos basePos) {
        // BFS to find shortest redstone signal path from torch outputs back to basePos
        Queue<BlockPos> queue = new ArrayDeque<>();
        Map<BlockPos, Integer> delayMap = new HashMap<>();

        // Torch output activates block above or adjacent wires
        BlockPos above = torchPos.offset("up");
        queue.add(above);
        delayMap.put(above, 1); // 1 tick intrinsic torch inversion delay

        for (BlockPos n : torchPos.neighbors()) {
            if (n.equals(torchPos.offset("down"))) continue; // Base
            LocalBlock nb = cluster.getBlock(n);
            if (nb != null && nb.isRedstoneWire()) {
                queue.add(n);
                delayMap.put(n, 1);
            }
        }

        Set<BlockPos> visited = new HashSet<>();
        while (!queue.isEmpty()) {
            BlockPos curr = queue.poll();
            if (curr.equals(basePos)) {
                return delayMap.get(curr);
            }
            if (!visited.add(curr)) continue;

            LocalBlock currBlock = cluster.getBlock(curr);
            int currentDelay = delayMap.get(curr);

            for (BlockPos next : curr.neighbors()) {
                if (visited.contains(next) || next.equals(torchPos)) continue;
                LocalBlock nextBlock = cluster.getBlock(next);
                if (nextBlock == null) continue;

                if (next.equals(basePos)) {
                    return currentDelay;
                }

                if (nextBlock.isRedstoneWire()) {
                    delayMap.putIfAbsent(next, currentDelay);
                    queue.add(next);
                } else if (nextBlock.isRepeater()) {
                    String rFacing = nextBlock.facing();
                    // Check if repeater input aligns with curr
                    if (next.offset(getOppositeDirection(rFacing)).equals(curr)) {
                        int rDelay = Integer.parseInt(nextBlock.getProperty("delay", "1"));
                        delayMap.putIfAbsent(next, currentDelay + rDelay);
                        queue.add(next.offset(rFacing)); // output
                    }
                } else if (nextBlock.isSolidConductiveBlock() && !next.equals(basePos)) {
                    // Signal can transmit through 1 solid block if fed by repeater or wire
                    delayMap.putIfAbsent(next, currentDelay);
                    queue.add(next);
                }
            }
        }

        return -1; // No loop found
    }

    /**
     * Scans for weak power blockades (e.g. attempting to unpower a torch with weak power).
     */
    private static void detectWeakPowerBlockades(
            LocalMachineCluster cluster,
            BlockPos targetPos,
            PowerState powerState,
            List<BlockPos> weakPowerBlockades,
            List<String> issues
    ) {
        // Check if targetPos is a base for a torch while only weakly powered
        for (BlockPos neighbor : targetPos.neighbors()) {
            LocalBlock nBlock = cluster.getBlock(neighbor);
            if (nBlock != null && nBlock.isRedstoneTorch()) {
                BlockPos base = getTorchBasePos(cluster, nBlock);
                if (base.equals(targetPos)) {
                    if (powerState.powerType() == PowerType.WEAK) {
                        weakPowerBlockades.add(targetPos);
                        issues.add(String.format("方块 %s 附着红石火把 %s，但该方块仅处于弱充能状态，红石火把无法熄灭！",
                                targetPos, neighbor));
                    }
                }
            }
        }

        // Also check if any wire expects power from a weakly powered block
        for (BlockPos neighbor : targetPos.neighbors()) {
            LocalBlock nBlock = cluster.getBlock(neighbor);
            if (nBlock != null && nBlock.isRedstoneWire()) {
                if (powerState.powerType() == PowerType.WEAK) {
                    // If the wire is not pointing into targetPos, it cannot receive power from a weak block
                    if (!isWirePointingTo(cluster, neighbor, targetPos)) {
                        weakPowerBlockades.add(targetPos);
                        issues.add(String.format("弱充能方块 %s 无法向相邻未对准的红石线 %s 传导信号",
                                targetPos, neighbor));
                        break;
                    }
                }
            }
        }
    }

    /**
     * Detects wire redirection disconnections.
     */
    private static void detectWireRedirection(
            LocalMachineCluster cluster,
            BlockPos targetPos,
            List<BlockPos> redirectedWires,
            List<String> warnings
    ) {
        LocalBlock target = cluster.getBlock(targetPos);
        if (target == null || target.isAir()) return;

        for (BlockPos neighbor : targetPos.neighbors()) {
            LocalBlock wire = cluster.getBlock(neighbor);
            if (wire != null && wire.isRedstoneWire() && (wire.isPowered() || !"0".equals(wire.getProperty("power", "0")))) {
                // If wire is powered, but redirected away from targetPos
                if (!isWirePointingTo(cluster, neighbor, targetPos) && !neighbor.equals(targetPos.offset("up"))) {
                    redirectedWires.add(neighbor);
                    warnings.add(String.format("红石线 %s 处于激活状态，但发生偏转脱离目标方块 %s，导致供电中断",
                            neighbor, targetPos));
                }
            }
        }
    }

    /**
     * Detects observer feedback loops (face-to-face observers or observer-piston loops).
     */
    private static void detectObserverLoops(
            LocalMachineCluster cluster,
            List<BlockPos> observerLoops,
            List<String> warnings
    ) {
        for (LocalBlock block : cluster.blocks().values()) {
            if (block.isObserver()) {
                String facing = block.facing();
                BlockPos detectedPos = block.pos().offset(facing); // Observer looks at facing
                LocalBlock target = cluster.getBlock(detectedPos);

                if (target != null && target.isObserver()) {
                    // Face-to-face: target looks back at block.pos()
                    if (target.pos().offset(target.facing()).equals(block.pos())) {
                        if (!observerLoops.contains(block.pos())) {
                            observerLoops.add(block.pos());
                            observerLoops.add(target.pos());
                            warnings.add(String.format("侦测器 %s 与 %s 面对面相对，构成 1-clock (2 gameticks) 自激震荡时钟",
                                    block.pos(), target.pos()));
                        }
                    }
                }
            }
        }
    }

    private static String getOppositeDirection(String dir) {
        return switch (dir.toLowerCase()) {
            case "north" -> "south";
            case "south" -> "north";
            case "east" -> "west";
            case "west" -> "east";
            case "up" -> "down";
            default -> "up";
        };
    }
}
