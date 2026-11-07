package hoshi.mcagent.cluster;

import java.util.*;

/**
 * Diagnostic analyzer for Minecraft Redstone Comparator dynamics,
 * container signal measurement, item sorter crosstalk, and overflow protection.
 */
public final class ComparatorRedstoneAnalyzer {

    public record ContainerSlotInfo(int slot, String itemId, int count, int maxStack) {}

    public record ComparatorReport(
            boolean isHealthy,
            boolean isSubtractMode,
            int outputSignal,
            int rearSignal,
            int sideSignal,
            boolean isSorterSlice,
            int redstoneWireLength,
            boolean hasCrosstalkRisk,
            boolean hasUnstackablePollution,
            boolean isOverflowProtected,
            BlockPos comparatorPos,
            BlockPos containerPos,
            String containerType,
            int filledItemCount,
            int containerSlotCapacity,
            List<BlockPos> redstoneWireChain,
            List<BlockPos> crosstalkLeakTargets,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static ComparatorReport empty() {
            return new ComparatorReport(
                    true, false, 0, 0, 0,
                    false, 0, false, false, true,
                    new BlockPos(0, 0, 0), new BlockPos(0, 0, 0),
                    "none", 0, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    "未检测到红石比较器或容器组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§e【红石比较器与容器分类拓扑诊断报告】§r\n");
            sb.append(String.format("▸ 目标比较器坐标：%s (模式: %s)\n",
                    comparatorPos, isSubtractMode ? "§c减法模式 (Subtract)§r" : "§a比较模式 (Compare)§r"));
            sb.append(String.format("▸ 信号强度：输出 §6%d§r | 输入(后端): %d | 侧边: %d\n",
                    outputSignal, rearSignal, sideSignal));

            if (!"none".equals(containerType)) {
                sb.append(String.format("▸ 绑测容器：%s (%s) | 填充负载: %d 物品 (槽位: %d)\n",
                        containerPos, containerType.toUpperCase(), filledItemCount, containerSlotCapacity));
            }

            if (isSorterSlice) {
                sb.append(String.format("▸ 物品分类切片：红石线长 %d 格 | 架构: %s\n",
                        redstoneWireLength,
                        isOverflowProtected ? "§a[安全防串扰 (3格线/41+1)]§r" : "§c[高危串扰隐患 (短线/超载)]§r"));
            }

            if (hasCrosstalkRisk) {
                sb.append("  ⚡ §c[高危串扰警报] 漏斗满溢或红石线过短，信号将横向泄漏至相邻切片导致漏光！§r\n");
                if (!crosstalkLeakTargets.isEmpty()) {
                    sb.append("  ✖ 泄漏波及切片目标: ");
                    for (BlockPos p : crosstalkLeakTargets) sb.append(p).append(" ");
                    sb.append("\n");
                }
            }

            if (hasUnstackablePollution) {
                sb.append("  ✖ §c[槽位污染] 检测到不可堆叠/16堆叠物品误入滤波槽，致使信号异常激增！§r\n");
            }

            if (!issues.isEmpty()) {
                sb.append("§c【发现问题】§r\n");
                for (String issue : issues) {
                    sb.append("  ✖ ").append(issue).append("\n");
                }
            }
            if (!warnings.isEmpty()) {
                sb.append("§6【风险预警】§r\n");
                for (String warn : warnings) {
                    sb.append("  ⚠ ").append(warn).append("\n");
                }
            }

            sb.append("▸ 诊断结论：").append(primaryDiagnosis).append("\n");
            if (!actionableAdvice.isEmpty()) {
                sb.append("▸ 优化建议：").append(actionableAdvice).append("\n");
            }
            return sb.toString();
        }
    }

    /**
     * Exact Minecraft vanilla formula for comparator container signal.
     */
    public static int calculateContainerSignal(int slotCount, List<ContainerSlotInfo> items) {
        if (slotCount <= 0 || items == null || items.isEmpty()) {
            return 0;
        }
        double sumFilledRatio = 0.0;
        boolean hasAnyItem = false;
        for (ContainerSlotInfo item : items) {
            if (item.count() > 0) {
                hasAnyItem = true;
                int maxStack = item.maxStack() > 0 ? item.maxStack() : 64;
                sumFilledRatio += (double) item.count() / (double) maxStack;
            }
        }
        if (!hasAnyItem) {
            return 0;
        }
        double rawSignal = 1.0 + (sumFilledRatio / (double) slotCount) * 14.0;
        int signal = (int) Math.floor(rawSignal);
        return Math.min(15, Math.max(1, signal));
    }

