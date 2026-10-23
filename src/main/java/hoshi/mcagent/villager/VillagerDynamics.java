package hoshi.mcagent.villager;

/**
 * Villager AI dynamics: Iron farm panic timing, bed clearance, and workstation binding.
 * Diagnoses the #1 cause of broken iron farms: Permanent Panic Insomnia (LOS break failure).
 */
public final class VillagerDynamics {

    public enum FarmType {
        IRON_FARM("刷铁机 (Iron Farm)"),
        BREEDER("村民繁殖机 (Villager Breeder)"),
        TRADING_HALL("村民交易大厅 (Trading Hall)");

        private final String label;
        FarmType(String label) { this.label = label; }
        public String label() { return label; }
    }

    public record VillagerReport(
            FarmType type,
            boolean healthy,
            String issue,
            String solution,
            String formattedReport
    ) {}

    public static VillagerReport diagnoseIronFarm(int villagerCount, boolean hasLosBreak, boolean hasSleptRecently) {
        boolean healthy = true;
        String issue = "运行正常";
        String solution = "保持当前配置，注意收集水流防卡。";

        if (villagerCount < 3) {
            healthy = false;
            issue = String.format("村民数量不足（当前 %d 名，硬性最低需要 3 名）", villagerCount);
            solution = "补充至至少 3 名具有有效床位的村民。";
        } else if (!hasLosBreak) {
            healthy = false;
            issue = "致命缺陷：永恒恐慌失眠 (Permanent Panic Insomnia)！村民 24 小时目视僵尸，无法入睡。";
            solution = "必须设置视线遮挡 (LOS Break)！使用活塞定期遮挡视线、或水流颠簸，让村民每隔数秒能躺下床 1 tick 满足'20分钟内睡过觉'的前置硬性条件！";
        } else if (!hasSleptRecently) {
            healthy = false;
            issue = "村民在过去 20 分钟内未成功入睡过 (Sleep Timer Expired)。";
            solution = "等待夜晚来临，暂时遮挡僵尸 3 秒让村民躺下一次即可重新激活铁傀儡刷新。";
        }

        StringBuilder sb = new StringBuilder();
        sb.append("§3【刷铁机恐慌时序与运行诊断】§r\n");
        sb.append(String.format("▸ 村民编组：%d 名 (要求 ≥ 3 名)\n", villagerCount));
        sb.append(String.format("▸ 视线周期遮断 (LOS Break)：%s\n", hasLosBreak ? "§a✔ 已配置§r" : "§c✖ 未配置 (致命失眠停摆)§r"));
        sb.append(String.format("▸ 20分钟内睡眠记录：%s\n", hasSleptRecently ? "§a✔ 满足§r" : "§c✖ 未满足§r"));
        sb.append(String.format("▸ 综合判定：%s\n", healthy ? "§a✔ 运转健康§r" : "§c✖ 存在故障§r"));
        if (!healthy) {
            sb.append(String.format("▸ 故障根因：%s\n", issue));
            sb.append(String.format("▸ 修复方案：%s", solution));
        } else {
            sb.append(String.format("▸ 运行建议：%s", solution));
        }

        return new VillagerReport(FarmType.IRON_FARM, healthy, issue, solution, sb.toString().trim());
    }

    public static VillagerReport diagnoseBreeder(int foodCount, boolean hasUnclaimedBeds, int ceilingHeightAboveBeds) {
        boolean healthy = true;
        String issue = "运行正常";
        String solution = "村民将在满足意愿后自动交配繁殖。";

        if (ceilingHeightAboveBeds < 2) {
            healthy = false;
            issue = String.format("床头上方净空不足（当前 %d 格，硬性要求至少 2 格净空）", ceilingHeightAboveBeds);
            solution = "幼年村民必须能在床头方块上跳跃寻路！清除床头上方多余方块，确保至少 2 格完整空气。";
        } else if (foodCount < 3) {
            healthy = false;
            issue = String.format("食物意愿储备不足（当前 %d，单次繁殖双方各需 3 面包或 12 胡萝卜）", foodCount);
            solution = "投喂至少 3 个面包或 12 个胡萝卜/马铃薯。";
        } else if (!hasUnclaimedBeds) {
            healthy = false;
            issue = "村庄内无多余空闲床位";
            solution = "村民总数不能超过有效床位数，请在安全区增设更多床位。";
        }

        StringBuilder sb = new StringBuilder();
        sb.append("§d【村民繁殖机结构与意愿诊断】§r\n");
        sb.append(String.format("▸ 床头上方净空：%d 格 (%s)\n", ceilingHeightAboveBeds,
                ceilingHeightAboveBeds >= 2 ? "§a✔ 合规§r" : "§c✖ 阻挡寻路§r"));
        sb.append(String.format("▸ 食物意愿储量：%d 份 (%s)\n", foodCount,
                foodCount >= 3 ? "§a✔ 充足§r" : "§c✖ 不足§r"));
        sb.append(String.format("▸ 多余空闲床位：%s\n", hasUnclaimedBeds ? "§a✔ 充足§r" : "§c✖ 缺乏§r"));
        sb.append(String.format("▸ 综合判定：%s\n", healthy ? "§a✔ 具备繁殖条件§r" : "§c✖ 繁殖停滞§r"));
        if (!healthy) {
            sb.append(String.format("▸ 故障根因：%s\n", issue));
            sb.append(String.format("▸ 修复方案：%s", solution));
        } else {
            sb.append(String.format("▸ 运行建议：%s", solution));
        }

        return new VillagerReport(FarmType.BREEDER, healthy, issue, solution, sb.toString().trim());
    }

    public static VillagerReport diagnoseTrading(boolean tradedBefore, boolean canReachWorkstation) {
        boolean healthy = true;
        String issue = "运行正常";
        String solution = "村民每天工作时段至多补货两次。";

        if (tradedBefore && !canReachWorkstation) {
            healthy = false;
            issue = "职业已锁定 (XP>0)，但村民无法触碰工作台补货！";
            solution = "拆除阻挡方块，确保村民能够贴合工作台方块脚部。";
        } else if (!tradedBefore && !canReachWorkstation) {
            healthy = false;
            issue = "无法转职：未锁定职业且无法寻路至工作台。";
            solution = "将工作台摆放在村民视线与脚部可到达处。";
        }

        StringBuilder sb = new StringBuilder();
        sb.append("§b【村民交易大厅与工作站诊断】§r\n");
        sb.append(String.format("▸ 交易历史锁定：%s\n", tradedBefore ? "§e已锁定职业 (XP>0)§r" : "§7未锁定 (可自由转职)§r"));
        sb.append(String.format("▸ 工作站物理可达：%s\n", canReachWorkstation ? "§a✔ 可触碰§r" : "§c✖ 路径阻挡§r"));
        sb.append(String.format("▸ 综合判定：%s\n", healthy ? "§a✔ 状态健康§r" : "§c✖ 存在死锁§r"));
        if (!healthy) {
            sb.append(String.format("▸ 故障根因：%s\n", issue));
            sb.append(String.format("▸ 修复方案：%s", solution));
        } else {
            sb.append(String.format("▸ 运行建议：%s", solution));
        }

        return new VillagerReport(FarmType.TRADING_HALL, healthy, issue, solution, sb.toString().trim());
    }

    private VillagerDynamics() {}
}
