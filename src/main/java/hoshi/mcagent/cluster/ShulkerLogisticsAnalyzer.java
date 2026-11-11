package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Diagnostic analyzer for Minecraft Shulker Box Logistics & Automation (v2.11.0):
 * - Dispenser vs Dropper: Shulker box block placement vs item entity spit
 * - Fullness comparator detection & hopper siphon race condition locking
 * - Shulker box 1-block clearance opening constraint
 * - Piston break mechanics & 5-minute despawn drop collection channels
 * - Shulker unloader zero-signal monostable pulse & persistent piston deadlock prevention
 */
public final class ShulkerLogisticsAnalyzer {

    public enum ShulkerSystemType {
        SHULKER_LOADER,
        SHULKER_UNLOADER,
        MANUAL_UNLOADER,
        NONE
    }

    public record ShulkerReport(
            boolean isHealthy,
            boolean hasDropperInsteadOfDispenser,
            boolean hasUnlockedHopperSiphon,
            boolean hasBoxOpenClearanceBlocked,
            boolean hasUncollectedDropHazard,
            boolean hasPersistentPistonLock,
            BlockPos targetPos,
            String targetBlockType,
            ShulkerSystemType systemType,
            int signalStrength,
            List<BlockPos> conflictNodes,
            List<BlockPos> ghostBlockPlacements,
            List<BlockPos> systemComponents,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static ShulkerReport empty() {
            return new ShulkerReport(
                    true, false, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", ShulkerSystemType.NONE, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到潜影盒装盒机、拆盒机或物流自动化组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§6【潜影盒装卸物流与自动化因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 物流系统构型：%s | 比较器信号: §e%d/15§r\n",
                    formatType(systemType), signalStrength));

            if (hasDropperInsteadOfDispenser) {
                sb.append("  ⚡ §c[投掷器误用致命卡死] 放置潜影盒必须使用发射器 (Dispenser)，误用投掷器只会将盒子作为掉落物吐出！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 误用投掷器: %s\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在此替换为发射器: %s\n", gPos));
                }
            }

            if (hasUnlockedHopperSiphon) {
                sb.append("  ⚡ §c[下方漏斗偷吸空盒] 装盒机下方收集漏斗未施加红石锁定，新放置的空盒被立刻吸走导致无限吐盒！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 未锁定漏斗: %s\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议接入红石锁定脉冲/火把锁存: %s\n", gPos));
                }
            }

            if (hasBoxOpenClearanceBlocked) {
                sb.append("  ⚡ §e[开盖空间物理受阻] 潜影盒开盖朝向正前方 1 格被实心方块封堵，无法正常开启！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ⚠ 阻挡方块: %s (需换为透明方块或空气)\n", cPos));
                }
            }

            if (hasUncollectedDropHazard) {
                sb.append("  ⚡ §e[掉落物无收集通道] 活塞推破潜影盒的落点周围无漏斗或水流承接，满载潜影盒将在 5 分钟后清除！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ⚠ 缺乏收集落点: %s\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议在此布置收集漏斗或水流: %s\n", gPos));
                }
            }

            if (hasPersistentPistonLock) {
                sb.append("  ⚡ §c[活塞持续伸出死锁] 拆盒机推盒活塞处于持续伸出状态，阻挡发射器放置下一个潜影盒！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 持续通电活塞: %s (需接入单稳态 1~2 刻短脉冲)\n", cPos));
                }
            }

            if (isHealthy) {
                sb.append("  ✔ §a潜影盒自动化流水线物理拓扑、发射时序与收集通道健康无死锁。§r\n");
            }

            sb.append(String.format("▸ 因果诊断：%s\n", primaryDiagnosis));
            if (!actionableAdvice.isEmpty()) {
                sb.append(String.format("▸ 优化建议：%s\n", actionableAdvice));
            }
            return sb.toString();
        }

        private static String formatType(ShulkerSystemType type) {
            return switch (type) {
                case SHULKER_LOADER -> "§6[自动装盒机 Shulker Loader]§r";
                case SHULKER_UNLOADER -> "§b[自动拆盒机 Shulker Unloader]§r";
                case MANUAL_UNLOADER -> "§a[手工存取/卸货台 Manual Station]§r";
                case NONE -> "§7[无/未识别]§r";
            };
        }
    }

    public static ShulkerReport analyzeShulker(LocalMachineCluster cluster, BlockPos focus) {
        if (cluster == null || cluster.isEmpty()) {
            return ShulkerReport.empty();
        }

        LocalBlock target = cluster.getBlock(focus);
        if (target == null) {
            Optional<LocalBlock> anyShulker = cluster.blocks().values().stream()
                    .filter(LocalBlock::isShulkerComponent)
                    .findFirst();
            if (anyShulker.isPresent()) {
                target = anyShulker.get();
                focus = target.pos();
            } else {
                return ShulkerReport.empty();
            }
        }

        List<LocalBlock> shulkerBoxes = cluster.blocks().values().stream()
                .filter(LocalBlock::isShulkerBox)
                .collect(Collectors.toList());
        List<LocalBlock> dispensers = cluster.blocks().values().stream()
                .filter(LocalBlock::isDispenser)
                .collect(Collectors.toList());
        List<LocalBlock> droppers = cluster.blocks().values().stream()
                .filter(LocalBlock::isDropper)
                .collect(Collectors.toList());
        List<LocalBlock> pistons = cluster.blocks().values().stream()
                .filter(LocalBlock::isPiston)
                .collect(Collectors.toList());
        List<LocalBlock> hoppers = cluster.getConnectedHoppers();
        List<LocalBlock> comparators = cluster.getConnectedComparators();

        if (shulkerBoxes.isEmpty() && dispensers.isEmpty() && droppers.isEmpty()) {
            return ShulkerReport.empty();
        }

        List<BlockPos> systemComponents = new ArrayList<>();
        shulkerBoxes.forEach(b -> systemComponents.add(b.pos()));
        dispensers.forEach(b -> systemComponents.add(b.pos()));
        droppers.forEach(b -> systemComponents.add(b.pos()));
        pistons.forEach(b -> systemComponents.add(b.pos()));
        hoppers.forEach(b -> systemComponents.add(b.pos()));
        comparators.forEach(b -> systemComponents.add(b.pos()));

        // Determine System Type
        ShulkerSystemType systemType = ShulkerSystemType.NONE;
        boolean hasTopFeedingHopper = false;
        boolean hasBottomExtractingHopper = false;

        for (LocalBlock sBox : shulkerBoxes) {
            LocalBlock above = cluster.getBlock(sBox.pos().offset("up"));
            LocalBlock below = cluster.getBlock(sBox.pos().offset("down"));
            if (above != null && above.isHopper()) hasTopFeedingHopper = true;
            if (below != null && below.isHopper()) hasBottomExtractingHopper = true;
        }

        if (hasTopFeedingHopper || (!dispensers.isEmpty() && !pistons.isEmpty() && !hasBottomExtractingHopper)) {
            systemType = ShulkerSystemType.SHULKER_LOADER;
        } else if (hasBottomExtractingHopper && (!pistons.isEmpty() || !dispensers.isEmpty())) {
            systemType = ShulkerSystemType.SHULKER_UNLOADER;
        } else if (!shulkerBoxes.isEmpty()) {
            systemType = ShulkerSystemType.MANUAL_UNLOADER;
        } else if (!dispensers.isEmpty() || !droppers.isEmpty()) {
            systemType = ShulkerSystemType.SHULKER_LOADER;
        }

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> ghostBlockPlacements = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        boolean hasDropperInsteadOfDispenser = false;
        boolean hasUnlockedHopperSiphon = false;
        boolean hasBoxOpenClearanceBlocked = false;
        boolean hasUncollectedDropHazard = false;
        boolean hasPersistentPistonLock = false;

        // 1. Check Dropper vs Dispenser
        for (LocalBlock dropper : droppers) {
            String facing = dropper.facing();
            BlockPos targetPlacement = dropper.pos().offset(facing);
            if (cluster.blocks().containsKey(targetPlacement) || systemType == ShulkerSystemType.SHULKER_LOADER) {
                hasDropperInsteadOfDispenser = true;
                conflictNodes.add(dropper.pos());
                ghostBlockPlacements.add(dropper.pos());
                issues.add(String.format("在 %s 处误用了投掷器 (Dropper) 代替发射器 (Dispenser)，导致潜影盒作为掉落物喷出而非放置为方块", dropper.pos()));
            }
        }

        // 2. Check Unlocked Hopper Siphon in Shulker Loader
        if (systemType == ShulkerSystemType.SHULKER_LOADER) {
            for (LocalBlock sBox : shulkerBoxes) {
                LocalBlock below = cluster.getBlock(sBox.pos().offset("down"));
                if (below != null && below.isHopper()) {
                    boolean isLocked = below.isPowered() || "false".equalsIgnoreCase(below.getProperty("enabled", "true"));
                    if (!isLocked) {
                        hasUnlockedHopperSiphon = true;
                        conflictNodes.add(below.pos());
                        ghostBlockPlacements.add(below.pos().offset("east"));
                        issues.add(String.format("装盒机下方收集漏斗 %s 未受红石锁定，新盒发射瞬间将被直接吸走导致无限吐盒", below.pos()));
                    }
                }
            }
        }

        // 3. Check Shulker Box Open Clearance Blockage
        for (LocalBlock sBox : shulkerBoxes) {
            String facing = sBox.facing();
            if (facing == null || facing.isEmpty()) facing = "up";
            BlockPos openPos = sBox.pos().offset(facing);
            LocalBlock openBlock = cluster.getBlock(openPos);
            if (openBlock != null && openBlock.isSolidConductiveBlock()) {
                hasBoxOpenClearanceBlocked = true;
                conflictNodes.add(openPos);
                warnings.add(String.format("潜影盒 %s 正前方开盖空间 %s 被实心方块 (%s) 封堵，物理上无法开启",
                        sBox.pos(), openPos, openBlock.blockId()));
            }
        }

        // 4. Check Uncollected Drop Hazard for Piston Break
        for (LocalBlock piston : pistons) {
            String pFacing = piston.facing();
            BlockPos breakTarget = piston.pos().offset(pFacing);
            LocalBlock targetB = cluster.getBlock(breakTarget);
            if (targetB != null && (targetB.isShulkerBox() || targetB.isAir())) {
                boolean hasCollector = false;
                for (BlockPos adj : breakTarget.neighbors()) {
                    LocalBlock adjB = cluster.getBlock(adj);
                    if (adjB != null && (adjB.isHopper() || adjB.isWater())) {
                        hasCollector = true;
                        break;
                    }
                }
                LocalBlock belowTarget = cluster.getBlock(breakTarget.offset("down"));
                if (belowTarget != null && (belowTarget.isHopper() || belowTarget.isWater())) {
                    hasCollector = true;
                }
                if (!hasCollector) {
                    hasUncollectedDropHazard = true;
                    conflictNodes.add(breakTarget);
                    ghostBlockPlacements.add(breakTarget.offset("down"));
                    warnings.add(String.format("活塞推破目标位 %s 下方及周围缺乏漏斗或水流收集通道，满载潜影盒将在 5 分钟后清除", breakTarget));
                }
            }
        }

        // 5. Check Persistent Piston Lock in Shulker Unloader
        if (systemType == ShulkerSystemType.SHULKER_UNLOADER) {
            for (LocalBlock piston : pistons) {
                if (piston.isExtended() || piston.isPowered()) {
                    hasPersistentPistonLock = true;
                    conflictNodes.add(piston.pos());
                    issues.add(String.format("拆盒机推盒活塞 %s 处于持续伸出状态，阻挡发射器放置下一个潜影盒，流水线死锁", piston.pos()));
                }
            }
        }

        // Signal strength detection from comparator
        int signalStrength = 0;
        for (LocalBlock comp : comparators) {
            try {
                int sig = Integer.parseInt(comp.getProperty("power", "0"));
                if (sig > signalStrength) signalStrength = sig;
            } catch (NumberFormatException ignored) {}
        }

        boolean isHealthy = !hasDropperInsteadOfDispenser && !hasUnlockedHopperSiphon &&
                !hasBoxOpenClearanceBlocked && !hasUncollectedDropHazard && !hasPersistentPistonLock;

        String primaryDiagnosis;
        String actionableAdvice;

        if (hasDropperInsteadOfDispenser) {
            primaryDiagnosis = "装盒机误用了投掷器代替发射器，潜影盒被当作掉落物吐出无法放置。";
            actionableAdvice = "将投掷器 (Dropper) 替换为发射器 (Dispenser)，圆孔朝向潜影盒放置位。";
        } else if (hasUnlockedHopperSiphon) {
            primaryDiagnosis = "装盒机下方收集漏斗未施加红石锁存，导致空盒落位即被偷吸。";
            actionableAdvice = "在活塞推破与发射新盒期间，通过红石火把或比较器脉冲锁死下方漏斗，落位后再解锁。";
        } else if (hasPersistentPistonLock) {
            primaryDiagnosis = "拆盒机活塞持续伸出阻挡新盒放置，缺少单稳态短脉冲截断。";
            actionableAdvice = "在比较器信号归零检测端接入 1~2 刻单稳态脉冲电路 (Monostable Circuit) 产生瞬态推破脉冲。";
        } else if (hasBoxOpenClearanceBlocked) {
            primaryDiagnosis = "潜影盒开盖空间被实心方块遮挡，玩家或机械无法打开。";
            actionableAdvice = "将开盖正前方的方块替换为玻璃、半砖、楼梯或空气。";
        } else if (hasUncollectedDropHazard) {
            primaryDiagnosis = "活塞推破落点周围缺乏漏斗或水流收集通道，潜影盒面临清除风险。";
            actionableAdvice = "在潜影盒落点下方铺设漏斗、漏斗矿车或导流水渠承接。";
        } else {
            primaryDiagnosis = "潜影盒装卸物流系统物理拓扑、发射时序与开盖通道健康。";
            actionableAdvice = "保持发射器备用盒供应，定期检查比较器信号线防外部串扰。";
        }

        return new ShulkerReport(
                isHealthy,
                hasDropperInsteadOfDispenser,
                hasUnlockedHopperSiphon,
                hasBoxOpenClearanceBlocked,
                hasUncollectedDropHazard,
                hasPersistentPistonLock,
                focus,
                target.blockId(),
                systemType,
                signalStrength,
                conflictNodes,
                ghostBlockPlacements,
                systemComponents,
                issues,
                warnings,
                primaryDiagnosis,
                actionableAdvice
        );
    }
}
