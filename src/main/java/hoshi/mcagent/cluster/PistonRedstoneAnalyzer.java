package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Diagnostic analyzer for Minecraft Java Edition Piston dynamics,
 * Quasi-Connectivity (QC), BUD (Block Update Detector) state-locks,
 * and 12-block push limits with Slime/Honey adhesion networks.
 */
public final class PistonRedstoneAnalyzer {

    public record PistonReport(
            boolean isHealthy,
            boolean isDirectlyPowered,
            boolean isQcPowered,
            boolean isBudLocked,
            boolean isBudPending,
            boolean isPushLimitExceeded,
            boolean hasImmovableObstacle,
            BlockPos pistonPos,
            String pistonFacing,
            int pushChainCount,
            List<BlockPos> pushChain,
            List<BlockPos> directPowerSources,
            List<BlockPos> qcPowerSources,
            List<BlockPos> immovableBlocks,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static PistonReport empty() {
            return new PistonReport(true, false, false, false, false, false, false,
                    new BlockPos(0, 0, 0), "unknown", 0,
                    Collections.emptyList(), Collections.emptyList(), Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    "未检测到活塞机械组件", "");
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§e【红石活塞与准连接 (QC) 拓扑诊断报告】§r\n");
            sb.append(String.format("▸ 目标活塞坐标：%s (朝向: %s)\n", pistonPos, pistonFacing.toUpperCase()));
            sb.append(String.format("▸ 供电状态：%s | 准连接(QC): %s\n",
                    isDirectlyPowered ? "§a直接供电§r" : "§7无直接供电§r",
                    isQcPowered ? "§b激活 (QC)§r" : "§7无§r"));

            if (isBudLocked) {
                sb.append("  ⚡ §c[BUD 锁定卡死] 供电已断开，但缺少方块更新导致活塞保持伸出！§r\n");
            } else if (isBudPending) {
                sb.append("  ⚡ §6[BUD 待命潜伏] 上方 QC 已充能，等待邻域方块更新触发弹出！§r\n");
            }

            sb.append(String.format("▸ 推块链条负载：%d / 12 方块 %s\n",
                    pushChainCount,
                    isPushLimitExceeded ? "§c[超重 >12]§r" : "§a[正常]§r"));

            if (!directPowerSources.isEmpty()) {
                sb.append("  - 直接供电源: ");
                for (BlockPos p : directPowerSources) sb.append(p).append(" ");
                sb.append("\n");
            }
            if (!qcPowerSources.isEmpty()) {
                sb.append("  - 准连接 (QC) 隔电源: ");
                for (BlockPos p : qcPowerSources) sb.append(p).append(" ");
                sb.append("\n");
            }
            if (!immovableBlocks.isEmpty()) {
                sb.append("  ✖ §c不可移动阻断方块: ");
                for (BlockPos p : immovableBlocks) sb.append(p).append(" ");
                sb.append("§r\n");
            }

            if (!issues.isEmpty()) {
                sb.append("§c【发现问题】§r\n");
                for (String issue : issues) {
                    sb.append("  ✖ ").append(issue).append("\n");
                }
            }
            if (!warnings.isEmpty()) {
                sb.append("§6【注意事项】§r\n");
                for (String w : warnings) {
                    sb.append("  ⚠ ").append(w).append("\n");
                }
            }

            sb.append("▸ 诊断结论：").append(primaryDiagnosis).append("\n");
            sb.append("▸ 优化建议：").append(actionableAdvice);
            return sb.toString();
        }
    }

    public static PistonReport analyze(LocalMachineCluster cluster) {
        return analyze(cluster, null);
    }

