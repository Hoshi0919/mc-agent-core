package hoshi.mcagent.farm;

/**
 * Hostile mob spawning dynamics, despawn sphere geometry and monster spawner analyzer.
 * Evaluates AFK distance, mob cap risks (70 cap), and deepslate heightmap advantages.
 */
public final class MobFarmDynamics {

    public enum DespawnZone {
        NO_SPAWN("0~24格绝对禁刷盲区", false, "玩家距离刷怪面过近(<24格)，游戏引擎禁止自然生成敌对生物！请拉开挂机距离。"),
        ACTIVE_GOLDEN("24~32格黄金高频活动圈", true, "极佳挂机区间！生物生成后立即自由寻路/活动，不触发随机清除，产出效率最高。"),
        RANDOM_DESPAWN("33~128格随机清除区", true, "生物每tick有1/800几率被清除(半衰期约28s)；必须配套极速水流冲刷或致死摔落井。"),
        INSTANT_DESPAWN(">128格瞬间清除视界", false, "致命失误！生物生成瞬间(>128格)在下一个tick被强制清除，产出彻底为零！");

        private final String label;
        private final boolean viable;
        private final String advice;

        DespawnZone(String label, boolean viable, String advice) {
            this.label = label;
            this.viable = viable;
            this.advice = advice;
        }

        public String label() { return label; }
        public boolean viable() { return viable; }
        public String advice() { return advice; }
    }

    public record FarmReport(
            double distance,
            DespawnZone zone,
            boolean cavesLit,
            boolean mobCapRisk,
            double heightAdvantageRatio,
            String formattedReport
    ) {}

    public record SpawnerReport(
            double playerDistance,
            int blockLight,
            boolean playerInRange,
            boolean lightSuppressed,
            boolean active,
            String formattedReport
    ) {}

    public static FarmReport evaluate(double afkY, double farmY, boolean cavesLit) {
        double dist = Math.abs(afkY - farmY);
        DespawnZone zone;
        if (dist < 24.0) {
            zone = DespawnZone.NO_SPAWN;
        } else if (dist <= 32.0) {
            zone = DespawnZone.ACTIVE_GOLDEN;
        } else if (dist <= 128.0) {
            zone = DespawnZone.RANDOM_DESPAWN;
        } else {
            zone = DespawnZone.INSTANT_DESPAWN;
        }

        boolean mobCapRisk = !cavesLit && (zone == DespawnZone.ACTIVE_GOLDEN || zone == DespawnZone.RANDOM_DESPAWN);

        // Heightmap advantage: lower farm Y has fewer non-air blocks above it
        double currentSpan = Math.max(10.0, 320.0 - farmY);
        double baselineSpan = 320.0 - 64.0; // 256
        double heightAdvantageRatio = Math.round((baselineSpan / currentSpan) * 100.0) / 100.0;

        StringBuilder sb = new StringBuilder();
        sb.append("§4【敌对生物生成动力学与清除球诊断】§r\n");
        sb.append(String.format("▸ 挂机垂直净距：%.1f 格 (挂机 Y=%.0f, 平台 Y=%.0f)\n", dist, afkY, farmY));
        sb.append(String.format("▸ 清除球区间判定：%s\n", zone.label()));
        sb.append(String.format("▸ 区域力学评估：%s\n", zone.advice()));

        if (mobCapRisk) {
            sb.append("▸ §c⚠️ 敌对生物上限告警§r：周边128格未完全点亮！70只敌对生物Cap将被地下洞穴怪物迅速占满，导致平台断崖式停产！建议高空挂机或点亮128格矿洞。\n");
        } else if (cavesLit) {
            sb.append("▸ §a✔ 洞穴压制状态良好§r：周围128格已有效点亮，70生物Cap全额倾斜至刷怪平台。\n");
        }

        if (heightAdvantageRatio > 1.2) {
            sb.append(String.format("▸ §e基岩低Y轴优势§r：当前高度抽样效率为常规地表的 %.2f 倍！\n", heightAdvantageRatio));
        }

        return new FarmReport(dist, zone, cavesLit, mobCapRisk, heightAdvantageRatio, sb.toString().trim());
    }

    public static SpawnerReport evaluateSpawner(double playerDist, int blockLight) {
        boolean playerInRange = playerDist <= 16.0;
        boolean lightSuppressed = blockLight >= 11;
        boolean active = playerInRange && !lightSuppressed;

        StringBuilder sb = new StringBuilder();
        sb.append("§6【刷怪笼激活与光照压制诊断】§r\n");
        sb.append(String.format("▸ 玩家距离：%.1f 格 (%s)\n", playerDist,
                playerInRange ? "§a≤16格 激活范围内§r" : "§c>16格 超出范围休眠§r"));
        sb.append(String.format("▸ 方块光照：%d 级 (%s)\n", blockLight,
                lightSuppressed ? "§a≥11级 彻底熄灭压制§r" : "§e<11级 允许生成§r"));

        if (!playerInRange) {
            sb.append("▸ §c状态：休眠§r。刷怪笼内旋转模型停止，无火焰粒子，玩家必须靠近至 16 格以内。");
        } else if (lightSuppressed) {
            sb.append("▸ §a状态：安全熄灭§r。高光照已彻底破坏生成条件，无怪物生成。");
        } else {
            sb.append("▸ §e状态：活跃生成中§r！建议底部铺设流水快速冲离 9x9x3 检查盒，防止同类实体达到 6 只导致生成暂停。");
        }

        return new SpawnerReport(playerDist, blockLight, playerInRange, lightSuppressed, active, sb.toString().trim());
    }

    private MobFarmDynamics() {}
}
