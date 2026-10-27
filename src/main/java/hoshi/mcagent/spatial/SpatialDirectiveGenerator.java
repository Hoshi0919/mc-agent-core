package hoshi.mcagent.spatial;

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
}
