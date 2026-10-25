package hoshi.mcagent.chunkload;

import java.util.*;

public class PortalChunkLoaderAnalyzer {

    public static class AlignmentResult {
        public final double overworldX, overworldY, overworldZ;
        public final double netherX, netherY, netherZ;
        public final int idealNetherX, idealNetherZ;
        public final double driftDistance;
        public final boolean isPerfect;
        public final boolean isSafe;
        public final boolean isBleedRisk;
        public final String advice;

        public AlignmentResult(double owX, double owY, double owZ, double netherX, double netherY, double netherZ,
                               int idealX, int idealZ, double drift, boolean perfect, boolean safe, boolean bleedRisk, String advice) {
            this.overworldX = owX;
            this.overworldY = owY;
            this.overworldZ = owZ;
            this.netherX = netherX;
            this.netherY = netherY;
            this.netherZ = netherZ;
            this.idealNetherX = idealX;
            this.idealNetherZ = idealZ;
            this.driftDistance = drift;
            this.isPerfect = perfect;
            this.isSafe = safe;
            this.isBleedRisk = bleedRisk;
            this.advice = advice;
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§6【生电下界传送门：8:1 坐标对齐与串门风险诊断】§r\n");
            sb.append(String.format("§7- 主世界坐标: §f(%.1f, %.1f, %.1f)§7 ➔ 下界理想坐标: §e(%d, ~ , %d)§r\n",
                    overworldX, overworldY, overworldZ, idealNetherX, idealNetherZ));
            sb.append(String.format("§7- 下界实际坐标: §f(%.1f, %.1f, %.1f)§7 | 空间漂移误差: §b%.2f 格§r\n",
                    netherX, netherY, netherZ, driftDistance));

            if (isPerfect) {
                sb.append("§a✔ 状态：完美的 1:1 双向绝对严格对称绑定！零串门风险！§r\n");
            } else if (isSafe) {
                sb.append("§e✔ 状态：处于 16 格安全容差圈内，可正常双向互通。§r\n");
            } else {
                sb.append("§c❌ 致命风险：漂移距离超过 16 格，存在严重【单向串门撕裂 (Portal Bleed)】！从下界返回时可能在主世界另行生成新门！§r\n");
            }
            sb.append(String.format("§7- 纠正建议: %s§r\n", advice));
            return sb.toString();
        }
    }

    public static AlignmentResult evaluateAlignment(double owX, double owY, double owZ, double netherX, double netherY, double netherZ) {
        int idealX = (int) Math.floor(owX / 8.0);
        int idealZ = (int) Math.floor(owZ / 8.0);
        double drift = Math.hypot(netherX - idealX, netherZ - idealZ);
        boolean perfect = drift < 0.001;
        boolean safe = drift <= 16.0;
        boolean bleed = drift > 16.0;

        String advice;
        if (perfect) {
            advice = "坐标已达极致对齐，无需任何调整。";
        } else if (safe) {
            advice = String.format("若需规避任何潜在临近门干扰，建议将下界门精确迁至 X=%d, Z=%d。", idealX, idealZ);
        } else {
            advice = String.format("强烈建议立即拆毁当前下界门，并精确移动至 X=%d, Z=%d 处重新点燃以修复对称拓扑！", idealX, idealZ);
        }

        return new AlignmentResult(owX, owY, owZ, netherX, netherY, netherZ, idealX, idealZ, drift, perfect, safe, bleed, advice);
    }

    public static class PermaloaderReport {
        public final double intervalSeconds;
        public final String transportType;
        public final boolean isValid;
        public final boolean isExpired;
        public final double ticketTicksRemaining;
        public final List<String> details;

        public PermaloaderReport(double interval, String transport, boolean valid, boolean expired, double remaining, List<String> details) {
            this.intervalSeconds = interval;
            this.transportType = transport;
            this.isValid = valid;
            this.isExpired = expired;
            this.ticketTicksRemaining = remaining;
            this.details = details != null ? details : Collections.emptyList();
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§6【生电传送门常载网 (Permaloader) 强加载动力学诊断】§r\n");
            sb.append(String.format("§7- 投掷/穿梭周期: §f%.2f 秒 (%.0f Ticks)§7 | 物流载具: §b%s§r\n",
                    intervalSeconds, intervalSeconds * 20.0, transportType));

            if (!isValid) {
                sb.append("§c❌ 错误：穿梭周期必须大于 0 秒！§r\n");
            } else if (isExpired) {
                sb.append("§c❌ 致命故障：投掷周期 >= 15.0 秒 (300 Ticks)！Ticket 30 强加载票在实体到达前已彻底过期，常载区块必定卸载死锁！§r\n");
            } else {
                sb.append(String.format("§a✔ 状态：强加载时钟维持正常！每次穿梭后保留 %.1f Ticks 强加载安全裕度。§r\n", ticketTicksRemaining));
            }

            sb.append("§e区块加载范围与层级矩阵：§r\n");
            sb.append("  §7* §f3x3 区块 (48x48 格)§7: 实体完全运算区 (Entity Ticking, Ticket 30) - 怪物AI/矿车/红石全速运算\n");
            sb.append("  §7* §f5x5 区块 (80x80 格)§7: 方块红石运算区 (Block Ticking, Ticket 31) - 红石与作物生长，生物AI冻结\n");
            sb.append("  §7* §f7x7 区块 (112x112 格)§7: 懒惰边界区 (Lazy Chunks, Ticket 32) - 仅常驻内存供寻路，不执行Tick\n");

            if (!details.isEmpty()) {
                sb.append("§b生电工程建议：§r\n");
                for (String d : details) {
                    sb.append(String.format("  §7- §f%s§r\n", d));
                }
            }
            return sb.toString();
        }
    }

    public static PermaloaderReport analyzePermaloader(double intervalSeconds, String transport) {
        if (intervalSeconds <= 0.0) {
            return new PermaloaderReport(intervalSeconds, transport, false, true, 0.0, Collections.singletonList("无效周期"));
        }

        boolean expired = intervalSeconds >= 15.0;
        double remainingTicks = Math.max(0.0, (15.0 - intervalSeconds) * 20.0);
        List<String> recs = new ArrayList<>();

        if (expired) {
            recs.add("必须将投掷时钟缩短至 15.0 秒以内（生电标准黄金周期：8.0 ~ 12.0 秒），以防服务端 TPS 波动导致加载断流。");
            recs.add("下界侧必须配建完备的收集装置或反向投掷回路，严防堆积 70+ 掉落物造成服务器卡顿或 despawn。");
        } else {
            if (intervalSeconds > 12.0) {
                recs.add("警报：当前周期接近 15.0 秒临界点，一旦出现卡顿掉 Tick，常载票可能偶发断裂，建议优化至 10 秒左右。");
            } else {
                recs.add("时钟非常稳健，具备充裕的防断流冗余。");
            }
            recs.add("崩溃自愈建议：增设侦测器+投掷器自激振荡脉冲，确保服务端重启后能自启动循环。");
        }

        return new PermaloaderReport(intervalSeconds, transport, true, expired, remainingTicks, recs);
    }
}
