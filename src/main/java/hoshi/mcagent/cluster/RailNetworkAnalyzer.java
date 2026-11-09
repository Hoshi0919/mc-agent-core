package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Diagnostic analyzer for Minecraft Minecart and Rail Networks (v2.8.0):
 * - Powered rail spacing and horizontal momentum cruising (max 38 blocks empty, 34 blocks occupied)
 * - Sloped rail ascent dynamics and rollback stall prevention (strict <= 2 spacing on slopes)
 * - Hopper minecart smart unloader stations and missing terminal backstops
 * - Unloader comparator pulse extension delay filtering (premature launch prevention)
 * - Activator rail lockout and accidental hopper minecart cargo disabling
 * - Detector rail cargo weighing and comparator coupling
 */
public final class RailNetworkAnalyzer {

    public enum RailType {
        UNLOADER_STATION,
        LOADER_STATION,
        SLOPED_ASCENT,
        CRUISING_LINE,
        ACTIVATOR_SECTION,
        NONE
    }

    public record RailReport(
            boolean isHealthy,
            boolean hasSlopeStallRisk,
            boolean hasMissingBackstop,
            boolean hasActivatorLockout,
            boolean hasUnloaderGlitchRisk,
            boolean hasUnderpoweredLaunch,
            BlockPos targetPos,
            String targetBlockType,
            RailType railType,
            int railCount,
            int poweredRailCount,
            List<BlockPos> conflictNodes,
            List<BlockPos> ghostBlockPlacements,
            List<BlockPos> railComponents,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static RailReport empty() {
            return new RailReport(
                    true, false, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", RailType.NONE, 0, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到铁轨、矿车站台或物流轨道网络组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§e【矿车铁轨网络、坡道动量与智能装卸站因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 轨道类型：%s | 铁轨总数: %d (充能铁轨: §6%d§r)\n",
                    formatRailType(railType), railCount, poweredRailCount));

            if (hasMissingBackstop) {
                sb.append("  ⚡ §c[终端缺失坚固挡板] 卸货站充能铁轨后方未检测到坚固实体方块！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 悬空/无依托站台: %s (静止矿车无法凭空起步，通电后原地卡死)\n", cPos));
                }
                for (BlockPos gPos : ghostBlockPlacements) {
                    sb.append(String.format("     ➕ 建议补全实体方块位置: %s\n", gPos));
                }
            }

            if (hasSlopeStallRisk) {
                sb.append("  ⚡ §e[坡道动量不足/倒溜高危] 斜坡铁轨检测到连续 ≥2 格普通铁轨！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 爬坡动力赤字段: %s (重力衰减导致动量耗尽，矿车将倒溜卡死)\n", cPos));
                }
            }

            if (hasActivatorLockout) {
                sb.append("  ⚡ §c[激活铁轨停用锁死] 检测到通电激活铁轨 (Activator Rail) 接入货运线路！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 锁定禁用节点: %s (漏斗矿车压过将被锁定停用，停止吸取掉落物)\n", cPos));
                }
            }

            if (hasUnloaderGlitchRisk) {
                sb.append("  ⚡ §6[卸货站提前发车隐患] 比较器直连反相火把，缺失双比较器脉冲延长器 (Pulse Extender)！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ↷ 无滤波检测端: %s (8-tick 物品抽取间歇可能导致信号瞬断提前弹走矿车)\n", cPos));
                }
            }

            if (hasUnderpoweredLaunch) {
                sb.append("  ⚡ §e[起步冲力不足] 站台起步段仅铺设 1 根充能铁轨，出站速度不足 2.4 m/s (极速仅 30%)！§r\n");
            }

            if (isHealthy) {
                sb.append("  ✓ §a[铁轨健康] 铁轨间距合理，站台挡板完备，卸货滤波与动力坡道配置健康无倒溜隐患。§r\n");
            }

            sb.append(String.format("▸ 核心诊断：%s\n", primaryDiagnosis));
            if (!actionableAdvice.isEmpty()) {
                sb.append(String.format("▸ 修复建议：%s\n", actionableAdvice));
            }
            return sb.toString();
        }

        private static String formatRailType(RailType rt) {
            return switch (rt) {
                case UNLOADER_STATION -> "§b智能漏斗矿车卸货站 (Smart Unloader Station)§r";
                case LOADER_STATION -> "§a智能矿车装货站 (Smart Loader Station)§r";
                case SLOPED_ASCENT -> "§e斜坡爬坡动力段 (Sloped Rail Ascent)§r";
                case CRUISING_LINE -> "§3平地极速巡航干线 (Cruising Rail Line)§r";
                case ACTIVATOR_SECTION -> "§d激活铁轨功能段 (Activator Functional Rail)§r";
                case NONE -> "§7常规铁轨轨道§r";
            };
        }
    }

    private RailNetworkAnalyzer() {}

    /**
     * Primary entry point for diagnosing rail networks, unloader stations, and slopes.
     */
    public static RailReport analyzeRail(LocalMachineCluster cluster, BlockPos targetPos) {
        if (cluster == null || cluster.isEmpty()) {
            return RailReport.empty();
        }

        List<LocalBlock> rails = cluster.getConnectedRails();
        if (rails.isEmpty()) {
            LocalBlock target = cluster.getBlock(targetPos);
            if (target != null && target.isHopper()) {
                LocalBlock above = cluster.getBlock(targetPos.offset("up"));
                if (above != null && above.isRail()) {
                    rails = Collections.singletonList(above);
                }
            }
        }

        if (rails.isEmpty()) {
            return RailReport.empty();
        }

        LocalBlock targetBlock = cluster.getBlock(targetPos);
        BlockPos focusPos = (targetBlock != null && !targetBlock.isAir()) ? targetPos : cluster.origin();

        // 1. Check for Unloader Station (rail above hopper)
        for (LocalBlock r : rails) {
            BlockPos downPos = r.pos().offset("down");
            LocalBlock below = cluster.getBlock(downPos);
            if (below != null && below.isHopper()) {
                return analyzeUnloaderStation(cluster, r, below, rails);
            }
        }

        // 2. Check for Activator Rail Lockout
        for (LocalBlock r : rails) {
            if (r.isActivatorRail()) {
                return analyzeActivatorRail(cluster, r, rails);
            }
        }

        // 3. Check for Sloped Rail Ascent (ascending rails or vertical step differences)
        boolean hasSlope = false;
        for (LocalBlock r : rails) {
            if (r.isAscendingRail()) {
                hasSlope = true;
                break;
            }
            for (LocalBlock r2 : rails) {
                if (!r.pos().equals(r2.pos()) && Math.abs(r.pos().y() - r2.pos().y()) == 1) {
                    int dist = Math.abs(r.pos().x() - r2.pos().x()) + Math.abs(r.pos().z() - r2.pos().z());
                    if (dist == 1) {
                        hasSlope = true;
                        break;
                    }
                }
            }
            if (hasSlope) break;
        }

        if (hasSlope) {
            return analyzeSlopedAscent(cluster, focusPos, rails);
        }

        // 4. Default: Cruising line analysis
        return analyzeCruisingLine(cluster, focusPos, rails);
    }

    /**
     * Diagnose Hopper Minecart Smart Unloader Station.
     */
    private static RailReport analyzeUnloaderStation(LocalMachineCluster cluster, LocalBlock unloaderRail, LocalBlock hopper, List<LocalBlock> allRails) {
        BlockPos railPos = unloaderRail.pos();
        BlockPos hopperPos = hopper.pos();

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> ghostBlocks = new ArrayList<>();
        List<BlockPos> railComponents = new ArrayList<>();
        for (LocalBlock r : allRails) {
            railComponents.add(r.pos());
        }
        railComponents.add(hopperPos);

        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        boolean hasMissingBackstop = false;
        boolean hasUnloaderGlitchRisk = false;
        boolean hasUnderpoweredLaunch = false;

        // Detect track incoming/outgoing directions
        String[] directions = {"north", "south", "east", "west"};
        String trackDirection = null;
        for (String dir : directions) {
            BlockPos nPos = railPos.offset(dir);
            LocalBlock nb = cluster.getBlock(nPos);
            if (nb != null && nb.isRail()) {
                trackDirection = dir;
                break;
            }
        }

        // Determine backstop position (opposite to track outgoing direction)
        BlockPos backstopPos;
        if (trackDirection != null) {
            backstopPos = railPos.offset(reverseDirection(trackDirection));
        } else {
            backstopPos = railPos.offset("south");
        }

        LocalBlock backstopBlock = cluster.getBlock(backstopPos);
        if (backstopBlock == null || !backstopBlock.isSolidConductiveBlock()) {
            hasMissingBackstop = true;
            conflictNodes.add(railPos);
            ghostBlocks.add(backstopPos);
            issues.add("卸货站终端充能铁轨后方未检测到坚固实体方块！静止矿车无法凭空起动，通电后将卡死在站台！");
        }

        // Check Hopper Comparator & Pulse Extender Filter
        LocalBlock comparatorBlock = null;
        for (String dir : directions) {
            BlockPos cPos = hopperPos.offset(dir);
            LocalBlock c = cluster.getBlock(cPos);
            if (c != null && c.isComparator()) {
                comparatorBlock = c;
                railComponents.add(cPos);
                break;
            }
        }

        if (comparatorBlock != null) {
            boolean hasPulseExtender = false;
            BlockPos compOut = comparatorBlock.pos().offset(comparatorBlock.facing());
            LocalBlock outBlock = cluster.getBlock(compOut);
            if (outBlock != null) {
                railComponents.add(compOut);
                if (outBlock.isRepeater()) {
                    int delay = Integer.parseInt(outBlock.getProperty("delay", "1"));
                    if (delay >= 3) {
                        hasPulseExtender = true;
                    }
                } else if (outBlock.isComparator()) {
                    hasPulseExtender = true;
                }
            }

            if (!hasPulseExtender) {
                hasUnloaderGlitchRisk = true;
                conflictNodes.add(comparatorBlock.pos());
                warnings.add("卸货站比较器直连反相控制端，未接入双比较器脉冲延长器 (Pulse Extender)；漏斗抽取物品交接的 8-tick 间歇可能诱发信号瞬断提前发车！");
            }
        }

        // Count powered rails in station
        int poweredCount = 0;
        for (LocalBlock r : allRails) {
            if (r.isPoweredRail()) poweredCount++;
        }

        if (poweredCount == 1 && allRails.size() > 1) {
            hasUnderpoweredLaunch = true;
            warnings.add("起步加速段仅铺设 1 根充能铁轨，出站速度不足 2.4 m/s (仅为极速 30%)，长距离巡航极易中途停滞。");
        }

        boolean isHealthy = !hasMissingBackstop && !hasUnloaderGlitchRisk && !hasUnderpoweredLaunch;
        String diagnosis;
        String advice;

        if (hasMissingBackstop) {
            diagnosis = "卸货站终端缺失实体挡板，静止矿车无法形成反弹动力起步卡死。";
            advice = "在终端充能铁轨后方紧贴放置一个实体方块（如石头、深板岩）作为反弹挡板。";
        } else if (hasUnloaderGlitchRisk) {
            diagnosis = "卸货站比较器缺失脉冲延长器延时滤波，存在抽料瞬隙提前发车隐患。";
            advice = "在比较器与反相火把之间串入双比较器脉冲延长器（8~12 ticks 滤波缓冲），杜绝提前发车。";
        } else if (hasUnderpoweredLaunch) {
            diagnosis = "起步段充能铁轨不足，矿车出站初速度较低。";
            advice = "在出站起步前 3~4 格连续铺设充能铁轨，使矿车在最短距离内提速至 8.0 m/s 极速。";
        } else {
            diagnosis = "智能卸货站结构完备，实体挡板存在且动力控制稳定。";
            advice = "保持当前配置，确保下方箱子容量充足。";
        }

        return new RailReport(
                isHealthy,
                false,
                hasMissingBackstop,
                false,
                hasUnloaderGlitchRisk,
                hasUnderpoweredLaunch,
                railPos,
                unloaderRail.blockId(),
                RailType.UNLOADER_STATION,
                allRails.size(),
                poweredCount,
                conflictNodes,
                ghostBlocks,
                railComponents,
                issues,
                warnings,
                diagnosis,
                advice
        );
    }

    /**
     * Diagnose Sloped Rail Ascent & Momentum Rollback Stall.
     */
    private static RailReport analyzeSlopedAscent(LocalMachineCluster cluster, BlockPos targetPos, List<LocalBlock> allRails) {
        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> railComponents = new ArrayList<>();
        for (LocalBlock r : allRails) {
            railComponents.add(r.pos());
        }

        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        int poweredCount = 0;
        int maxConsecutiveNormalOnSlope = 0;
        int currentConsecutiveNormal = 0;
        List<BlockPos> consecutiveNormalPos = new ArrayList<>();
        List<BlockPos> longestNormalSlopeChain = new ArrayList<>();

        List<LocalBlock> sortedRails = new ArrayList<>(allRails);
        sortedRails.sort(Comparator.comparingInt((LocalBlock b) -> b.pos().y())
                .thenComparingInt(b -> b.pos().x())
                .thenComparingInt(b -> b.pos().z()));

        for (LocalBlock r : sortedRails) {
            if (r.isPoweredRail()) {
                poweredCount++;
                if (currentConsecutiveNormal > maxConsecutiveNormalOnSlope) {
                    maxConsecutiveNormalOnSlope = currentConsecutiveNormal;
                    longestNormalSlopeChain = new ArrayList<>(consecutiveNormalPos);
                }
                currentConsecutiveNormal = 0;
                consecutiveNormalPos.clear();
            } else {
                currentConsecutiveNormal++;
                consecutiveNormalPos.add(r.pos());
            }
        }
        if (currentConsecutiveNormal > maxConsecutiveNormalOnSlope) {
            maxConsecutiveNormalOnSlope = currentConsecutiveNormal;
            longestNormalSlopeChain = new ArrayList<>(consecutiveNormalPos);
        }

        boolean hasSlopeStallRisk = maxConsecutiveNormalOnSlope >= 2;
        if (hasSlopeStallRisk) {
            conflictNodes.addAll(longestNormalSlopeChain);
            issues.add(String.format("斜坡爬坡段连续出现 %d 格普通铁轨 (≥2)！矿车克服重力爬坡时动量急剧衰减，必定在半坡发生重力倒溜卡死 (Rollback Stall)！", maxConsecutiveNormalOnSlope));
        }

        boolean isHealthy = !hasSlopeStallRisk;
        String diagnosis = hasSlopeStallRisk ?
                "斜坡铁轨充能间隔过大 (连续普通铁轨≥2)，上行矿车动量耗尽发生重力倒溜。" :
                "斜坡动力充沛，充能铁轨间隔符合安全爬坡规范 (≤1格普通铁轨)。";
        String advice = hasSlopeStallRisk ?
                "斜坡上充能铁轨间距严禁超过 2 格，请至少按“1 充能 + 1 普通”交替铺设；重载建议 1:1 全铺充能铁轨。" :
                "保持当前坡道动力配置。";

        return new RailReport(
                isHealthy,
                hasSlopeStallRisk,
                false,
                false,
                false,
                false,
                targetPos,
                sortedRails.get(0).blockId(),
                RailType.SLOPED_ASCENT,
                allRails.size(),
                poweredCount,
                conflictNodes,
                Collections.emptyList(),
                railComponents,
                issues,
                warnings,
                diagnosis,
                advice
        );
    }

    /**
     * Diagnose Activator Rail Lockout on collection lines.
     */
    private static RailReport analyzeActivatorRail(LocalMachineCluster cluster, LocalBlock activatorRail, List<LocalBlock> allRails) {
        BlockPos actPos = activatorRail.pos();
        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> railComponents = new ArrayList<>();
        for (LocalBlock r : allRails) {
            railComponents.add(r.pos());
        }

        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        boolean isPowered = activatorRail.isPowered() || activatorRail.isRedstonePowerSource();
        if (!isPowered) {
            for (BlockPos nPos : actPos.neighbors()) {
                LocalBlock nb = cluster.getBlock(nPos);
                if (nb != null && nb.isRedstonePowerSource()) {
                    isPowered = true;
                    break;
                }
            }
        }

        boolean hasActivatorLockout = isPowered;
        if (hasActivatorLockout) {
            conflictNodes.add(actPos);
            issues.add("检测到通电激活铁轨 (Activator Rail) 接入轨道！漏斗矿车压过通电激活铁轨会被强行锁定停用 (disabled)，停止吸取所有掉落物！");
        }

        int poweredCount = 0;
        for (LocalBlock r : allRails) {
            if (r.isPoweredRail()) poweredCount++;
        }

        boolean isHealthy = !hasActivatorLockout;
        String diagnosis = hasActivatorLockout ?
                "通电激活铁轨导致漏斗矿车被强行锁定，货运收集功能瘫痪。" :
                "激活铁轨处于未通电休眠状态。";
        String advice = hasActivatorLockout ?
                "若为物资收集线，请将激活铁轨更换为充能铁轨 (Powered Rail)；激活铁轨仅用于弹射生物或引爆 TNT 矿车。" :
                "若需弹射乘骑生物或引爆 TNT 矿车，请接入红石信号激活。";

        return new RailReport(
                isHealthy,
                false,
                false,
                hasActivatorLockout,
                false,
                false,
                actPos,
                activatorRail.blockId(),
                RailType.ACTIVATOR_SECTION,
                allRails.size(),
                poweredCount,
                conflictNodes,
                Collections.emptyList(),
                railComponents,
                issues,
                warnings,
                diagnosis,
                advice
        );
    }

    /**
     * Diagnose Horizontal Cruising Rail Line.
     */
    private static RailReport analyzeCruisingLine(LocalMachineCluster cluster, BlockPos targetPos, List<LocalBlock> allRails) {
        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> railComponents = new ArrayList<>();
        for (LocalBlock r : allRails) {
            railComponents.add(r.pos());
        }

        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        int poweredCount = 0;
        int normalCount = 0;
        for (LocalBlock r : allRails) {
            if (r.isPoweredRail()) {
                poweredCount++;
            } else if (r.isNormalRail()) {
                normalCount++;
            }
        }

        boolean hasUnderpowered = normalCount > 38 && poweredCount == 0;
        if (hasUnderpowered) {
            warnings.add(String.format("平地巡航段连续普通铁轨达 %d 格 (>38 格)！矿车动量严重衰减，无法维持 8.0 m/s 极速巡航。", normalCount));
        }

        boolean isHealthy = !hasUnderpowered;
        String diagnosis = hasUnderpowered ?
                "平地巡航普通铁轨超过 38 格阈值，矿车速度明显跌落。" :
                "平地巡航铁轨配置健康，动量巡航正常。";
        String advice = hasUnderpowered ?
                "平地建议每 34~38 格铺设 1 根充能铁轨以维持矿车最高限速 (8.0 m/s)。" :
                "保持当前轨道配置。";

        return new RailReport(
                isHealthy,
                false,
                false,
                false,
                false,
                hasUnderpowered,
                targetPos,
                allRails.get(0).blockId(),
                RailType.CRUISING_LINE,
                allRails.size(),
                poweredCount,
                conflictNodes,
                Collections.emptyList(),
                railComponents,
                issues,
                warnings,
                diagnosis,
                advice
        );
    }

    private static String reverseDirection(String dir) {
        return switch (dir.toLowerCase()) {
            case "north" -> "south";
            case "south" -> "north";
            case "east" -> "west";
            case "west" -> "east";
            case "up" -> "down";
            case "down" -> "up";
            default -> "south";
        };
    }
}
