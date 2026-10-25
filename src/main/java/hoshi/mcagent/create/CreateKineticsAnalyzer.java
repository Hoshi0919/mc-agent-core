package hoshi.mcagent.create;

import java.util.*;

public class CreateKineticsAnalyzer {

    public static class MachineEntry {
        public final String type;
        public final int count;
        public final double rpm;
        public final double impactFactor; // SU per RPM

        public MachineEntry(String type, int count, double rpm) {
            this.type = type.toLowerCase();
            this.count = count;
            this.rpm = rpm;
            this.impactFactor = resolveImpactFactor(this.type);
        }

        public double getTotalImpact() {
            return impactFactor * rpm * count;
        }
    }

    public static double resolveImpactFactor(String type) {
        String t = type.toLowerCase();
        if (t.contains("crush") || t.contains("粉碎")) return 8.0;
        if (t.contains("press") || t.contains("辊压") || t.contains("冲压")) return 8.0;
        if (t.contains("arm") || t.contains("机械臂")) return 8.0;
        if (t.contains("mix") || t.contains("搅拌")) return 4.0;
        if (t.contains("saw") || t.contains("锯")) return 4.0;
        if (t.contains("mill") || t.contains("磨盘") || t.contains("风磨")) return 4.0;
        if (t.contains("drill") || t.contains("钻头")) return 4.0;
        if (t.contains("pump") || t.contains("泵")) return 4.0;
        if (t.contains("belt") || t.contains("带") || t.contains("齿轮")) return 1.0;
        return 4.0; // default baseline
    }

    public static class KineticReport {
        public final String sourceName;
        public final double totalCapacity;
        public final double totalImpact;
        public final double loadFactor;
        public final boolean isOverstressed;
        public final double surplusSU;
        public final double deficitSU;
        public final double maxUniformRPM;
        public final List<String> recommendations;

        public KineticReport(String sourceName, double totalCapacity, double totalImpact, double loadFactor,
                             boolean isOverstressed, double surplusSU, double deficitSU, double maxUniformRPM,
                             List<String> recommendations) {
            this.sourceName = sourceName;
            this.totalCapacity = totalCapacity;
            this.totalImpact = totalImpact;
            this.loadFactor = loadFactor;
            this.isOverstressed = isOverstressed;
            this.surplusSU = surplusSU;
            this.deficitSU = deficitSU;
            this.maxUniformRPM = maxUniformRPM;
            this.recommendations = recommendations != null ? recommendations : Collections.emptyList();
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§6【Create 机械动力学：应力与转速网络诊断】§r\n");
            sb.append(String.format("§7- 动力源: §f%s§7 | 总应力容量: §e%.0f SU§7 | 负载总消耗: §b%.0f SU§7 (负载率: §f%.1f%%§7)§r\n",
                    sourceName, totalCapacity, totalImpact, loadFactor));

            if (isOverstressed) {
                sb.append(String.format("§c❌ 致命状态：动力网络已【过载断裂 (Overstressed)】！转速归零停摆！赤字: -%.0f SU§r\n", deficitSU));
            } else {
                sb.append(String.format("§a✔ 状态正常：动力裕度充沛 (+%.0f SU)，全线稳定运转！§r\n", surplusSU));
            }

            if (maxUniformRPM > 0) {
                sb.append(String.format("§d- 临界全线安全同步转速上限: §f%.1f RPM§7 (当前最高不可超过此值)§r\n", maxUniformRPM));
            }

            if (!recommendations.isEmpty()) {
                sb.append("§e优化与调谐建议：§r\n");
                for (String rec : recommendations) {
                    sb.append(String.format("  §7* §f%s§r\n", rec));
                }
            }
            return sb.toString();
        }
    }

    public static KineticReport analyze(String source, int param, List<MachineEntry> machines) {
        double capacity = 0.0;
        String sourceLabel;
        String s = source.toLowerCase();

        if (s.contains("large_water") || s.contains("大水轮")) {
            int count = Math.max(1, param);
            capacity = count * 512.0;
            sourceLabel = count + "台大型水轮 (512 SU/台 @ 4 RPM)";
        } else if (s.contains("water") || s.contains("水轮")) {
            int count = Math.max(1, param);
            capacity = count * 256.0;
            sourceLabel = count + "台小型水轮 (256 SU/台 @ 8 RPM)";
        } else if (s.contains("windmill") || s.contains("风车")) {
            int sails = Math.max(8, param);
            int sailUnits = Math.min(16, sails / 8);
            capacity = sailUnits * 512.0;
            sourceLabel = String.format("风车轴承 (%d块帆布, %d组 @ 16 RPM)", sails, sailUnits);
        } else if (s.contains("steam") || s.contains("蒸汽")) {
            int level = Math.max(1, Math.min(18, param));
            if (level == 1) capacity = 2048.0;
            else if (level == 2) capacity = 4096.0;
            else if (level == 3) capacity = 8192.0;
            else if (level == 4) capacity = 16384.0;
            else if (level <= 9) capacity = level * 16384.0;
            else capacity = 147456.0 + (level - 9) * 16384.0;
            sourceLabel = String.format("%d级蒸汽机锅炉阵列", level);
        } else {
            capacity = Math.max(512.0, param);
            sourceLabel = String.format("自定义动力网络 (%s: %.0f SU)", source, capacity);
        }

        double totalImpact = 0.0;
        double sumKTimesCount = 0.0;
        if (machines != null) {
            for (MachineEntry m : machines) {
                totalImpact += m.getTotalImpact();
                sumKTimesCount += m.impactFactor * m.count;
            }
        }

        double loadFactor = capacity > 0 ? (totalImpact / capacity) * 100.0 : 999.0;
        boolean overstressed = totalImpact > capacity;
        double surplus = Math.max(0.0, capacity - totalImpact);
        double deficit = Math.max(0.0, totalImpact - capacity);
        double maxUniformRPM = sumKTimesCount > 0 ? capacity / sumKTimesCount : 256.0;

        List<String> recs = new ArrayList<>();
        if (overstressed) {
            recs.add(String.format("过载断裂警报：总消耗超过容量 %.0f SU。建议增设变速齿轮降速（齿轮比 1:2 可减半应力消耗）。", deficit));
            if (s.contains("windmill") || s.contains("风车")) {
                int neededSails = (int) Math.ceil(deficit / 512.0) * 8;
                recs.add(String.format("扩容方案：为风车追加安装至少 %d 块帆布以补齐 %.0f SU 缺口。", neededSails, deficit));
            } else if (s.contains("steam") || s.contains("蒸汽")) {
                recs.add("扩容方案：增加锅炉水箱容积、提升供水通量（机械泵高速注水）或喂食烈焰饼触发超频！");
            } else {
                recs.add(String.format("扩容方案：并联至少 %d 台水轮以增加基础应力输出。", (int) Math.ceil(deficit / 256.0)));
            }
        } else {
            if (loadFactor > 80.0) {
                recs.add(String.format("高负载运行警报：当前负载率已达 %.1f%%，后续新增设备易诱发过载断裂，请预留至少 20%% 缓冲裕度。", loadFactor));
            } else {
                recs.add(String.format("工况极佳：剩余可用裕度 %.0f SU，可安全挂载更高转速或接入更多工艺机器。", surplus));
            }
            recs.add("齿轮传动法则：大齿轮带动小齿轮 2:1 提速（转速翻倍但应力消耗翻倍），小齿轮带动大齿轮 1:2 降速（转速减半但消耗减半）。");
        }

        return new KineticReport(sourceLabel, capacity, totalImpact, loadFactor, overstressed, surplus, deficit, maxUniformRPM, recs);
    }
}
