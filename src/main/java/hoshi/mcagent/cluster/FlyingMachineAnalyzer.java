package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Diagnostic analyzer for Minecraft Flying Machines & Slimestone Automata (v2.10.0):
 * - Piston 12-block push limit & recursive adhesion cluster search
 * - Slime vs Honey segregation, dual-engine non-adhesion & accidental bridging jams
 * - Glazed terracotta non-sticky guiding rails vs accidental terrain adhesion
 * - Immovable stopper blocks (Obsidian) at docking stations
 * - Observer polarity, cycle synchronization & dead-stroke stalling
 */
public final class FlyingMachineAnalyzer {

    public enum EngineType {
        TWO_WAY_REVERSIBLE_ENGINE,
        ONE_WAY_ENGINE,
        MULTI_SEGMENT_HARVESTER,
        DOCKING_STATION,
        NONE
    }

    public record FlyingReport(
            boolean isHealthy,
            boolean hasPushLimitExceeded,
            boolean hasBridgingJam,
            boolean hasAccidentalAdhesion,
            boolean hasMissingStopper,
            boolean hasObserverPolarityDeficit,
            BlockPos targetPos,
            String targetBlockType,
            EngineType engineType,
            int totalMovingBlocks,
            int slimeCount,
            int honeyCount,
            List<BlockPos> conflictNodes,
            List<BlockPos> ghostBlockPlacements,
            List<BlockPos> engineComponents,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static FlyingReport empty() {
            return new FlyingReport(
                    true, false, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", EngineType.NONE, 0, 0, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到活塞飞行器、机械蠕虫或停靠站组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§6【双向活塞飞行器与机械蠕虫动力学因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 机械引擎构型：%s | 移动负载: %d 格 (粘液: §a%d§r, 蜂蜜: §6%d§r)\n",
                    formatType(engineType), totalMovingBlocks, slimeCount, honeyCount));

            if (hasPushLimitExceeded) {
                sb.append("  ⚡ §c[活塞推动超限卡死] 动力构件负载超过 12 格物理推动上限！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 超载构件/阻挡点: %s\n", cPos));
                }
            }

            if (hasBridgingJam) {
                sb.append("  ⚡ §c[粘液/蜂蜜短路粘连] 异动引擎构件发生同类粘性方块相互吸附！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 粘连接触点: %s (两段无法解耦推进)\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在此替换为对立粘性方块或带釉陶瓦: %s\n", gPos));
                }
            }

            if (hasAccidentalAdhesion) {
                sb.append("  ⚡ §d[外部地形意外吸附] 粘性方块抓取了周围未隔离的常规地形方块！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 意外吸附位置: %s\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在此铺设带釉陶瓦导轨: %s\n", gPos));
                }
            }

            if (hasMissingStopper) {
                sb.append("  ⚡ §e[停靠站缺失黑曜石限位] 飞行器到达端点将冲毁换向基站机构！§r\n");
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在停靠撞击端补全黑曜石阻挡块: %s\n", gPos));
                }
            }

            if (hasObserverPolarityDeficit) {
                sb.append("  ⚡ §c[侦测器朝向极性失配] 侦测器输出未正对动力活塞或时序反向！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 朝向失配侦测器: %s (单拍运行后失去自激脉冲)\n", cPos));
                }
            }

            if (isHealthy) {
                sb.append("  ✔ §a[飞行引擎动力健康] 12 格负载预算合规，时序闭环与粘液/蜂蜜隔断正常。§r\n");
            }

            sb.append("▸ §6核心诊断§r：").append(primaryDiagnosis).append("\n");
            if (!actionableAdvice.isEmpty()) {
                sb.append("▸ §a修复建议§r：").append(actionableAdvice).append("\n");
            }
            return sb.toString();
        }

        private static String formatType(EngineType type) {
            return switch (type) {
                case TWO_WAY_REVERSIBLE_ENGINE -> "§b双向可逆活塞飞行引擎 (Two-Way Engine)§r";
                case ONE_WAY_ENGINE -> "§a单向自主巡航飞行引擎 (One-Way Engine)§r";
                case MULTI_SEGMENT_HARVESTER -> "§d多段复合收割/盾构机械 (Multi-Stage Harvester/Bore)§r";
                case DOCKING_STATION -> "§e端点停靠与换向基站 (Docking Station)§r";
                case NONE -> "§7未识别§r";
            };
        }
    }

    private FlyingMachineAnalyzer() {}

    public static FlyingReport analyzeFlyingMachine(LocalMachineCluster cluster, BlockPos focus) {
        if (cluster == null || cluster.isEmpty()) {
            return FlyingReport.empty();
        }

        LocalBlock target = cluster.getBlock(focus);
        if (target == null) {
            target = cluster.originBlock().orElse(null);
        }

        if (target == null || (!target.isFlyingComponent())) {
            target = cluster.blocks().values().stream()
                    .filter(LocalBlock::isFlyingComponent)
                    .findFirst().orElse(null);
        }

        if (target == null) {
            return FlyingReport.empty();
        }

        BlockPos targetPos = target.pos();
        String targetBlockType = target.blockId();

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> ghostBlockPlacements = new ArrayList<>();
        List<BlockPos> engineComponents = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        List<LocalBlock> pistons = cluster.blocks().values().stream().filter(LocalBlock::isPiston).toList();
        List<LocalBlock> observers = cluster.blocks().values().stream().filter(LocalBlock::isObserver).toList();
        List<LocalBlock> slimeBlocks = cluster.blocks().values().stream().filter(LocalBlock::isSlimeBlock).toList();
        List<LocalBlock> honeyBlocks = cluster.blocks().values().stream().filter(LocalBlock::isHoneyBlock).toList();

        for (LocalBlock b : cluster.blocks().values()) {
            if (b.isFlyingComponent()) {
                engineComponents.add(b.pos());
            }
        }

        int slimeCount = slimeBlocks.size();
        int honeyCount = honeyBlocks.size();

        EngineType engineType = EngineType.ONE_WAY_ENGINE;
        if (pistons.size() >= 2) {
            Set<String> facings = pistons.stream().map(LocalBlock::facing).collect(Collectors.toSet());
            boolean hasOpposing = (facings.contains("east") && facings.contains("west")) ||
                                  (facings.contains("north") && facings.contains("south")) ||
                                  (facings.contains("up") && facings.contains("down"));
            if (hasOpposing) {
                engineType = EngineType.TWO_WAY_REVERSIBLE_ENGINE;
            } else if (pistons.size() >= 3) {
                engineType = EngineType.MULTI_SEGMENT_HARVESTER;
            }
        } else if (slimeCount == 0 && honeyCount == 0 && cluster.blocks().values().stream().anyMatch(b -> b.isTrapdoor() || b.isNoteBlock() || b.isObsidian())) {
            engineType = EngineType.DOCKING_STATION;
        }

        boolean hasPushLimitExceeded = false;
        boolean hasBridgingJam = false;
        boolean hasAccidentalAdhesion = false;
        boolean hasMissingStopper = false;
        boolean hasObserverPolarityDeficit = false;

        int maxPushLoad = 0;
        for (LocalBlock piston : pistons) {
            BlockPos facePos = piston.pos().offset(piston.facing());
            Set<BlockPos> pushCluster = calculatePushCluster(cluster, piston, facePos);
            if (pushCluster.size() > maxPushLoad) {
                maxPushLoad = pushCluster.size();
            }
            if (pushCluster.size() > 12) {
                hasPushLimitExceeded = true;
                conflictNodes.add(piston.pos());
                for (BlockPos p : pushCluster) {
                    if (!conflictNodes.contains(p)) {
                        conflictNodes.add(p);
                    }
                }
                issues.add(String.format("活塞推动超限卡死：活塞 %s (朝向 %s) 推动负载达 %d 格，超过 12 格物理推动上限！",
                        piston.pos(), piston.facing(), pushCluster.size()));
            }
        }

        if (pistons.size() >= 2) {
            LocalBlock p1 = pistons.get(0);
            LocalBlock p2 = pistons.get(1);
            if (!p1.facing().equalsIgnoreCase(p2.facing())) {
                for (LocalBlock s1 : slimeBlocks) {
                    for (LocalBlock s2 : slimeBlocks) {
                        if (!s1.pos().equals(s2.pos()) && s1.pos().manhattanDistance(s2.pos()) == 1) {
                            boolean s1NearP1 = s1.pos().manhattanDistance(p1.pos()) <= s1.pos().manhattanDistance(p2.pos());
                            boolean s2NearP2 = s2.pos().manhattanDistance(p2.pos()) < s2.pos().manhattanDistance(p1.pos());
                            if (s1NearP1 && s2NearP2) {
                                hasBridgingJam = true;
                                conflictNodes.add(s1.pos());
                                conflictNodes.add(s2.pos());
                                ghostBlockPlacements.add(s2.pos());
                                issues.add(String.format("粘连短路死锁：两翼动力构件在 %s 与 %s 处发生同类粘液块短路粘连！双驱无法解耦，建议将其中一段替换为蜂蜜块。", s1.pos(), s2.pos()));
                            }
                        }
                    }
                }
                for (LocalBlock h1 : honeyBlocks) {
                    for (LocalBlock h2 : honeyBlocks) {
                        if (!h1.pos().equals(h2.pos()) && h1.pos().manhattanDistance(h2.pos()) == 1) {
                            boolean h1NearP1 = h1.pos().manhattanDistance(p1.pos()) <= h1.pos().manhattanDistance(p2.pos());
                            boolean h2NearP2 = h2.pos().manhattanDistance(p2.pos()) < h2.pos().manhattanDistance(p1.pos());
                            if (h1NearP1 && h2NearP2) {
                                hasBridgingJam = true;
                                conflictNodes.add(h1.pos());
                                conflictNodes.add(h2.pos());
                                ghostBlockPlacements.add(h2.pos());
                                issues.add(String.format("粘连短路死锁：两翼动力构件在 %s 与 %s 处发生同类蜂蜜块短路粘连！双驱无法解耦，建议将其中一段替换为粘液块。", h1.pos(), h2.pos()));
                            }
                        }
                    }
                }
            }
        }

        for (LocalBlock sticky : cluster.blocks().values()) {
            if (sticky.isSlimeBlock() || sticky.isHoneyBlock()) {
                for (BlockPos nbPos : sticky.pos().getDirectNeighbors()) {
                    LocalBlock nb = cluster.getBlock(nbPos);
                    if (nb != null && !nb.isAir() && !nb.isFlyingComponent() && !nb.isGlazedTerracotta() && !nb.isImmovable()) {
                        hasAccidentalAdhesion = true;
                        conflictNodes.add(nbPos);
                        ghostBlockPlacements.add(nbPos);
                        warnings.add(String.format("外界地形意外吸附：粘性方块 %s 意外吸附了外界非绝缘方块 %s (%s)！建议改用带釉陶瓦隔离。",
                                sticky.pos(), nbPos, nb.blockId()));
                    }
                }
            }
        }

        boolean hasDockingTrigger = cluster.blocks().values().stream().anyMatch(b -> b.isTrapdoor() || b.isNoteBlock());
        boolean hasObsidianStopper = cluster.blocks().values().stream().anyMatch(LocalBlock::isObsidian);
        if (hasDockingTrigger && !hasObsidianStopper) {
            hasMissingStopper = true;
            LocalBlock trigger = cluster.blocks().values().stream().filter(b -> b.isTrapdoor() || b.isNoteBlock()).findFirst().orElse(null);
            if (trigger != null) {
                BlockPos stopperPos = trigger.pos().offset("up");
                ghostBlockPlacements.add(stopperPos);
                conflictNodes.add(trigger.pos());
            }
            warnings.add("停靠站缺失黑曜石限位阻挡：检测到换向触发机构 (音符盒/活板门)，但未检测到黑曜石阻挡块！飞行器冲入将推毁换向基站。");
        }

        for (LocalBlock obs : observers) {
            String obsFacing = obs.facing();
            String outputDir = oppositeFacing(obsFacing);
            BlockPos outPos = obs.pos().offset(outputDir);
            LocalBlock outBlock = cluster.getBlock(outPos);

            boolean outputValid = outBlock != null && (outBlock.isPiston() || outBlock.isSlimeBlock() || outBlock.isHoneyBlock() || outBlock.isSolidConductiveBlock());
            if (!outputValid) {
                hasObserverPolarityDeficit = true;
                conflictNodes.add(obs.pos());
                issues.add(String.format("侦测器朝向极性失配：侦测器 %s 朝向 %s (脉冲输出端指向 %s / %s)，未有效对准动力活塞或传导构件！",
                        obs.pos(), obsFacing, outputDir, outPos));
            }
        }

        int totalMovingBlocks = maxPushLoad;
        boolean isHealthy = !hasPushLimitExceeded && !hasBridgingJam && !hasAccidentalAdhesion && !hasMissingStopper && !hasObserverPolarityDeficit;

        String primaryDiagnosis;
        String actionableAdvice;

        if (hasPushLimitExceeded) {
            primaryDiagnosis = "飞行器动力构件超载：推动方块总数超过 12 格上限，活塞卡死无法伸展";
            actionableAdvice = "拆减附带方块或分割推拉动力构件，确保每个活塞推动的粘附子集群 ≤ 12 个方块。";
        } else if (hasBridgingJam) {
            primaryDiagnosis = "两翼动力构件发生粘连短路：同种粘性方块相互吸附导致两段无法解耦推进";
            actionableAdvice = "在相邻动力段交错使用粘液块与蜂蜜块（互不相粘特性），或用带釉陶瓦阻断粘连。";
        } else if (hasObserverPolarityDeficit) {
            primaryDiagnosis = "侦测器朝向极性颠倒或时序断流：脉冲输出端未正确驱动动力活塞";
            actionableAdvice = "调整侦测器朝向，确保感应面朝向移动侦测位，红石输出红点精准对准动力活塞或驱动粘性方块。";
        } else if (hasAccidentalAdhesion) {
            primaryDiagnosis = "粘性方块吸附外界未绝缘地形方块，引发整机阻力超载停摆";
            actionableAdvice = "在飞行轨道两侧隧道或基座铺设带釉陶瓦 (Glazed Terracotta)，利用其不粘特性隔离外界地形。";
        } else if (hasMissingStopper) {
            primaryDiagnosis = "端点换向停靠站缺乏黑曜石等不可移动方块进行刚性阻挡拦截";
            actionableAdvice = "在停靠撞击端加装黑曜石/哭泣黑曜石阻挡块，确保飞行器到位刹车并触发换向更新。";
        } else {
            primaryDiagnosis = "双向活塞飞行器与机械蠕虫动力学完整健康";
            actionableAdvice = "动力活塞推拉时钟同步，12格推动预算与粘液/蜂蜜隔断合规，可稳定自激巡航。";
        }

        return new FlyingReport(
                isHealthy,
                hasPushLimitExceeded,
                hasBridgingJam,
                hasAccidentalAdhesion,
                hasMissingStopper,
                hasObserverPolarityDeficit,
                targetPos,
                targetBlockType,
                engineType,
                totalMovingBlocks,
                slimeCount,
                honeyCount,
                conflictNodes,
                ghostBlockPlacements,
                engineComponents,
                issues,
                warnings,
                primaryDiagnosis,
                actionableAdvice
        );
    }

    private static Set<BlockPos> calculatePushCluster(LocalMachineCluster cluster, LocalBlock piston, BlockPos startPos) {
        Set<BlockPos> visited = new HashSet<>();
        Queue<BlockPos> queue = new ArrayDeque<>();

        LocalBlock startBlock = cluster.getBlock(startPos);
        if (startBlock == null || startBlock.isAir()) {
            return visited;
        }

        queue.add(startPos);
        visited.add(startPos);

        while (!queue.isEmpty() && visited.size() <= 20) {
            BlockPos cur = queue.poll();
            LocalBlock curBlock = cluster.getBlock(cur);
            if (curBlock == null || curBlock.isAir()) continue;

            if (curBlock.isSlimeBlock()) {
                for (BlockPos nbPos : cur.getDirectNeighbors()) {
                    if (visited.contains(nbPos) || nbPos.equals(piston.pos())) continue;
                    LocalBlock nb = cluster.getBlock(nbPos);
                    if (nb != null && !nb.isAir() && !nb.isImmovable() && !nb.isHoneyBlock() && !nb.isGlazedTerracotta()) {
                        visited.add(nbPos);
                        queue.add(nbPos);
                    }
                }
            } else if (curBlock.isHoneyBlock()) {
                for (BlockPos nbPos : cur.getDirectNeighbors()) {
                    if (visited.contains(nbPos) || nbPos.equals(piston.pos())) continue;
                    LocalBlock nb = cluster.getBlock(nbPos);
                    if (nb != null && !nb.isAir() && !nb.isImmovable() && !nb.isSlimeBlock() && !nb.isGlazedTerracotta()) {
                        visited.add(nbPos);
                        queue.add(nbPos);
                    }
                }
            }
        }
        return visited;
    }

    private static String oppositeFacing(String facing) {
        return switch (facing.toLowerCase()) {
            case "north" -> "south";
            case "south" -> "north";
            case "east" -> "west";
            case "west" -> "east";
            case "up" -> "down";
            case "down" -> "up";
            default -> "down";
        };
    }
}
