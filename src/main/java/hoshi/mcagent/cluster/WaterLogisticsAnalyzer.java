package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Diagnostic analyzer for Minecraft Water and Bubble Column Logistics (v2.9.0):
 * - Soul sand bubble elevator source-block continuity & broken flowing-water traps
 * - Top ejection spill hazard and missing deflector ceiling
 * - Ice canal 8-block flow horizon & dry-ice inertia glide gaps
 * - Honey block / chest edge 0.125-block item alignment for dual-hopper overlap (5.0 items/s)
 * - Opposing eddy currents, zero-velocity stagnation points & 5-minute item despawn traps
 */
public final class WaterLogisticsAnalyzer {

    public enum WaterLogisticsType {
        SOUL_SAND_BUBBLE_ELEVATOR,
        MAGMA_WHIRLPOOL_COLUMN,
        ICE_WATER_CANAL,
        ALIGNED_HOPPER_STREAM,
        DROPPER_WATER_INJECTION,
        NONE
    }

    public record WaterReport(
            boolean isHealthy,
            boolean hasBrokenBubbleColumn,
            boolean hasTopSpillRisk,
            boolean hasFlowStallRisk,
            boolean hasMisalignedStream,
            boolean hasDespawnVortexRisk,
            BlockPos targetPos,
            String targetBlockType,
            WaterLogisticsType logisticsType,
            int waterBlockCount,
            int iceBlockCount,
            List<BlockPos> conflictNodes,
            List<BlockPos> ghostBlockPlacements,
            List<BlockPos> waterComponents,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static WaterReport empty() {
            return new WaterReport(
                    true, false, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", WaterLogisticsType.NONE, 0, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到水流、气泡柱、冰道物流或物品对齐组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§b【水流传输网络、气泡柱动力学与物品对齐因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 物流类型：%s | 水体单元数: %d (冰道方块: §b%d§r)\n",
                    formatType(logisticsType), waterBlockCount, iceBlockCount));

            if (hasBrokenBubbleColumn) {
                sb.append("  ⚡ §c[气泡柱中断卡死] 灵魂沙垂直水柱中检测到流动水！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 流动水断点: %s (非全源水导致浮力消失，掉落物卡死)\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在此种植海带转化为水源: %s\n", gPos));
                }
            }

            if (hasTopSpillRisk) {
                sb.append("  ⚡ §e[顶端外溢散落高危] 气泡柱顶端缺乏坚固顶盖或侧向承接导流水渠！§r\n");
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在顶端上方补全防喷顶盖/半砖: %s\n", gPos));
                }
            }

            if (hasFlowStallRisk) {
                sb.append("  ⚡ §c[水流动量衰竭停摆] 水道已达到或超过 8 格流动极限！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 推力枯竭点: %s (水平速度降为0，物品停滞)\n", cPos));
                }
            }

            if (hasMisalignedStream) {
                sb.append("  ⚡ §d[物品流未对齐高危] 并排双漏斗上方水渠缺乏蜂蜜块/箱子边缘内凹对齐！§r\n");
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议水渠边缘放置蜂蜜块 (0.125格缝隙对齐): %s\n", gPos));
                }
            }

            if (hasDespawnVortexRisk) {
                sb.append("  ⚡ §c[对冲涡流与5分钟清除高危] 检测到对向流动水死角！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 滞流死角: %s (合速度为0，物品积聚5分钟后必定Despawn)\n", cPos));
                }
            }

            if (isHealthy) {
                sb.append("  ✔ §a[物流动力健康] 水流连续性、气泡柱全源与物品导向拓扑正常。§r\n");
            }

            sb.append("▸ §6核心诊断§r：").append(primaryDiagnosis).append("\n");
            if (!actionableAdvice.isEmpty()) {
                sb.append("▸ §a修复建议§r：").append(actionableAdvice).append("\n");
            }
            return sb.toString();
        }

        private static String formatType(WaterLogisticsType type) {
            return switch (type) {
                case SOUL_SAND_BUBBLE_ELEVATOR -> "§6灵魂沙垂直高速气泡柱提升机§r";
                case MAGMA_WHIRLPOOL_COLUMN -> "§c岩浆块下沉漩涡水道§r";
                case ICE_WATER_CANAL -> "§b蓝冰/浮冰低摩擦水流高速滑道§r";
                case ALIGNED_HOPPER_STREAM -> "§d双漏斗蜂蜜块边缘对齐吞吐线§r";
                case DROPPER_WATER_INJECTION -> "§e投掷器侧向注入与防倒灌站台§r";
                case NONE -> "§7未识别§r";
            };
        }
    }

    private WaterLogisticsAnalyzer() {}

    public static WaterReport analyzeWater(LocalMachineCluster cluster, BlockPos focus) {
        if (cluster == null || cluster.isEmpty()) {
            return WaterReport.empty();
        }

        LocalBlock target = cluster.getBlock(focus);
        if (target == null) {
            target = cluster.originBlock().orElse(null);
        }

        if (target == null || (!target.isWater() && !target.isSoulSand() && !target.isIce() &&
                               !target.isHoneyBlock() && !target.isHopper() && !target.isDropper())) {
            target = cluster.blocks().values().stream()
                    .filter(b -> b.isWater() || b.isSoulSand() || b.isIce() || b.isHoneyBlock() || b.isDropper())
                    .findFirst().orElse(null);
        }

        if (target == null) {
            return WaterReport.empty();
        }

        BlockPos targetPos = target.pos();
        String targetBlockType = target.blockId();

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> ghostBlockPlacements = new ArrayList<>();
        List<BlockPos> waterComponents = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        int waterCount = 0;
        int iceCount = 0;
        for (LocalBlock b : cluster.blocks().values()) {
            if (b.isWater()) {
                waterCount++;
                waterComponents.add(b.pos());
            }
            if (b.isIce()) {
                iceCount++;
            }
        }

        boolean hasBrokenBubble = false;
        boolean hasTopSpill = false;
        boolean hasFlowStall = false;
        boolean hasMisaligned = false;
        boolean hasDespawnVortex = false;

        WaterLogisticsType logisticsType = WaterLogisticsType.NONE;

        // Check 1: Soul Sand Bubble Column
        LocalBlock soulSandBlock = cluster.blocks().values().stream()
                .filter(LocalBlock::isSoulSand)
                .findFirst().orElse(null);

        if (soulSandBlock != null) {
            logisticsType = WaterLogisticsType.SOUL_SAND_BUBBLE_ELEVATOR;
            BlockPos base = soulSandBlock.pos();
            int curY = base.y() + 1;
            BlockPos highestWaterPos = null;

            while (true) {
                BlockPos colPos = new BlockPos(base.x(), curY, base.z());
                LocalBlock colBlock = cluster.getBlock(colPos);
                if (colBlock == null || !colBlock.isWater()) {
                    break;
                }
                highestWaterPos = colPos;

                if (colBlock.isFlowingWater()) {
                    hasBrokenBubble = true;
                    conflictNodes.add(colPos);
                    ghostBlockPlacements.add(colPos);
                    issues.add(String.format("气泡柱中断卡死：坐标 %s 为流动水而非全源水源！气泡浮力在此处彻底消失，掉落物无法上升。", colPos));
                }
                curY++;
            }

            if (highestWaterPos != null) {
                BlockPos topCapPos = highestWaterPos.offset("up");
                LocalBlock topCapBlock = cluster.getBlock(topCapPos);
                if (topCapBlock == null || topCapBlock.isAir()) {
                    hasTopSpill = true;
                    ghostBlockPlacements.add(topCapPos);
                    warnings.add(String.format("气泡柱顶端外溢高危：顶端 %s 缺乏坚固挡板顶盖，垂直高速冲击力将导致掉落物飞出水渠散落丢失。", topCapPos));
                }
            }
        }

        // Check 2: Ice canal 8-block limit & flow stall
        if (iceCount > 0 || cluster.blocks().values().stream().anyMatch(LocalBlock::isIce)) {
            if (logisticsType == WaterLogisticsType.NONE) {
                logisticsType = WaterLogisticsType.ICE_WATER_CANAL;
            }

            Map<Integer, List<LocalBlock>> waterByY = cluster.blocks().values().stream()
                    .filter(LocalBlock::isWater)
                    .collect(Collectors.groupingBy(b -> b.pos().y()));

            for (Map.Entry<Integer, List<LocalBlock>> entry : waterByY.entrySet()) {
                List<LocalBlock> layer = entry.getValue();
                int minX = layer.stream().mapToInt(b -> b.pos().x()).min().orElse(0);
                int maxX = layer.stream().mapToInt(b -> b.pos().x()).max().orElse(0);
                int minZ = layer.stream().mapToInt(b -> b.pos().z()).min().orElse(0);
                int maxZ = layer.stream().mapToInt(b -> b.pos().z()).max().orElse(0);

                int spanX = maxX - minX + 1;
                int spanZ = maxZ - minZ + 1;

                if (spanX >= 8) {
                    boolean hasSign = cluster.blocks().values().stream().anyMatch(LocalBlock::isSign);
                    if (!hasSign) {
                        hasFlowStall = true;
                        BlockPos stallPos = new BlockPos(maxX, entry.getKey(), minZ);
                        conflictNodes.add(stallPos);
                        issues.add(String.format("水流动力耗尽停摆：X轴水流长度达 %d 格，超出 8 格流动极限 (坐标 %s)，水流推力归零卡死。", spanX, stallPos));
                    }
                }
                if (spanZ >= 8) {
                    boolean hasSign = cluster.blocks().values().stream().anyMatch(LocalBlock::isSign);
                    if (!hasSign) {
                        hasFlowStall = true;
                        BlockPos stallPos = new BlockPos(minX, entry.getKey(), maxZ);
                        conflictNodes.add(stallPos);
                        issues.add(String.format("水流动力耗尽停摆：Z轴水流长度达 %d 格，超出 8 格流动极限 (坐标 %s)，水流推力归零卡死。", spanZ, stallPos));
                    }
                }
            }
        }

        // Check 3: Dual-hopper Item Alignment (Honey Block / Chest edge)
        List<LocalBlock> hoppers = cluster.getConnectedHoppers();
        if (hoppers.size() >= 2) {
            boolean isParallelHoppers = false;
            for (int i = 0; i < hoppers.size(); i++) {
                for (int j = i + 1; j < hoppers.size(); j++) {
                    BlockPos p1 = hoppers.get(i).pos();
                    BlockPos p2 = hoppers.get(j).pos();
                    if (p1.y() == p2.y() && p1.manhattanDistance(p2) == 1) {
                        isParallelHoppers = true;
                        break;
                    }
                }
            }

            if (isParallelHoppers) {
                if (logisticsType == WaterLogisticsType.NONE) {
                    logisticsType = WaterLogisticsType.ALIGNED_HOPPER_STREAM;
                }
                boolean hasHoney = cluster.blocks().values().stream().anyMatch(LocalBlock::isHoneyBlock);
                boolean hasChest = cluster.blocks().values().stream().anyMatch(LocalBlock::isChest);

                if (!hasHoney && !hasChest) {
                    hasMisaligned = true;
                    for (LocalBlock h : hoppers) {
                        conflictNodes.add(h.pos());
                    }
                    BlockPos recPos = hoppers.get(0).pos().offset("up").offset("north");
                    ghostBlockPlacements.add(recPos);
                    warnings.add("物品流未对齐高危：并排双漏斗上方水渠未检测到蜂蜜块或箱子等 0.125 格边缘内凹对齐构件！掉落物无法跨双漏斗吸取盒，吞吐量折半且易溢出丢物。");
                }
            }
        }

        // Check 4: Opposing Eddy Currents & Despawn Vortex
        List<LocalBlock> sources = cluster.blocks().values().stream()
                .filter(b -> b.isWater() && b.isWaterSource())
                .collect(Collectors.toList());

        if (sources.size() >= 2) {
            for (int i = 0; i < sources.size(); i++) {
                for (int j = i + 1; j < sources.size(); j++) {
                    BlockPos s1 = sources.get(i).pos();
                    BlockPos s2 = sources.get(j).pos();
                    if (s1.y() == s2.y() && s1.manhattanDistance(s2) <= 4 && s1.manhattanDistance(s2) > 1) {
                        BlockPos mid = new BlockPos((s1.x() + s2.x()) / 2, s1.y(), (s1.z() + s2.z()) / 2);
                        LocalBlock midBlock = cluster.getBlock(mid);
                        if (midBlock != null && midBlock.isWater()) {
                            hasDespawnVortex = true;
                            conflictNodes.add(mid);
                            issues.add(String.format("对冲涡流滞流死角：水源 %s 与 %s 对向冲击，中间点 %s 合速度为零形成滞流漩涡！掉落物滞留 5 分钟后必定被清除 (Despawn)。", s1, s2, mid));
                        }
                    }
                }
            }
        }

        if (logisticsType == WaterLogisticsType.NONE && (waterCount > 0 || iceCount > 0)) {
            logisticsType = WaterLogisticsType.ICE_WATER_CANAL;
        }

        boolean isHealthy = !hasBrokenBubble && !hasTopSpill && !hasFlowStall && !hasMisaligned && !hasDespawnVortex;

        String primaryDiagnosis;
        String actionableAdvice;

        if (hasBrokenBubble) {
            primaryDiagnosis = "气泡柱水体中断：存在流动水破坏了全源水连续性，浮力推力消失";
            actionableAdvice = "在流动水方块处种植海带并催熟至顶层，或在其位置放置冰块打碎转化为水源。";
        } else if (hasFlowStall) {
            primaryDiagnosis = "水流超出 8 格流动极限，末端推力衰竭导致物品停摆卡死";
            actionableAdvice = "在第 8 格放置告示牌阻断水流，留出 1~2 格干燥冰面（依靠惯性滑行），紧接放置新水源开启下一段流水。";
        } else if (hasDespawnVortex) {
            primaryDiagnosis = "双向水源对冲形成零速度滞流漩涡，物品面临 5 分钟 Despawn 清除";
            actionableAdvice = "拆除对冲水源或用告示牌/实体方块建立单向导流挡板，消除对流死角。";
        } else if (hasMisaligned) {
            primaryDiagnosis = "双漏斗上方水流未对齐，掉落物无法同时覆盖两个漏斗的吸取体积";
            actionableAdvice = "在水渠侧壁放置蜂蜜块或箱子，利用 14/16 (0.875格) 碰撞箱让物品在 0.125 格边缘内凹处对齐双漏斗中缝。";
        } else if (hasTopSpill) {
            primaryDiagnosis = "气泡柱顶端缺乏防喷顶盖，高速冲出的掉落物存在外溢散落风险";
            actionableAdvice = "在气泡柱顶水方块上方 1 格安装平滑石半砖或活板门作为导流顶盖，并布置 90° 横向导流。";
        } else {
            primaryDiagnosis = "水流与气泡柱物流网络动力学完整健康";
            actionableAdvice = "水路拓扑规范，全源水连续性与物品推进正常。";
        }

        return new WaterReport(
                isHealthy,
                hasBrokenBubble,
                hasTopSpill,
                hasFlowStall,
                hasMisaligned,
                hasDespawnVortex,
                targetPos,
                targetBlockType,
                logisticsType,
                waterCount,
                iceCount,
                conflictNodes,
                ghostBlockPlacements,
                waterComponents,
                issues,
                warnings,
                primaryDiagnosis,
                actionableAdvice
        );
    }
}
