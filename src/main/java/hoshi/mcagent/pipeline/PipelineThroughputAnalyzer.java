package hoshi.mcagent.pipeline;

import java.util.Objects;

/**
 * Throughput & Bottleneck Analyzer for Minecraft Logistics and Automation (Vanilla & Modpack).
 * Calculates exact transfer rates, deficit bottlenecks, and scaling optimizations.
 */
public class PipelineThroughputAnalyzer {

    // Logistics Transfer Constants (Items per second)
    public static final double HOPPER_TRANSFER_RATE = 2.5;         // 8 game ticks (0.4s) per item transfer
    public static final double HOPPER_MINECART_RATE = 20.0;       // 1 item per game tick (0.05s) through solid block
    public static final double WATER_ICE_STREAM_RATE = 32.0;      // Continuous water flow on packed/blue ice
    public static final double DROPPER_HIGH_FREQ_RATE = 10.0;     // 2-tick observer pulse clock dropper

    // Machine Smelting Constants (Items consumed per second)
    public static final double REGULAR_FURNACE_RATE = 0.1;        // 200 game ticks (10.0s) per smelt
    public static final double BLAST_FURNACE_RATE = 0.2;          // 100 game ticks (5.0s) per ore smelt (2x speed)
    public static final double SMOKER_RATE = 0.2;                 // 100 game ticks (5.0s) per food smelt (2x speed)

    public record PipelineReport(
            String systemName,
            int machineCount,
            double machineItemRate,
            double totalDemandRate,
            String transportType,
            double supplyCapacityRate,
            boolean hasBottleneck,
            double deficitPercentage,
            int maxSupportedMachines,
            String diagnosis,
            String optimizationAdvice
    ) {
        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("§6【工业物流流水线吞吐诊断：%s】§r\n", systemName));
            sb.append(String.format("▸ §7阵列规模§r：%d 台设备 | 单台消耗: %.2f items/s | 总需求: §e%.2f items/s§r\n",
                    machineCount, machineItemRate, totalDemandRate));
            sb.append(String.format("▸ §b供料管线§r：%s | 最大供料速率: §%s%.2f items/s§r\n",
                    transportType, hasBottleneck ? "c" : "a", supplyCapacityRate));

            if (hasBottleneck) {
                sb.append(String.format("▸ §c⚠️ 瓶颈告警§r：严重供料赤字！缺口达到 §c%.1f%%§r，主干管道无法承载！\n", deficitPercentage));
                sb.append(String.format("  当前管网最多仅能支撑 §e%d 台§r 设备满载运转，其余 %d 台将陷入周期性断料停摆。\n",
                        maxSupportedMachines, machineCount - maxSupportedMachines));
                sb.append(String.format("▸ §a优化方案§r：%s\n", optimizationAdvice));
            } else {
                double spare = supplyCapacityRate - totalDemandRate;
                sb.append(String.format("▸ §a✔ 物流充盈§r：供料充足！吞吐冗余度 +%.1f%% (余量 +%.2f items/s)。\n",
                        (supplyCapacityRate / totalDemandRate - 1.0) * 100, spare));
                sb.append(String.format("  当前供料系统最高可拓展支撑至 §e%d 台§r 设备满载运转。\n", maxSupportedMachines));
                sb.append(String.format("▸ §e工程提示§r：%s\n", optimizationAdvice));
            }
            return sb.toString();
        }
    }

    /**
     * Evaluates a furnace smelting array against an input transport pipeline.
     */
    public static PipelineReport analyzeSmeltingArray(int furnaceCount, String furnaceType, String transportType) {
        int count = Math.max(1, furnaceCount);
        String fType = furnaceType != null ? furnaceType.trim().toLowerCase() : "furnace";
        String tType = transportType != null ? transportType.trim().toLowerCase() : "hopper";

        double machineRate = REGULAR_FURNACE_RATE;
        String systemName = "普通熔炉阵列";
        if (fType.contains("blast") || fType.contains("高炉")) {
            machineRate = BLAST_FURNACE_RATE;
            systemName = "高炉冶炼阵列 (2x极速)";
        } else if (fType.contains("smoker") || fType.contains("烟熏")) {
            machineRate = SMOKER_RATE;
            systemName = "烟熏炉烹饪阵列 (2x极速)";
        }

        double totalDemand = count * machineRate;

        double supplyRate = HOPPER_TRANSFER_RATE;
        String transportDesc = "单漏斗传输 (2.5 items/s)";
        if (tType.contains("dual") || tType.contains("双漏斗")) {
            supplyRate = HOPPER_TRANSFER_RATE * 2.0;
            transportDesc = "双漏斗对称并联 (5.0 items/s)";
        } else if (tType.contains("minecart") || tType.contains("矿车")) {
            supplyRate = HOPPER_MINECART_RATE;
            transportDesc = "漏斗矿车穿透极速分流 (20.0 items/s)";
        } else if (tType.contains("water") || tType.contains("水流") || tType.contains("冰道")) {
            supplyRate = WATER_ICE_STREAM_RATE;
            transportDesc = "水流浮冰高速通道 (32.0 items/s)";
        } else if (tType.contains("dropper") || tType.contains("投掷器")) {
            supplyRate = DROPPER_HIGH_FREQ_RATE;
            transportDesc = "侦测器双频投掷器 (10.0 items/s)";
        }

        boolean bottleneck = supplyRate < totalDemand;
        double deficit = bottleneck ? ((totalDemand - supplyRate) / totalDemand) * 100.0 : 0.0;
        int maxSupported = (int) Math.floor(supplyRate / machineRate);

        String advice;
        if (bottleneck) {
            if (tType.contains("hopper") && !tType.contains("dual")) {
                advice = "单漏斗 2.5/s 上限锁死！建议升级为【双漏斗对称推入】(支持 25 台高炉) 或部署【漏斗矿车来回巡回分流】(支持 100 台高炉)。";
            } else if (tType.contains("dual")) {
                advice = "双漏斗 5.0/s 已饱和！建议改用【顶部漏斗矿车站】穿透下料或【水流冰道投掷器批量分流】。";
            } else {
                advice = "建议将阵列拆分为独立的双路对称单元，或增加前置缓冲分配箱。";
            }
        } else {
            advice = "当前物流供料处于完全健康区间，下层出料口漏斗排空速率建议同步匹配，避免出料堵塞。";
        }

        return new PipelineReport(
                systemName,
                count,
                machineRate,
                totalDemand,
                transportDesc,
                supplyRate,
                bottleneck,
                deficit,
                maxSupported,
                bottleneck ? "SUPPLY_BOTTLENECK" : "THROUGHPUT_HEALTHY",
                advice
        );
    }
}
