package hoshi.mcagent.spatial;

import hoshi.mcagent.cluster.Ae2NetworkAnalyzer;
import hoshi.mcagent.cluster.PistonRedstoneAnalyzer;
import hoshi.mcagent.cluster.ComparatorRedstoneAnalyzer;
import hoshi.mcagent.cluster.RedstoneLogicAnalyzer;
import hoshi.mcagent.cluster.RedstoneTransmissionAnalyzer;
import hoshi.mcagent.cluster.RailNetworkAnalyzer;
import hoshi.mcagent.cluster.WaterLogisticsAnalyzer;
import hoshi.mcagent.cluster.BlockPos;
import hoshi.mcagent.cluster.HopperNetworkAnalyzer;
import hoshi.mcagent.cluster.KineticNetworkAnalyzer;
import hoshi.mcagent.cluster.LocalBlock;
import hoshi.mcagent.cluster.LocalMachineCluster;
import hoshi.mcagent.multiblock.MultiblockBlueprint;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * High-level generator translating causal engine reports and blueprints into 3D spatial overlay directives.
 */
public final class SpatialDirectiveGenerator {

    private static final Pattern BLOCK_POS_PATTERN = Pattern.compile("\\[(-?\\d+),\\s*(-?\\d+),\\s*(-?\\d+)\\]");

    private SpatialDirectiveGenerator() {}

    /**
     * Generates in-world holographic overlays for Create mod kinetic jamming.
     */
    public static SpatialDirectivePacket generateKineticOverlay(LocalMachineCluster cluster, KineticNetworkAnalyzer.KineticReport report) {
        if (report == null || report.totalComponents() == 0) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds

        if (report.isJammed()) {
            Set<BlockPos> conflictPositions = new LinkedHashSet<>();
            for (String conflictStr : report.conflicts()) {
                Matcher m = BLOCK_POS_PATTERN.matcher(conflictStr);
                List<BlockPos> matched = new ArrayList<>();
                while (m.find()) {
                    int x = Integer.parseInt(m.group(1));
                    int y = Integer.parseInt(m.group(2));
                    int z = Integer.parseInt(m.group(3));
                    matched.add(new BlockPos(x, y, z));
                }
                if (matched.size() >= 2) {
                    BlockPos p1 = matched.get(0);
                    BlockPos p2 = matched.get(1);
                    conflictPositions.add(p1);
                    conflictPositions.add(p2);
                    primitives.add(SpatialPrimitive.flowArrow(p1, p2, SpatialColor.RED, "JAMMED RATIO", duration));
                } else if (matched.size() == 1) {
                    conflictPositions.add(matched.get(0));
                }
            }

            for (BlockPos pos : conflictPositions) {
                primitives.add(SpatialPrimitive.boxOutline(pos, SpatialColor.RED, "JAMMED", duration));
            }

            if (!conflictPositions.isEmpty()) {
                BlockPos first = conflictPositions.iterator().next();
                primitives.add(SpatialPrimitive.billboard(first.offset("up"), "⚠ 传动冲突卡死点", SpatialColor.RED, duration));
            }

            return SpatialDirectivePacket.of(
                    "kinetic-jam-" + System.currentTimeMillis(),
                    "KINETIC_JAM",
                    primitives,
                    report.primaryDiagnosis(),
                    report.actionableRemediation()
            );
        } else {
            if (cluster != null) {
                for (LocalBlock b : cluster.getConnectedKinetics()) {
                    primitives.add(SpatialPrimitive.boxOutline(b.pos(), SpatialColor.GREEN.withAlpha(120), "OK", 100));
                }
            }
            return SpatialDirectivePacket.of(
                    "kinetic-healthy-" + System.currentTimeMillis(),
                    "KINETIC_HEALTHY",
                    primitives,
                    report.primaryDiagnosis(),
                    report.actionableRemediation()
            );
        }
    }