    /**
     * Simplified container signal calculator for uniform stack size.
     */
    public static int calculateSimpleContainerSignal(int slotCount, int totalItems, int maxStack) {
        if (slotCount <= 0 || totalItems <= 0) return 0;
        int stackSize = maxStack > 0 ? maxStack : 64;
        List<ContainerSlotInfo> items = new ArrayList<>();
        int remaining = totalItems;
        for (int i = 0; i < slotCount && remaining > 0; i++) {
            int take = Math.min(stackSize, remaining);
            items.add(new ContainerSlotInfo(i, "item", take, stackSize));
            remaining -= take;
        }
        return calculateContainerSignal(slotCount, items);
    }

    public static ComparatorReport analyze(LocalMachineCluster cluster, BlockPos targetComparatorPos) {
        if (cluster == null || cluster.blocks().isEmpty()) {
            return ComparatorReport.empty();
        }

        LocalBlock comparator = cluster.getBlock(targetComparatorPos);
        if (comparator == null || !comparator.isComparator()) {
            // Find any comparator in cluster
            for (LocalBlock b : cluster.blocks().values()) {
                if (b.isComparator()) {
                    comparator = b;
                    targetComparatorPos = b.pos();
                    break;
                }
            }
        }
        if (comparator == null || !comparator.isComparator()) {
            return ComparatorReport.empty();
        }

        String facing = comparator.getProperty("facing", "north").toLowerCase();
        boolean isSubtract = "subtract".equalsIgnoreCase(comparator.getProperty("mode", "compare"));

        // Rear direction (source container or input power is opposite to facing)
        BlockPos rearPos = getOppositeOffset(targetComparatorPos, facing);
        LocalBlock rearBlock = cluster.getBlock(rearPos);

        BlockPos containerPos = rearPos;
        String containerType = "none";
        int slotCount = 0;
        int filledItemCount = 0;
        boolean hasUnstackable = false;
        int rearSignal = 0;

        if (rearBlock != null && rearBlock.isContainer()) {
            containerType = parseContainerType(rearBlock.blockId());
            slotCount = getSlotCapacity(containerType);

            // Check custom property for item counts if provided
            String itemsProp = rearBlock.getProperty("items_count", "");
            String unstackableProp = rearBlock.getProperty("has_unstackable", "false");
            hasUnstackable = "true".equalsIgnoreCase(unstackableProp);

            if (!itemsProp.isEmpty()) {
                try {
                    filledItemCount = Integer.parseInt(itemsProp);
                } catch (NumberFormatException ignored) {}
            } else {
                // Default based on container properties
                filledItemCount = parseItemCountFromBlock(rearBlock);
            }

            if (hasUnstackable) {
                // If polluted with unstackable item (e.g. 1 potion in hopper)
                List<ContainerSlotInfo> items = new ArrayList<>();
                items.add(new ContainerSlotInfo(0, "potion", 1, 1));
                int remaining = Math.max(0, filledItemCount - 1);
                for (int s = 1; s < slotCount; s++) {
                    int take = Math.min(64, remaining);
                    items.add(new ContainerSlotInfo(s, "filler", take, 64));
                    remaining -= take;
                }
                rearSignal = calculateContainerSignal(slotCount, items);
            } else {
                rearSignal = calculateSimpleContainerSignal(slotCount, filledItemCount, 64);
            }
        } else if (rearBlock != null) {
            String power = rearBlock.getProperty("power", "0");
            try {
                rearSignal = Integer.parseInt(power);
            } catch (NumberFormatException ignored) {
                rearSignal = rearBlock.isPowered() ? 15 : 0;
            }
        }

        // Side inputs (left and right perpendicular to facing)
        List<BlockPos> sidePositions = getSideOffsets(targetComparatorPos, facing);
        int sideSignal = 0;
        for (BlockPos sidePos : sidePositions) {
            LocalBlock sideBlock = cluster.getBlock(sidePos);
            if (sideBlock != null) {
                int p = 0;
                try {
                    p = Integer.parseInt(sideBlock.getProperty("power", "0"));
                } catch (NumberFormatException ignored) {
                    p = sideBlock.isPowered() ? 15 : 0;
                }
                if (p > sideSignal) sideSignal = p;
            }
        }

        // Output calculation
        int outputSignal;
        if (isSubtract) {
            outputSignal = Math.max(0, rearSignal - sideSignal);
        } else {
            outputSignal = rearSignal >= sideSignal ? rearSignal : 0;
        }

        // Analyze Redstone wire chain in front of comparator
        BlockPos frontPos = getFacingOffset(targetComparatorPos, facing);
        List<BlockPos> wireChain = new ArrayList<>();
        BlockPos cur = frontPos;
        for (int i = 0; i < 5; i++) {
            LocalBlock wire = cluster.getBlock(cur);
            if (wire != null && wire.isRedstoneWire()) {
                wireChain.add(cur);
                cur = getFacingOffset(cur, facing);
            } else {
                break;
            }
        }
        int wireLength = wireChain.size();

        // Sorter slice detection
        boolean isSorterSlice = (rearBlock != null && rearBlock.isHopper()) && (wireLength >= 2);
        boolean hasCrosstalkRisk = false;
        boolean isOverflowProtected = true;
        List<BlockPos> crosstalkLeakTargets = new ArrayList<>();

        if (isSorterSlice) {
            // Check overflow safety
            // If wireLength == 2, a signal of 3 will propagate signal strength 2 to wire 2,
            // which can cross-bleed into adjacent parallel slices!
            if (wireLength == 2) {
                isOverflowProtected = false;
                // If items can reach 46+ (triggering signal 3) or container is currently 46+
                if (filledItemCount >= 46 || outputSignal >= 3) {
                    hasCrosstalkRisk = true;
                    // Detect adjacent parallel wires at distance 1
                    for (BlockPos wirePos : wireChain) {
                        for (BlockPos side : getSideOffsets(wirePos, facing)) {
                            LocalBlock adj = cluster.getBlock(side);
                            if (adj != null && adj.isRedstoneWire()) {
                                crosstalkLeakTargets.add(side);
                            }
                        }
                    }
                }
            } else if (wireLength >= 3) {
                // Safe against full 64+1+1+1+1 = 68 items (signal 3)
                isOverflowProtected = true;
                if (outputSignal >= 4) {
                    // Extreme overflow (e.g. unstackable item pollution)
                    hasCrosstalkRisk = true;
                }
            }
        }

        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();
        boolean isHealthy = true;

        if (hasUnstackable) {
            isHealthy = false;
            issues.add(String.format("滤波漏斗内混入不可堆叠物品，导致比较器信号暴增至 %d！", outputSignal));
        }

        if (hasCrosstalkRisk) {
            isHealthy = false;
            issues.add(String.format("检测到红石串扰风险！当前信号强度 %d 在 %d 格红石线末端诱发横向泄漏，将毁损相邻分类切片！",
                    outputSignal, wireLength));
        } else if (!isOverflowProtected && isSorterSlice) {
            warnings.add(String.format("当前分类切片仅采用 %d 格红石线走线；若下方箱子满溢导致漏斗堆积超 45 件，将引发串扰！", wireLength));
        }

        String primaryDiagnosis;
        String actionableAdvice;

        if (!isHealthy) {
            if (hasUnstackable) {
                primaryDiagnosis = "不可堆叠物品槽位污染，破坏物品分类器信号标定";
                actionableAdvice = "立即取出漏斗中的不可堆叠物品，换用重命名后的 64 堆叠方块（如铁砧重命名安山岩）作为滤波占位符。";
            } else {
                primaryDiagnosis = "分类机红石线过短或满溢超载，面临相邻切片串扰烧毁风险";
                actionableAdvice = "建议将红石粉线路扩充至 3 格走线，并严格采用 41+1+1+1+1 物品布局，确保满溢时信号上限截断在 3 格以内。";
            }
        } else if (isSorterSlice) {
            primaryDiagnosis = isOverflowProtected ? "物品分类切片架构健全，具备防满溢串扰保护" : "物品分类切片正常运行（注意防范后续满仓溢出）";
            actionableAdvice = isOverflowProtected ? "当前 3 格红石走线与槽位配置安全，可支持紧凑密集切片并行排列。" :
                    "建议预留满仓停机熔断机制，或升级为标准 3 格红石线分类切片。";
        } else {
            primaryDiagnosis = String.format("红石比较器运行正常 (输出信号: %d)", outputSignal);
            actionableAdvice = isSubtract ? "当前处于减法模式，可通过侧面信号动态衰减实现脉冲延长或高频时钟。" :
                    "当前处于比较模式，输出等于或大于后端信号时如实透传。";
        }

        return new ComparatorReport(
                isHealthy, isSubtract, outputSignal, rearSignal, sideSignal,
                isSorterSlice, wireLength, hasCrosstalkRisk, hasUnstackable, isOverflowProtected,
                targetComparatorPos, containerPos, containerType,
                filledItemCount, slotCount, wireChain, crosstalkLeakTargets,
                issues, warnings, primaryDiagnosis, actionableAdvice
        );
    }

