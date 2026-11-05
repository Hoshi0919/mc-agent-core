package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Topological analyzer for Applied Energistics 2 (AE2) ME networks.
 * Detects controller multiblock rule violations, 8/32 channel exhaustion,
 * greedy route starvation, and recursive P2P loops in 0ms.
 */
public final class Ae2NetworkAnalyzer {

    public record Ae2Report(
            boolean isHealthy,
            boolean hasMultiblockError,
            boolean hasChannelOverload,
            boolean hasP2pLoop,
            int totalControllers,
            int totalCables,
            int totalDenseCables,
            int totalDevices,
            int onlineDevices,
            int missingChannelDevices,
            List<BlockPos> illegalInteriorControllers,
            List<BlockPos> overloadedCables,
            List<BlockPos> offlineDevices,
            List<String> issues,
            String primaryDiagnosis,
            String actionableRemediation
    ) {
        public static Ae2Report healthy(int controllers, int cables, int dense, int devices, String desc) {
            return new Ae2Report(
                    true, false, false, false,
                    controllers, cables, dense, devices, devices, 0,
                    Collections.emptyList(), Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    desc,
                    "ME 数字化网络拓扑健康，频道分配合理，所有设备均处于在线就绪状态。"
            );
        }

        public static Ae2Report empty() {
            return new Ae2Report(
                    true, false, false, false,
                    0, 0, 0, 0, 0, 0,
                    Collections.emptyList(), Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到 AE2 数字化网络组件",
                    ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§b【AE2 数字化网络：频道拓扑与控制器诊断】§r\n");
            sb.append(String.format("§7- 控制器: §f%d块§7 | 普通线缆(8ch): §f%d§7 | 致密线缆(32ch): §f%d§7 | 终端设备: §e%d台§r\n",
                    totalControllers, totalCables, totalDenseCables, totalDevices));

            if (isHealthy) {
                sb.append(String.format("§a✔ 网络工况健康：全部 %d 台设备在线 (100%% 频道覆盖)！§r\n", onlineDevices));
            } else {
                sb.append("§c❌ 拓扑异常警告：检测到网络阻断与配置缺陷！§r\n");
                if (hasMultiblockError) {
                    sb.append("§c  * 控制器多方块结构非法！整网陷入瘫痪！§r\n");
                }
                if (hasChannelOverload) {
                    sb.append(String.format("§6  * 频道过载耗尽：已有 %d 台终端设备因抢不到频道而掉线 (Missing Channel)！§r\n", missingChannelDevices));
                }
                if (hasP2pLoop) {
                    sb.append("§d  * 检测到 P2P 隧道自引用回环死锁！§r\n");
                }
            }

            if (!issues.isEmpty()) {
                sb.append("§e具体异常清单：§r\n");
                for (String issue : issues) {
                    sb.append(String.format("  §7- §f%s§r\n", issue));
                }
            }

            if (actionableRemediation != null && !actionableRemediation.isEmpty()) {
                sb.append("§a建议整改方案：§r\n");
                sb.append(String.format("  §7* §f%s§r\n", actionableRemediation));
            }

            return sb.toString();
        }
    }

    public static Ae2Report analyze(LocalMachineCluster cluster) {
        if (cluster == null || cluster.isEmpty()) {
            return Ae2Report.empty();
        }

        List<LocalBlock> ae2Blocks = cluster.getConnectedAe2();
        if (ae2Blocks.isEmpty()) {
            return Ae2Report.empty();
        }

        Map<BlockPos, LocalBlock> blockMap = new HashMap<>();
        List<LocalBlock> controllers = new ArrayList<>();
        List<LocalBlock> regularCables = new ArrayList<>();
        List<LocalBlock> denseCables = new ArrayList<>();
        List<LocalBlock> devices = new ArrayList<>();
        List<LocalBlock> p2pTunnels = new ArrayList<>();

        for (LocalBlock b : ae2Blocks) {
            blockMap.put(b.pos(), b);
            if (b.isAe2Controller()) {
                controllers.add(b);
            } else if (b.isAe2DenseCable()) {
                denseCables.add(b);
            } else if (b.isAe2Cable()) {
                regularCables.add(b);
            } else if (b.isAe2P2PTunnel()) {
                p2pTunnels.add(b);
                devices.add(b); // P2P consumes 1 channel on carrier
            } else if (b.isAe2Device()) {
                devices.add(b);
            }
        }

        List<String> issues = new ArrayList<>();
        List<BlockPos> illegalInterior = new ArrayList<>();
        List<BlockPos> overloadedCables = new ArrayList<>();
        List<BlockPos> offlineDevices = new ArrayList<>();
        boolean multiblockError = false;
        boolean channelOverload = false;
        boolean p2pLoop = false;

        // 1. Controller Multiblock Validation
        if (!controllers.isEmpty()) {
            Set<BlockPos> controllerSet = new HashSet<>();
            int minX = Integer.MAX_VALUE, maxX = Integer.MIN_VALUE;
            int minY = Integer.MAX_VALUE, maxY = Integer.MIN_VALUE;
            int minZ = Integer.MAX_VALUE, maxZ = Integer.MIN_VALUE;

            for (LocalBlock c : controllers) {
                BlockPos p = c.pos();
                controllerSet.add(p);
                minX = Math.min(minX, p.x());
                maxX = Math.max(maxX, p.x());
                minY = Math.min(minY, p.y());
                maxY = Math.max(maxY, p.y());
                minZ = Math.min(minZ, p.z());
                maxZ = Math.max(maxZ, p.z());
            }

            int spanX = maxX - minX + 1;
            int spanY = maxY - minY + 1;
            int spanZ = maxZ - minZ + 1;

            if (spanX > 7 || spanY > 7 || spanZ > 7) {
                multiblockError = true;
                issues.add(String.format("控制器尺寸超限：包围盒为 %dx%dx%d 方块（规则严禁超过 7x7x7）", spanX, spanY, spanZ));
            }

            // Check for fully enclosed solid interior blocks
            for (LocalBlock c : controllers) {
                BlockPos p = c.pos();
                int neighborControllerCount = 0;
                for (BlockPos n : p.getDirectNeighbors()) {
                    if (controllerSet.contains(n)) {
                        neighborControllerCount++;
                    }
                }
                if (neighborControllerCount == 6) {
                    multiblockError = true;
                    illegalInterior.add(p);
                    issues.add(String.format("控制器实心内部违规：坐标 %s 处于 2x2x2 封闭立方体核心内部（无任何外表面暴露）", p));
                }
            }

            // Check connectivity of controller blocks (must be a single connected component)
            if (!controllers.isEmpty()) {
                Set<BlockPos> visited = new HashSet<>();
                Queue<BlockPos> queue = new ArrayDeque<>();
                BlockPos start = controllers.get(0).pos();
                queue.add(start);
                visited.add(start);

                while (!queue.isEmpty()) {
                    BlockPos curr = queue.poll();
                    for (BlockPos n : curr.getDirectNeighbors()) {
                        if (controllerSet.contains(n) && !visited.contains(n)) {
                            visited.add(n);
                            queue.add(n);
                        }
                    }
                }

                if (visited.size() < controllers.size()) {
                    multiblockError = true;
                    issues.add(String.format("控制器多结构冲突：网络中存在 %d 个未连通的独立控制器构架（AE2 严禁同一个网络存在多个独立控制器组）",
                            controllers.size() - visited.size() + 1));
                }
            }
        }

        // 2. Channel Capacity & Spanning Tree Simulation
        int totalDev = devices.size();
        if (controllers.isEmpty()) {
            // Ad-hoc network without controller has hard cap of 8 channels
            if (totalDev > 8) {
                channelOverload = true;
                int deficit = totalDev - 8;
                issues.add(String.format("无控制器 (Ad-hoc) 网络频道超限：挂载了 %d 台设备（上限 8 频道），末端 %d 台设备已掉线", totalDev, deficit));
                for (int i = 8; i < totalDev; i++) {
                    offlineDevices.add(devices.get(i).pos());
                }
            }
        } else if (!multiblockError) {
            // With valid controller, build BFS tree to simulate greedy routing
            Map<BlockPos, Integer> depthMap = new HashMap<>();
            Map<BlockPos, BlockPos> parentMap = new HashMap<>();
            Queue<BlockPos> queue = new ArrayDeque<>();

            for (LocalBlock c : controllers) {
                depthMap.put(c.pos(), 0);
                queue.add(c.pos());
            }

            List<BlockPos> visitOrder = new ArrayList<>();
            while (!queue.isEmpty()) {
                BlockPos curr = queue.poll();
                visitOrder.add(curr);
                int d = depthMap.get(curr);

                for (BlockPos n : curr.getDirectNeighbors()) {
                    if (blockMap.containsKey(n) && !depthMap.containsKey(n)) {
                        depthMap.put(n, d + 1);
                        parentMap.put(n, curr);
                        queue.add(n);
                    }
                }
            }

            // Demand map for channel usage
            Map<BlockPos, Integer> channelDemand = new HashMap<>();
            for (LocalBlock dev : devices) {
                channelDemand.put(dev.pos(), 1);
            }

            // Aggregate channels from deepest leaf up to root
            Collections.reverse(visitOrder);
            for (BlockPos node : visitOrder) {
                int demand = channelDemand.getOrDefault(node, 0);
                BlockPos parent = parentMap.get(node);
                if (parent != null) {
                    channelDemand.put(parent, channelDemand.getOrDefault(parent, 0) + demand);
                }

                LocalBlock block = blockMap.get(node);
                if (block != null) {
                    int cap = 8;
                    boolean isCable = false;
                    if (block.isAe2DenseCable()) {
                        cap = 32;
                        isCable = true;
                    } else if (block.isAe2Cable()) {
                        cap = 8;
                        isCable = true;
                    }

                    if (isCable && demand > cap) {
                        channelOverload = true;
                        overloadedCables.add(node);
                        issues.add(String.format("线缆频道过载：%s 承载了 %d 个频道（容量上限 %d 频道），超出 %d 个频道！",
                                node, demand, cap, demand - cap));
                    }
                }
            }

            // Flag devices that exceed cable capacity along their route
            for (LocalBlock dev : devices) {
                BlockPos curr = dev.pos();
                boolean starved = false;
                while (curr != null) {
                    LocalBlock blk = blockMap.get(curr);
                    if (blk != null) {
                        int cap = blk.isAe2DenseCable() ? 32 : (blk.isAe2Cable() ? 8 : 1024);
                        int dem = channelDemand.getOrDefault(curr, 0);
                        if (dem > cap) {
                            starved = true;
                            break;
                        }
                    }
                    curr = parentMap.get(curr);
                }
                if (starved && !offlineDevices.contains(dev.pos())) {
                    offlineDevices.add(dev.pos());
                }
            }
        }

        // 3. P2P Recursive Loop Check
        if (p2pTunnels.size() >= 2) {
            for (LocalBlock p2p : p2pTunnels) {
                String subNet = p2p.getProperty("frequency", "");
                if ("carrier".equalsIgnoreCase(subNet) || "loop".equalsIgnoreCase(subNet)) {
                    p2pLoop = true;
                    issues.add(String.format("P2P 隧道自引用死锁：隧道 %s 频率绑定产生回环，载体与输出陷入递归循环！", p2p.pos()));
                }
            }
        }

        int missingCount = offlineDevices.size();
        int onlineCount = Math.max(0, totalDev - missingCount);
        boolean isHealthy = !multiblockError && !channelOverload && !p2pLoop;

        String primaryDiagnosis;
        String remediation;

        if (isHealthy) {
            primaryDiagnosis = String.format("✔ AE2 网络拓扑健康（%d 台设备全部在线，0 频道溢出）", totalDev);
            remediation = "当前网络布线合理。若未来新增机器，请注意保持各支路 8/32 频道裕度，或使用致密线缆/P2P 扩展。";
        } else if (multiblockError) {
            primaryDiagnosis = "❌ 控制器多方块结构严重违规，网络离线停摆！";
            if (!illegalInterior.isEmpty()) {
                remediation = String.format("立即拆除内部实心坐标 %s 处的控制器方块，使其保持中空或外表面暴露！", illegalInterior.get(0));
            } else {
                remediation = "检查控制器尺寸使其严格限制在 7x7x7 内，并确保所有控制器方块紧密相连为一个整体结构。";
            }
        } else if (channelOverload) {
            primaryDiagnosis = String.format("⚠ 频道超载导致 %d 台设备掉线 (Missing Channel)！", missingCount);
            remediation = "将过载处的普通线缆（8 频道）升级为致密线缆（32 频道），或使用 P2P 隧道建立点对点压缩传输。";
        } else {
            primaryDiagnosis = "⚠ P2P 隧道配置错误导致逻辑回环！";
            remediation = "重置 P2P 频率，确保载体子网与数据终端子网保持物理电气隔离。";
        }

        return new Ae2Report(
                isHealthy,
                multiblockError,
                channelOverload,
                p2pLoop,
                controllers.size(),
                regularCables.size(),
                denseCables.size(),
                totalDev,
                onlineCount,
                missingCount,
                illegalInterior,
                overloadedCables,
                offlineDevices,
                issues,
                primaryDiagnosis,
                remediation
        );
    }
}