    /**
     * Generates in-world overlay for hopper logistics pipelines, circular deadlocks, and overflow bleed.
     */
    public static SpatialDirectivePacket generateHopperOverlay(LocalMachineCluster cluster, HopperNetworkAnalyzer.HopperReport report) {
        if (report == null || report.totalHoppers() == 0) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds

        // 1. Flow arrows for all connected hoppers
        if (cluster != null) {
            for (LocalBlock h : cluster.getConnectedHoppers()) {
                String facing = h.facing();
                BlockPos targetPos = h.pos().offset(facing);
                primitives.add(SpatialPrimitive.flowArrow(h.pos(), targetPos, SpatialColor.CYAN.withAlpha(140), "FLOW", duration));
            }
        }

        // 2. Deadlock loop overlays
        if (report.hasDeadlock()) {
            for (String dlStr : report.deadlocks()) {
                Matcher m = BLOCK_POS_PATTERN.matcher(dlStr);
                List<BlockPos> cycle = new ArrayList<>();
                while (m.find()) {
                    cycle.add(new BlockPos(Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2)), Integer.parseInt(m.group(3))));
                }
                for (int i = 0; i < cycle.size(); i++) {
                    BlockPos from = cycle.get(i);
                    BlockPos to = cycle.get((i + 1) % cycle.size());
                    primitives.add(SpatialPrimitive.boxOutline(from, SpatialColor.YELLOW, "DEADLOCK", duration));
                    primitives.add(SpatialPrimitive.flowArrow(from, to, SpatialColor.ORANGE, "CYCLE", duration));
                }
            }
        }

        // 3. Stalled / Backpressure hoppers
        if (report.hasBackpressure()) {
            for (String stStr : report.stalledHoppers()) {
                Matcher m = BLOCK_POS_PATTERN.matcher(stStr);
                if (m.find()) {
                    BlockPos p = new BlockPos(Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2)), Integer.parseInt(m.group(3)));
                    primitives.add(SpatialPrimitive.boxOutline(p, SpatialColor.RED, "BACKPRESSURE", duration));
                }
            }
        }

        // 4. Sorter bleed risk
        if (report.hasBleedRisk()) {
            for (String wStr : report.warnings()) {
                Matcher m = BLOCK_POS_PATTERN.matcher(wStr);
                if (m.find()) {
                    BlockPos p = new BlockPos(Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2)), Integer.parseInt(m.group(3)));
                    primitives.add(SpatialPrimitive.boxOutline(p, SpatialColor.PURPLE, "BLEED RISK >45", duration));
                }
            }
        }

        return SpatialDirectivePacket.of(
                "hopper-diag-" + System.currentTimeMillis(),
                "HOPPER_DIAGNOSTICS",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    /**
     * Projects holographic ghost blocks for multiblock blueprints (e.g. Conduit, Beacon, Portal).
     */
    public static SpatialDirectivePacket generateMultiblockGhostOverlay(MultiblockBlueprint blueprint, BlockPos centerPos) {
        if (blueprint == null || centerPos == null) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 600; // 30 seconds

        int sizeX = blueprint.widthX();
        int sizeY = blueprint.heightY();
        int sizeZ = blueprint.depthZ();

        int halfX = sizeX / 2;
        int halfY = sizeY / 2;
        int halfZ = sizeZ / 2;

        if ("conduit".equalsIgnoreCase(blueprint.id())) {
            List<String[]> layers = blueprint.layerSchematics();
            for (int ly = 0; ly < Math.min(5, layers.size()); ly++) {
                String[] rows = layers.get(ly);
                int worldY = centerPos.y() - halfY + ly;
                for (int row = 0; row < rows.length; row++) {
                    String line = rows[row];
                    int worldZ = centerPos.z() - halfZ + row;
                    for (int col = 0; col < line.length(); col++) {
                        int worldX = centerPos.x() - halfX + col;
                        char c = line.charAt(col);
                        BlockPos p = new BlockPos(worldX, worldY, worldZ);
                        if (c == '#') {
                            primitives.add(SpatialPrimitive.ghostBlock(p, "minecraft:prismarine", SpatialColor.BLUE.withAlpha(160), duration));
                        } else if (c == 'C') {
                            primitives.add(SpatialPrimitive.ghostBlock(p, "minecraft:conduit", SpatialColor.CYAN.withAlpha(220), duration));
                        }
                    }
                }
            }
        } else if (blueprint.id().startsWith("beacon")) {
            int layersCount = blueprint.heightY() - 1;
            for (int l = 0; l < layersCount; l++) {
                int radius = layersCount - l;
                int curY = centerPos.y() + l;
                for (int dx = -radius; dx <= radius; dx++) {
                    for (int dz = -radius; dz <= radius; dz++) {
                        primitives.add(SpatialPrimitive.ghostBlock(
                                new BlockPos(centerPos.x() + dx, curY, centerPos.z() + dz),
                                "minecraft:iron_block",
                                SpatialColor.YELLOW.withAlpha(140),
                                duration
                        ));
                    }
                }
            }
            primitives.add(SpatialPrimitive.ghostBlock(
                    new BlockPos(centerPos.x(), centerPos.y() + layersCount, centerPos.z()),
                    "minecraft:beacon",
                    SpatialColor.CYAN.withAlpha(220),
                    duration
            ));
        } else {
            BlockPos min = new BlockPos(centerPos.x() - halfX, centerPos.y(), centerPos.z() - halfZ);
            BlockPos max = new BlockPos(centerPos.x() + halfX, centerPos.y() + sizeY, centerPos.z() + halfZ);
            primitives.add(SpatialPrimitive.boxOutline(min, max, SpatialColor.BLUE, blueprint.name(), duration));
        }

        primitives.add(SpatialPrimitive.billboard(
                new BlockPos(centerPos.x(), centerPos.y() + sizeY + 1, centerPos.z()),
                "蓝图投影: " + blueprint.name(),
                SpatialColor.YELLOW,
                duration
        ));

        return SpatialDirectivePacket.of(
                "multiblock-" + blueprint.id() + "-" + System.currentTimeMillis(),
                "MULTIBLOCK_GHOST",
                primitives,
                "多方块蓝图全息投影: " + blueprint.name(),
                blueprint.coreActivationCondition()
        );
    }

    /**
     * Generates in-world spherical boundary rings for mob farm despawn zones.
     */
    public static SpatialDirectivePacket generateMobFarmOverlay(double playerX, double playerY, double playerZ) {
        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 400; // 20 seconds

        primitives.add(SpatialPrimitive.sphereBoundary(
                playerX, playerY, playerZ, 24.0,
                SpatialColor.RED.withAlpha(150),
                "0-24m: 绝对禁刷盲区 (No-Spawn Zone)",
                duration
        ));

        primitives.add(SpatialPrimitive.sphereBoundary(
                playerX, playerY, playerZ, 32.0,
                SpatialColor.GREEN.withAlpha(180),
                "24-32m: 黄金高频活动圈 (Active Golden Sphere)",
                duration
        ));

        primitives.add(SpatialPrimitive.sphereBoundary(
                playerX, playerY, playerZ, 128.0,
                SpatialColor.CYAN.withAlpha(120),
                "128m: 瞬间蒸发视界 (Instant Despawn Horizon)",
                duration
        ));

        BlockPos playerHead = new BlockPos((int) Math.floor(playerX), (int) Math.floor(playerY) + 2, (int) Math.floor(playerZ));
        primitives.add(SpatialPrimitive.billboard(
                playerHead,
                "生电刷怪动力学生成圈 (24m/32m/128m)",
                SpatialColor.GREEN,
                duration
        ));

        return SpatialDirectivePacket.of(
                "mobfarm-spheres-" + System.currentTimeMillis(),
                "MOB_FARM_SPHERES",
                primitives,
                "生电清除球与生成动力学视界",
                "红色=24m禁刷，绿色=32m黄金活动区，青色=128m瞬间清除界"
        );
    }

    /**
     * Generates portal 8:1 alignment visual guides.
     */
    public static SpatialDirectivePacket generatePortalAlignmentOverlay(
            int overworldX, int overworldZ,
            int currentNetherX, int currentNetherZ,
            int idealNetherX, int idealNetherZ
    ) {
        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 400;

        BlockPos curPos = new BlockPos(currentNetherX, 64, currentNetherZ);
        BlockPos idealPos = new BlockPos(idealNetherX, 64, idealNetherZ);

        primitives.add(SpatialPrimitive.boxOutline(curPos, SpatialColor.RED, "漂移下界门", duration));
        primitives.add(SpatialPrimitive.boxOutline(idealPos, SpatialColor.GREEN, "推荐对齐点 (8:1)", duration));

        if (!curPos.equals(idealPos)) {
            primitives.add(SpatialPrimitive.flowArrow(curPos, idealPos, SpatialColor.PURPLE, "迁址向量", duration));
        }

        primitives.add(SpatialPrimitive.billboard(
                idealPos.offset("up"),
                String.format("推荐下界门坐标 [%d, 64, %d]", idealNetherX, idealNetherZ),
                SpatialColor.GREEN,
                duration
        ));

        return SpatialDirectivePacket.of(
                "portal-align-" + System.currentTimeMillis(),
                "PORTAL_ALIGNMENT",
                primitives,
                "传送门 8:1 欧氏空间对齐引导",
                String.format("当前漂移下界门位于 [%d, %d]，建议迁至 [%d, %d] 消除串门风险",
                        currentNetherX, currentNetherZ, idealNetherX, idealNetherZ)
        );
    }

    /**
     * Generates in-world holographic overlays for Applied Energistics 2 (AE2) networks.
     */
    public static SpatialDirectivePacket generateAe2Overlay(LocalMachineCluster cluster, Ae2NetworkAnalyzer.Ae2Report report) {
        if (report == null || (report.totalControllers() == 0 && report.totalCables() == 0 && report.totalDevices() == 0)) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds

        for (BlockPos pos : report.illegalInteriorControllers()) {
            primitives.add(SpatialPrimitive.boxOutline(pos, SpatialColor.RED, "ILLEGAL INTERIOR", duration));
            primitives.add(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 控制器实心内部违规方块", SpatialColor.RED, duration));
        }

        for (BlockPos pos : report.overloadedCables()) {
            primitives.add(SpatialPrimitive.boxOutline(pos, SpatialColor.ORANGE, "CABLE OVERLOAD", duration));
            primitives.add(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 频道过载线缆", SpatialColor.ORANGE, duration));
        }

        for (BlockPos pos : report.offlineDevices()) {
            primitives.add(SpatialPrimitive.boxOutline(pos, SpatialColor.YELLOW, "MISSING CHANNEL", duration));
            primitives.add(SpatialPrimitive.ghostBlock(pos, "ae2:missing_channel", Map.of("state", "offline"), SpatialColor.YELLOW, duration));
            primitives.add(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 频道耗尽离线", SpatialColor.YELLOW, duration));
        }

        if (report.isHealthy() && report.totalDevices() > 0) {
            if (cluster != null && cluster.originBlock().isPresent()) {
                BlockPos org = cluster.origin();
                primitives.add(SpatialPrimitive.boxOutline(org, SpatialColor.CYAN, "AE2 OK", duration));
                primitives.add(SpatialPrimitive.billboard(org.offset("up"), String.format("✔ AE2 在线: %d台", report.onlineDevices()), SpatialColor.CYAN, duration));
            }
        }

        return SpatialDirectivePacket.of(
                "ae2-network-" + System.currentTimeMillis(),
                "AE2_NETWORK",
                primitives,
                report.primaryDiagnosis(),
                report.actionableRemediation()
        );
    }


    /**
     * Generates in-world holographic overlays for Minecraft Java Edition Piston,
     * Quasi-Connectivity (QC), BUD locks, and push limit overloads.
     */
    public static SpatialDirectivePacket generatePistonOverlay(LocalMachineCluster cluster, PistonRedstoneAnalyzer.PistonReport report) {
        if (report == null || "unknown".equals(report.pistonFacing())) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds
        BlockPos pPos = report.pistonPos();

        // 1. Highlight Piston itself
        if (report.isBudLocked()) {
            primitives.add(SpatialPrimitive.boxOutline(pPos, SpatialColor.YELLOW, "BUD LOCK", duration));
            primitives.add(SpatialPrimitive.billboard(pPos.offset("up"), "⚠ BUD 锁定：需方块更新复位", SpatialColor.YELLOW, duration));
        } else if (report.isBudPending()) {
            primitives.add(SpatialPrimitive.boxOutline(pPos, SpatialColor.CYAN, "BUD ARMED", duration));
            primitives.add(SpatialPrimitive.billboard(pPos.offset("up"), "ℹ BUD 待命：等待更新触发", SpatialColor.CYAN, duration));
        } else if (!report.isHealthy()) {
            primitives.add(SpatialPrimitive.boxOutline(pPos, SpatialColor.RED, "PISTON STALLED", duration));
        } else {
            primitives.add(SpatialPrimitive.boxOutline(pPos, SpatialColor.GREEN, "PISTON OK", duration));
        }

        // 2. Quasi-Connectivity (QC) sources: Cyan box outline and flow arrows to the piston
        for (BlockPos qp : report.qcPowerSources()) {
            primitives.add(SpatialPrimitive.boxOutline(qp, SpatialColor.CYAN, "QC POWER SOURCE", duration));
            primitives.add(SpatialPrimitive.flowArrow(qp, pPos, SpatialColor.CYAN, "QUASI-CONNECTIVITY (QC)", duration));
            primitives.add(SpatialPrimitive.billboard(qp.offset("up"), "⚡ 隔空准连接电源", SpatialColor.CYAN, duration));
        }

        // 3. Immovable obstacles: Purple box outlines
        for (BlockPos ip : report.immovableBlocks()) {
            primitives.add(SpatialPrimitive.boxOutline(ip, SpatialColor.PURPLE, "IMMOVABLE BLOCK", duration));
            primitives.add(SpatialPrimitive.billboard(ip.offset("up"), "✖ 不可推动障碍", SpatialColor.PURPLE, duration));
        }

        // 4. Push chain and push limit overloads
        if (report.isPushLimitExceeded()) {
            for (int i = 0; i < report.pushChain().size(); i++) {
                BlockPos bPos = report.pushChain().get(i);
                if (i >= 12) {
                    primitives.add(SpatialPrimitive.boxOutline(bPos, SpatialColor.RED, "PUSH LIMIT (MAX 12)", duration));
                    primitives.add(SpatialPrimitive.billboard(bPos.offset("up"), String.format("✖ 超载方块 (#%d)", i + 1), SpatialColor.RED, duration));
                } else {
                    primitives.add(SpatialPrimitive.boxOutline(bPos, SpatialColor.ORANGE, String.format("BLOCK #%d", i + 1), duration));
                }
            }
        }

        return SpatialDirectivePacket.of(
                "piston-dynamics-" + System.currentTimeMillis(),
                "PISTON_DYNAMICS",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    /**
     * Generates in-world holographic overlays for Minecraft Redstone Comparators,
     * container fullness, item sorter crosstalk hazards, and overflow protection.
     */
    public static SpatialDirectivePacket generateComparatorOverlay(LocalMachineCluster cluster, ComparatorRedstoneAnalyzer.ComparatorReport report) {
        if (report == null || "none".equals(report.containerType()) && report.outputSignal() == 0 && report.redstoneWireLength() == 0 && !report.isSubtractMode()) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds
        BlockPos cPos = report.comparatorPos();

        // 1. Comparator outline
        if (report.hasCrosstalkRisk() || report.hasUnstackablePollution()) {
            primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.RED, "COMPARATOR HAZARD", duration));
            primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), String.format("⚡ 比较器告警 (信号: %d)", report.outputSignal()), SpatialColor.RED, duration));
        } else if (report.isSubtractMode()) {
            primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.PURPLE, "SUBTRACT MODE", duration));
            primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), String.format("➖ 减法模式 (输出: %d)", report.outputSignal()), SpatialColor.PURPLE, duration));
        } else {
            primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.YELLOW, "COMPARATOR", duration));
            primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), String.format("⚡ 比较模式 (信号: %d)", report.outputSignal()), SpatialColor.YELLOW, duration));
        }

        // 2. Bound container
        if (!"none".equals(report.containerType())) {
            BlockPos contPos = report.containerPos();
            if (report.hasUnstackablePollution()) {
                primitives.add(SpatialPrimitive.boxOutline(contPos, SpatialColor.PURPLE, "POLLUTED CONTAINER", duration));
                primitives.add(SpatialPrimitive.billboard(contPos.offset("up"), "✖ 槽位污染：不可堆叠物品", SpatialColor.PURPLE, duration));
            } else {
                primitives.add(SpatialPrimitive.boxOutline(contPos, SpatialColor.CYAN, "CONTAINER", duration));
                primitives.add(SpatialPrimitive.billboard(contPos.offset("up"), String.format("📦 容器负载: %d 物品", report.filledItemCount()), SpatialColor.CYAN, duration));
            }
        }

        // 3. Redstone wire chain
        if (!report.redstoneWireChain().isEmpty()) {
            for (int i = 0; i < report.redstoneWireChain().size(); i++) {
                BlockPos wPos = report.redstoneWireChain().get(i);
                if (report.hasCrosstalkRisk()) {
                    primitives.add(SpatialPrimitive.boxOutline(wPos, SpatialColor.RED, "CROSSTALK WIRE", duration));
                } else if (report.isOverflowProtected()) {
                    primitives.add(SpatialPrimitive.boxOutline(wPos, SpatialColor.GREEN, String.format("WIRE #%d", i + 1), duration));
                } else {
                    primitives.add(SpatialPrimitive.boxOutline(wPos, SpatialColor.ORANGE, String.format("WIRE #%d", i + 1), duration));
                }
            }
        }

        // 4. Crosstalk leakage targets
        for (BlockPos leakTarget : report.crosstalkLeakTargets()) {
            primitives.add(SpatialPrimitive.boxOutline(leakTarget, SpatialColor.RED, "CROSSTALK LEAK TARGET", duration));
            primitives.add(SpatialPrimitive.flowArrow(cPos, leakTarget, SpatialColor.RED, "CROSSTALK LEAK", duration));
            primitives.add(SpatialPrimitive.billboard(leakTarget.offset("up"), "⚠ 串扰信号泄漏毁损", SpatialColor.RED, duration));
        }

        return SpatialDirectivePacket.of(
                "comparator-dynamics-" + System.currentTimeMillis(),
                "COMPARATOR_DYNAMICS",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    /**
     * Generates in-world holographic overlays for redstone transmission, torch burnout, and powering blockades.
     */
    public static SpatialDirectivePacket generateTransmissionOverlay(
            LocalMachineCluster cluster,
            RedstoneTransmissionAnalyzer.TransmissionReport report
    ) {
        if (report == null) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds
        BlockPos tPos = report.targetPos();

        // 1. Target block bounding box and state
        if (report.hasTorchBurnout()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.RED, "TORCH BURNOUT HAZARD", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), String.format("⚡ 烧毁高危 (信号: %d)", report.signalStrength()), SpatialColor.RED, duration));
        } else if (report.hasWeakPowerBlockade()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.ORANGE, "WEAK POWER BLOCKADE", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "✖ 弱充能阻断点", SpatialColor.ORANGE, duration));
        } else if (report.hasWireRedirectionDisconnection()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.YELLOW, "WIRE REDIRECTED", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "↷ 偏转断路线路", SpatialColor.YELLOW, duration));
        } else if (report.hasObserverLoop()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.CYAN, "OBSERVER LOOP", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "⟳ 侦测器自激时钟", SpatialColor.CYAN, duration));
        } else {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.GREEN, "HEALTHY TRANSMISSION", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), String.format("✓ 传输正常 (信号: %d)", report.signalStrength()), SpatialColor.GREEN, duration));
        }

        // 2. Burnout torches
        for (BlockPos bPos : report.burnoutTorches()) {
            primitives.add(SpatialPrimitive.boxOutline(bPos, SpatialColor.RED, "BURNOUT TORCH", duration));
            primitives.add(SpatialPrimitive.billboard(bPos.offset("up"), "⚠ 火把自激烧毁高危", SpatialColor.RED, duration));
        }

        // 3. Weak power blockades
        for (BlockPos wPos : report.weakPowerBlockades()) {
            primitives.add(SpatialPrimitive.boxOutline(wPos, SpatialColor.ORANGE, "WEAK POWER", duration));
            primitives.add(SpatialPrimitive.billboard(wPos.offset("up"), "✖ 弱充能：火把不熄灭/导线不供电", SpatialColor.ORANGE, duration));
        }

        // 4. Redirected wires
        for (BlockPos rPos : report.redirectedWires()) {
            primitives.add(SpatialPrimitive.boxOutline(rPos, SpatialColor.YELLOW, "REDIRECTED WIRE", duration));
            primitives.add(SpatialPrimitive.flowArrow(rPos, tPos, SpatialColor.YELLOW, "REDIRECTED DISCONNECTED", duration));
            primitives.add(SpatialPrimitive.billboard(rPos.offset("up"), "↷ 导线偏转脱离目标", SpatialColor.YELLOW, duration));
        }

        // 5. Observer loops
        for (BlockPos oPos : report.observerLoops()) {
            primitives.add(SpatialPrimitive.boxOutline(oPos, SpatialColor.CYAN, "OBSERVER OSCILLATION", duration));
            primitives.add(SpatialPrimitive.billboard(oPos.offset("up"), "⟳ 1-Clock 自激震荡", SpatialColor.CYAN, duration));
        }

        return SpatialDirectivePacket.of(
                "redstone-transmission-" + System.currentTimeMillis(),
                "REDSTONE_TRANSMISSION",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    /**
     * Generates in-world holographic overlays for redstone logic, latches, flip-flops, and gates.
     */
    public static SpatialDirectivePacket generateLogicOverlay(
            LocalMachineCluster cluster,
            RedstoneLogicAnalyzer.LogicReport report
    ) {
        if (report == null) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300; // 15 seconds
        BlockPos tPos = report.targetPos();

        // 1. Target block bounding box and state
        if (report.hasRaceConflict()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.RED, "LATCH RACE CONFLICT", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "⚠ 锁存器竞争冲突 (S=1, R=1)", SpatialColor.RED, duration));
        } else if (report.hasPulseWidthMismatch()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.YELLOW, "PULSE WIDTH MISMATCH", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "⚠ 脉冲>2gt 活塞无法吐方块", SpatialColor.YELLOW, duration));
        } else if (report.hasBulbLock()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.ORANGE, "BULB LOCKED", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "💡 铜球未断电锁定", SpatialColor.ORANGE, duration));
        } else if (report.hasGlitchRisk()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.YELLOW, "GATE GLITCH RISK", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "↷ 门电路延时毛刺高危", SpatialColor.YELLOW, duration));
        } else {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.GREEN, "LOGIC HEALTHY", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), String.format("✓ 逻辑正常 (输出: %s)", report.outputState() ? "ON" : "OFF"), SpatialColor.GREEN, duration));
        }

        // 2. Conflict nodes
        for (BlockPos cPos : report.conflictNodes()) {
            primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.RED, "CONFLICT NODE", duration));
            primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "✖ 冲突节点", SpatialColor.RED, duration));
        }

        // 3. Active outputs
        for (BlockPos aPos : report.activeOutputs()) {
            primitives.add(SpatialPrimitive.boxOutline(aPos, SpatialColor.CYAN, "ACTIVE OUTPUT", duration));
            primitives.add(SpatialPrimitive.billboard(aPos.offset("up"), "⚡ 激活输出 Q=1", SpatialColor.CYAN, duration));
        }

        // 4. Logic components
        for (BlockPos lPos : report.logicComponents()) {
            if (!lPos.equals(tPos) && !report.conflictNodes().contains(lPos)) {
                primitives.add(SpatialPrimitive.boxOutline(lPos, SpatialColor.BLUE, "LOGIC COMPONENT", duration));
            }
        }

        return SpatialDirectivePacket.of(
                "redstone-logic-" + System.currentTimeMillis(),
                "REDSTONE_LOGIC",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    /**
     * Generate 3D spatial holographic diagnostic overlay for Minecart & Rail Networks (v2.8.0).
     */
    public static SpatialDirectivePacket generateRailOverlay(LocalMachineCluster cluster, RailNetworkAnalyzer.RailReport report) {
        if (report == null) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300;
        BlockPos tPos = report.targetPos();

        // 1. Missing Backstop
        if (report.hasMissingBackstop()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.RED, "MISSING BACKSTOP", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "✖ 站台缺失挡板：静止矿车无法起动", SpatialColor.RED, duration));
            for (BlockPos gPos : report.ghostBlockPlacements()) {
                primitives.add(SpatialPrimitive.ghostBlock(gPos, "minecraft:stone", SpatialColor.CYAN, duration));
                primitives.add(SpatialPrimitive.billboard(gPos.offset("up"), "➕ 补全坚固挡板", SpatialColor.CYAN, duration));
            }
        }

        // 2. Slope Stall Risk
        if (report.hasSlopeStallRisk()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.YELLOW, "SLOPE STALL RISK", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "⚠ 坡道动力不足：普通铁轨连续≥2格", SpatialColor.YELLOW, duration));
            }
        }

        // 3. Activator Lockout
        if (report.hasActivatorLockout()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.PURPLE, "ACTIVATOR LOCKOUT", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "⚠ 激活铁轨导致漏斗矿车停止吸物", SpatialColor.PURPLE, duration));
            }
        }

        // 4. Unloader Glitch Risk
        if (report.hasUnloaderGlitchRisk()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.ORANGE, "UNLOADER GLITCH RISK", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "↷ 卸货站无延时滤波", SpatialColor.ORANGE, duration));
            }
        }

        // 5. Healthy rail components
        if (report.isHealthy()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.GREEN, "RAIL HEALTHY", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "✔ 铁轨动力/站台配置健康", SpatialColor.GREEN, duration));
        }

        // 6. Other rail components
        for (BlockPos rPos : report.railComponents()) {
            if (!rPos.equals(tPos) && !report.conflictNodes().contains(rPos)) {
                primitives.add(SpatialPrimitive.boxOutline(rPos, SpatialColor.BLUE, "RAIL COMPONENT", duration));
            }
        }

        return SpatialDirectivePacket.of(
                "rail-network-" + System.currentTimeMillis(),
                "RAIL_NETWORK",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }

    public static SpatialDirectivePacket generateWaterOverlay(LocalMachineCluster cluster, WaterLogisticsAnalyzer.WaterReport report) {
        if (report == null || cluster == null) {
            return SpatialDirectivePacket.empty();
        }

        List<SpatialPrimitive> primitives = new ArrayList<>();
        int duration = 300;
        BlockPos tPos = report.targetPos();

        // 1. Broken Bubble Column
        if (report.hasBrokenBubbleColumn()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.RED, "BROKEN BUBBLE COLUMN", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "✖ 气泡柱中断：此处为流动水而非水源", SpatialColor.RED, duration));
            }
            for (BlockPos gPos : report.ghostBlockPlacements()) {
                primitives.add(SpatialPrimitive.ghostBlock(gPos, "minecraft:kelp", SpatialColor.CYAN, duration));
                primitives.add(SpatialPrimitive.billboard(gPos.offset("up"), "➕ 种植海带转化为水源", SpatialColor.CYAN, duration));
            }
        }

        // 2. Top Spill Deflector
        if (report.hasTopSpillRisk()) {
            for (BlockPos gPos : report.ghostBlockPlacements()) {
                primitives.add(SpatialPrimitive.boxOutline(gPos, SpatialColor.YELLOW, "TOP SPILL DEFLECTOR", duration));
                primitives.add(SpatialPrimitive.ghostBlock(gPos, "minecraft:smooth_stone_slab", SpatialColor.YELLOW, duration));
                primitives.add(SpatialPrimitive.billboard(gPos.offset("up"), "⚠ 补全导流顶盖防飞溅", SpatialColor.YELLOW, duration));
            }
        }

        // 3. Flow Stall Risk
        if (report.hasFlowStallRisk()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.ORANGE, "FLOW STALL RISK", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "⚠ 水流动力衰竭：超出8格流动极限", SpatialColor.ORANGE, duration));
            }
        }

        // 4. Misaligned Item Stream
        if (report.hasMisalignedStream()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.PURPLE, "MISALIGNED ITEM STREAM", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "⚠ 物品未对齐：双漏斗无法满速吞吐", SpatialColor.PURPLE, duration));
            }
            for (BlockPos gPos : report.ghostBlockPlacements()) {
                primitives.add(SpatialPrimitive.ghostBlock(gPos, "minecraft:honey_block", SpatialColor.GREEN, duration));
                primitives.add(SpatialPrimitive.billboard(gPos.offset("up"), "➕ 放置蜂蜜块对齐双漏斗", SpatialColor.GREEN, duration));
            }
        }

        // 5. Despawn Vortex Risk
        if (report.hasDespawnVortexRisk()) {
            for (BlockPos cPos : report.conflictNodes()) {
                primitives.add(SpatialPrimitive.boxOutline(cPos, SpatialColor.RED, "DESPAWN VORTEX RISK", duration));
                primitives.add(SpatialPrimitive.billboard(cPos.offset("up"), "✖ 涡流对冲死角：物品将滞留5分钟后清除", SpatialColor.RED, duration));
            }
        }

        // 6. Healthy water components
        if (report.isHealthy()) {
            primitives.add(SpatialPrimitive.boxOutline(tPos, SpatialColor.GREEN, "WATER LOGISTICS HEALTHY", duration));
            primitives.add(SpatialPrimitive.billboard(tPos.offset("up"), "✔ 水流/气泡柱物流动力健康", SpatialColor.GREEN, duration));
        }

        // 7. Water components
        for (BlockPos wPos : report.waterComponents()) {
            if (!wPos.equals(tPos) && !report.conflictNodes().contains(wPos)) {
                primitives.add(SpatialPrimitive.boxOutline(wPos, SpatialColor.BLUE, "WATER STREAM", duration));
            }
        }

        return SpatialDirectivePacket.of(
                "water-logistics-" + System.currentTimeMillis(),
                "WATER_LOGISTICS",
                primitives,
                report.primaryDiagnosis(),
                report.actionableAdvice()
        );
    }
}