    private static BlockPos getOppositeOffset(BlockPos pos, String facing) {
        return switch (facing) {
            case "north" -> pos.offset(0, 0, 1);
            case "south" -> pos.offset(0, 0, -1);
            case "west" -> pos.offset(1, 0, 0);
            case "east" -> pos.offset(-1, 0, 0);
            default -> pos.offset(0, 0, 1);
        };
    }

    private static BlockPos getFacingOffset(BlockPos pos, String facing) {
        return switch (facing) {
            case "north" -> pos.offset(0, 0, -1);
            case "south" -> pos.offset(0, 0, 1);
            case "west" -> pos.offset(-1, 0, 0);
            case "east" -> pos.offset(1, 0, 0);
            default -> pos.offset(0, 0, -1);
        };
    }

    private static List<BlockPos> getSideOffsets(BlockPos pos, String facing) {
        List<BlockPos> sides = new ArrayList<>(2);
        if ("north".equals(facing) || "south".equals(facing)) {
            sides.add(pos.offset(-1, 0, 0));
            sides.add(pos.offset(1, 0, 0));
        } else {
            sides.add(pos.offset(0, 0, -1));
            sides.add(pos.offset(0, 0, 1));
        }
        return sides;
    }

    private static String parseContainerType(String blockId) {
        if (blockId == null) return "unknown";
        String id = blockId.toLowerCase();
        if (id.contains("hopper")) return "hopper";
        if (id.contains("chest")) return "chest";
        if (id.contains("barrel")) return "barrel";
        if (id.contains("shulker_box")) return "shulker_box";
        if (id.contains("dispenser")) return "dispenser";
        if (id.contains("dropper")) return "dropper";
        if (id.contains("crafter")) return "crafter";
        if (id.contains("furnace") || id.contains("smoker") || id.contains("blast_furnace")) return "furnace";
        if (id.contains("brewing_stand")) return "brewing_stand";
        if (id.contains("chiseled_bookshelf")) return "chiseled_bookshelf";
        if (id.contains("composter")) return "composter";
        return "container";
    }

    private static int getSlotCapacity(String containerType) {
        return switch (containerType) {
            case "hopper", "brewing_stand" -> 5;
            case "chest", "barrel", "shulker_box" -> 27;
            case "dispenser", "dropper", "crafter" -> 9;
            case "furnace" -> 3;
            case "chiseled_bookshelf" -> 6;
            case "composter" -> 8;
            default -> 27;
        };
    }

    private static int parseItemCountFromBlock(LocalBlock block) {
        String countStr = block.getProperty("items", "");
        if (!countStr.isEmpty()) {
            try {
                return Integer.parseInt(countStr);
            } catch (NumberFormatException ignored) {}
        }
        return block.isPowered() ? 45 : 0;
    }
}