    public static PistonReport analyze(LocalMachineCluster cluster, BlockPos targetPos) {
        if (cluster == null || cluster.isEmpty()) {
            return PistonReport.empty();
        }

        LocalBlock piston = null;
        if (targetPos != null) {
            piston = cluster.getBlock(targetPos);
        }
        if (piston == null || !piston.isPiston()) {
            var originOpt = cluster.originBlock();
            if (originOpt.isPresent() && originOpt.get().isPiston()) {
                piston = originOpt.get();
            }
        }
        if (piston == null || !piston.isPiston()) {
            var pistons = cluster.getConnectedPistons();
            if (!pistons.isEmpty()) {
                piston = pistons.get(0);
            }
        }

        if (piston == null || !piston.isPiston()) {
            return PistonReport.empty();
        }

        BlockPos pPos = piston.pos();
        String facing = piston.facing();
        boolean extended = piston.isExtended();

        List<BlockPos> directPower = new ArrayList<>();
        List<BlockPos> qcPower = new ArrayList<>();
        List<BlockPos> immovables = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        // 1. Direct Powering Check (6 direct neighbors)
        for (BlockPos nPos : pPos.getDirectNeighbors()) {
            LocalBlock nBlock = cluster.getBlock(nPos);
            if (nBlock != null) {
                if (nBlock.isRedstonePowerSource()) {
                    directPower.add(nPos);
                }
            }
        }

        // 2. Quasi-Connectivity (QC) Check
        // In Java Edition, a piston checks the block space directly above it (pPos.y + 1)
        // for power sources as if it were the upper part of a 2-block door.
        BlockPos abovePos = pPos.offset("up"); // [x, y+1, z]
        Set<BlockPos> directNeighborSet = new HashSet<>(pPos.getDirectNeighbors());

        // Check abovePos itself
        LocalBlock aboveBlock = cluster.getBlock(abovePos);
        if (aboveBlock != null && aboveBlock.isRedstonePowerSource()) {
            if (!directNeighborSet.contains(abovePos)) {
                qcPower.add(abovePos);
            }
        }

        // Check neighbors of abovePos (abovePos.y+1, abovePos north/south/west/east)
        List<BlockPos> qcCandidatePositions = new ArrayList<>();
        qcCandidatePositions.add(abovePos.offset("up")); // [x, y+2, z]
        qcCandidatePositions.add(abovePos.offset("north"));
        qcCandidatePositions.add(abovePos.offset("south"));
        qcCandidatePositions.add(abovePos.offset("west"));
        qcCandidatePositions.add(abovePos.offset("east"));

        for (BlockPos qp : qcCandidatePositions) {
            if (!directNeighborSet.contains(qp)) {
                LocalBlock qBlock = cluster.getBlock(qp);
                if (qBlock != null && qBlock.isRedstonePowerSource()) {
                    qcPower.add(qp);
                }
            }
        }

        boolean isDirectlyPowered = !directPower.isEmpty();
        boolean isQcPowered = !qcPower.isEmpty();

        // 3. BUD State Machine
        boolean isBudLocked = extended && !isDirectlyPowered && !isQcPowered;
        boolean isBudPending = !extended && !isDirectlyPowered && isQcPowered;

        if (isBudLocked) {
            issues.add(String.format("活塞 %s 处于 BUD 锁定状态：红石源已切断，因未收到方块更新依然保持伸出！", pPos));
        }
        if (isBudPending) {
            warnings.add(String.format("活塞 %s 上方存在准连接 (QC) 充能但未更新：一旦邻近方块发生改变将立即弹出！", pPos));
        }

        // 4. Push Chain & Adhesion BFS
        List<BlockPos> pushChain = new ArrayList<>();
        boolean isPushLimitExceeded = false;
        boolean hasImmovableObstacle = false;

        BlockPos stepPos = pPos.offset(facing);
        Set<BlockPos> visitedInChain = new HashSet<>();
        Queue<BlockPos> queue = new ArrayDeque<>();

        LocalBlock firstBlock = cluster.getBlock(stepPos);
        if (firstBlock != null && !firstBlock.isAir()) {
            queue.add(stepPos);
            visitedInChain.add(stepPos);
        }

        while (!queue.isEmpty()) {
            BlockPos current = queue.poll();
            LocalBlock curBlock = cluster.getBlock(current);
            if (curBlock == null || curBlock.isAir()) {
                continue;
            }

            if (curBlock.isImmovable()) {
                hasImmovableObstacle = true;
                immovables.add(current);
                issues.add(String.format("遭遇不可移动方块 %s (%s)，阻断活塞推动！", current, curBlock.blockId()));
                continue;
            }

            pushChain.add(current);

            // Forward block in the push direction
            BlockPos nextInLine = current.offset(facing);
            if (!visitedInChain.contains(nextInLine)) {
                LocalBlock nextBlock = cluster.getBlock(nextInLine);
                if (nextBlock != null && !nextBlock.isAir()) {
                    visitedInChain.add(nextInLine);
                    queue.add(nextInLine);
                }
            }

            // Slime / Honey Adhesion check
            boolean isSlime = curBlock.isSlimeBlock();
            boolean isHoney = curBlock.isHoneyBlock();

            if (isSlime || isHoney) {
                for (BlockPos neighbor : current.getDirectNeighbors()) {
                    if (neighbor.equals(pPos) || visitedInChain.contains(neighbor)) {
                        continue;
                    }
                    LocalBlock nBlock = cluster.getBlock(neighbor);
                    if (nBlock == null || nBlock.isAir()) {
                        continue;
                    }

                    // Honey-Slime mutual exclusion: Slime does not stick to Honey!
                    if (isSlime && nBlock.isHoneyBlock()) {
                        continue;
                    }
                    if (isHoney && nBlock.isSlimeBlock()) {
                        continue;
                    }
                    // Glazed terracotta is not pulled by slime/honey
                    if (nBlock.isGlazedTerracotta()) {
                        continue;
                    }

                    visitedInChain.add(neighbor);
                    queue.add(neighbor);
                }
            }
        }

        int pushChainCount = pushChain.size();
        if (pushChainCount > 12) {
            isPushLimitExceeded = true;
            BlockPos excessBlock = pushChain.get(12);
            issues.add(String.format("推块链总数达到 %d 块，突破 12 方块上限！第 13 块方块位于 %s", pushChainCount, excessBlock));
        }

        boolean isHealthy = issues.isEmpty() && !isBudLocked;

        String primaryDiagnosis;
        String actionableAdvice;

        if (isBudLocked) {
            primaryDiagnosis = "⚡ [BUD 锁定卡死] 活塞断电后未接收到邻域方块更新，保持伸出卡滞。";
            actionableAdvice = "解决建议：在活塞正交相邻方块处放置或破坏任意方块产生方块更新，或给予一次红石线脉冲强制其复位缩回。";
        } else if (hasImmovableObstacle) {
            primaryDiagnosis = "⚡ [不可移动方块阻断] 推块路径上包含黑曜石、基岩或 Java 版不可推容器 (TileEntity)。";
            actionableAdvice = "解决建议：移除阻碍的不可移动方块，或使用漏斗矿车/投掷器等代替实心阻挡。";
        } else if (isPushLimitExceeded) {
            primaryDiagnosis = String.format("⚡ [推块上限超载] 推块链条包含 %d 块方块，超出 12 方块推力上限。", pushChainCount);
            actionableAdvice = "解决建议：使用釉面陶瓦隔断粘液块/蜜蜂块的横向粘连，或减少推击链条上的方块数量。";
        } else if (isBudPending) {
            primaryDiagnosis = "⚡ [BUD 待命状态] 活塞处于准连接 (QC) 充能状态，等待方块更新触发。";
            actionableAdvice = "状态正常：若需要即时弹出，请在活塞旁引入红石脉冲或更新源；若用于方块更新检测器 (BUD)，已就绪。";
        } else if (isDirectlyPowered || isQcPowered) {
            primaryDiagnosis = "✓ 活塞供电正常，推块链符合动力学规范。";
            actionableAdvice = "保持当前布线即可。";
        } else {
            primaryDiagnosis = "✓ 活塞未充能，推块链处于安全休眠状态。";
            actionableAdvice = "正常状态。通过红石粉或中继器输入信号即可激活。";
        }

        return new PistonReport(
                isHealthy,
                isDirectlyPowered,
                isQcPowered,
                isBudLocked,
                isBudPending,
                isPushLimitExceeded,
                hasImmovableObstacle,
                pPos,
                facing,
                pushChainCount,
                Collections.unmodifiableList(pushChain),
                Collections.unmodifiableList(directPower),
                Collections.unmodifiableList(qcPower),
                Collections.unmodifiableList(immovables),
                Collections.unmodifiableList(issues),
                Collections.unmodifiableList(warnings),
                primaryDiagnosis,
                actionableAdvice
        );
    }
}
