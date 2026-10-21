package hoshi.mcagent.engine;

import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;

import java.util.Optional;

/**
 * Fast-path resolver that computes answers deterministically in 0ms without calling LLMs.
 * Saves tokens, prevents hallucinations on mathematical/version facts, and keeps TPS unaffected.
 */
public final class FastPathResolver {

    public record Resolution(
            String textResponse,
            String suggestedCommand,
            String category
    ) {}

    public static Optional<Resolution> tryResolve(String rawQuery, ContextSnapshot context) {
        if (rawQuery == null || rawQuery.trim().isEmpty()) {
            return Optional.empty();
        }
        String q = rawQuery.trim().toLowerCase();

        // 1. Nether Portal / Coordinate math
        if (q.contains("地狱坐标") || q.contains("下界坐标") || q.contains("传送门坐标") || q.contains("对应坐标") || q.contains("换算坐标")) {
            return Optional.of(resolveCoordinates(context));
        }

        // 2. Ore depth distribution lookup
        if (q.contains("在几层") || q.contains("在第几层") || q.contains("层数") || q.contains("在哪挖") || q.contains("矿石分布") || q.contains("高度") || q.contains("怎么挖")) {
            LocalGameRules.OreDistribution ore = LocalGameRules.findOre(q);
            if (ore != null) {
                String resp = String.format("§6【%s 生成高度指南 (1.18+)】§r\n" +
                                "▸ 高度区间：Y=%d 至 Y=%d\n" +
                                "▸ 最优层数：§aY=%d§r\n" +
                                "▸ 提示：%s",
                        ore.name(), ore.minY(), ore.maxY(), ore.optimalY(), ore.notes());
                String cmd = String.format("/waypoint add %s Y=%d", ore.name().split(" ")[0], ore.optimalY());
                return Optional.of(new Resolution(resp, cmd, "ORE_LOOKUP"));
            }
        }

        // 3. Mob spawning & light level check
        if (q.contains("不刷怪") || (q.contains("刷怪") && (q.contains("亮度") || q.contains("条件") || q.contains("为什么") || q.contains("怎么") || q.contains("不生成")))) {
            StringBuilder sb = new StringBuilder();
            sb.append("§b【1.18+ 敌对生物刷怪判定】§r\n");
            if (context != null && context.targetBlock() != null && !context.targetBlock().isAir()) {
                TargetBlock tb = context.targetBlock();
                sb.append(String.format("▸ 您当前注视方块：[%d, %d, %d] | 方块光照：%d | 天空光照：%d\n",
                        tb.x(), tb.y(), tb.z(), tb.blockLight(), tb.skyLight()));
                if (tb.blockLight() > 0) {
                    sb.append(String.format("▸ §c注意：当前方块光照为 %d (>=1)，由于 1.18+ 规定方块光照必须为 0，此处绝不可能自然刷怪！§r\n", tb.blockLight()));
                } else {
                    sb.append("▸ 当前方块光照为 0，满足光照刷怪条件（需检查周围 24~128 格玩家距离及生物群系限制）。\n");
                }
            } else {
                sb.append("▸ 1.18+ 规则：方块内部【方块光照 (Block Light) 必须为 0】才能生成敌对怪！\n");
            }
            sb.append("▸ 彻底点亮：任意方块光照 >= 1 即安全；刷怪塔必须做到 0 漏光。");
            return Optional.of(new Resolution(sb.toString(), null, "MOB_SPAWN_LIGHT"));
        }

        // 4. Netherite upgrade (1.20+)
        if (q.contains("合金") && (q.contains("怎么") || q.contains("升级") || q.contains("模板") || q.contains("锻造") || q.contains("做") || q.contains("合"))) {
            String resp = "§6【下界合金装备升级 (1.20+)】§r\n" +
                    "▸ 1.20+ 锻造台不可直接合！必须放入三样：\n" +
                    "  ① §e下界合金升级锻造模板§r（堡垒遗迹宝箱获取）\n" +
                    "  ② 钻石装备/工具\n" +
                    "  ③ 下界合金锭\n" +
                    "▸ §a模板复制秘籍§r：工作台放置 7 个钻石 + 1 个下界岩 + 1 个升级模板 ➔ 复制出 2 个模板！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:bastion_remnant", "NETHERITE_UPGRADE"));
        }

        // 5. Mace / Heavy Core (1.21)
        if (q.contains("重锤") || q.contains("mace") || q.contains("重型核心") || q.contains("旋风棒")) {
            String resp = "§d【重锤 (Mace) 制作与机制 (1.21)】§r\n" +
                    "▸ 合成配方：1 个重型核心 (Heavy Core) + 1 个旋风棒 (Breeze Rod)\n" +
                    "▸ 获取途径：重型核心仅在试炼密室 (Trial Chamber) 的【不祥宝库】用不祥试炼钥匙开启获得\n" +
                    "▸ 核心特效：坠落攻击伤害随下落高度倍增，击中目标时完全免疫坠落伤害！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:trial_chambers", "MACE_1_21"));
        }

        // 6. Crafter (1.21)
        if (q.contains("合成器") || q.contains("自动合成") || q.contains("crafter")) {
            String resp = "§b【自动合成器 (Crafter) 指南 (1.21)】§r\n" +
                    "▸ 激活方式：需要红石脉冲（如时钟信号或侦测器）触发一次合成。\n" +
                    "▸ 槽位锁定：右键点击 3x3 槽位可禁用该格，使其不接受漏斗漏入物品。\n" +
                    "▸ 自动化技巧：通过红石比较器检测槽位填满度，满配方后触发脉冲发射成品。\n";
            return Optional.of(new Resolution(resp, null, "CRAFTER_1_21"));
        }

        // 7. Enchantment conflicts / mutual exclusions
        if (q.contains("冲突") || q.contains("互斥") || q.contains("不能一起") || (q.contains("附魔") && (q.contains("无限") || q.contains("经验修补") || q.contains("锋利") || q.contains("保护") || q.contains("时运")))) {
            String resp = "§e【附魔冲突与互斥速查】§r\n" +
                    "▸ §c弓箭§r：【经验修补】与【无限】互斥，无法共存！\n" +
                    "▸ §c武器伤害§r：【锋利】/【亡灵杀手】/【节肢杀手】互斥；重锤上【致密】与【破甲】互斥。\n" +
                    "▸ §c防具防护§r：【保护】/【火焰保护】/【爆炸保护】/【弹射物保护】互斥。\n" +
                    "▸ §c工具采集§r：【精准采集】与【时运】互斥。\n" +
                    "▸ §c弩箭特殊§r：【多重射击】与【穿透】互斥；靴子【冰霜行者】与【深海漫游者】互斥。";
            return Optional.of(new Resolution(resp, "/enchant @s minecraft:mending", "ENCHANTMENT_CONFLICT"));
        }

        // 8. Villager trade locking & professions
        if (q.contains("村民") && (q.contains("转职") || q.contains("锁") || q.contains("刷") || q.contains("工作台") || q.contains("职业") || q.contains("交易") || q.contains("图书") || q.contains("经验修补"))) {
            String resp = "§a【村民职业与锁交易机制】§r\n" +
                    "▸ §e永久锁定原则§r：只要与村民完成【任意 1 次交易】，其职业和附魔项将永久锁定，敲掉工作台也不会改变！\n" +
                    "▸ §b无限刷经验修补书技巧§r：在未交易前，放置讲台让无业村民成为图书管理员，检查交易；若不是所需附魔书，空手破坏讲台重放即可无限重置！\n" +
                    "▸ §f核心工作台对应§r：\n" +
                    "  - 讲台 ➔ 图书管理员 (附魔书/绿宝石)\n" +
                    "  - 高炉 ➔ 盔甲匠 | 砂轮 ➔ 武器匠 | 锻造台 ➔ 工具匠\n" +
                    "  - 制箭台 ➔ 制箭师 (木棍换绿宝石神器)";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:village", "VILLAGER_MECHANICS"));
        }

        // 9. Beacon Pyramid structure & layers
        if (q.contains("信标") || (q.contains("金字塔") && q.contains("层")) || (q.contains("急迫") && (q.contains("2") || q.contains("二") || q.contains("ii")))) {
            String resp = "§b【信标金字塔搭建与效果 (Beacon)】§r\n" +
                    "▸ §6基座矿物块规格§r（铁/金/绿宝石/钻石/下界合金均可）：\n" +
                    "  - 1 层：3×3 = 9 块 (范围 20 格，速度I / 急迫I)\n" +
                    "  - 2 层：5×5+9 = 34 块 (范围 30 格，增加 抗性I / 跳跃I)\n" +
                    "  - 3 层：7×7+34 = 83 块 (范围 40 格，增加 力量I)\n" +
                    "  - 4 层满级：9×9+83 = 164 块 (共 2 组+36 块，范围 50 格)\n" +
                    "▸ §a满级特权§r：解锁【急迫 II】（配合效率V镐实现秒挖深板岩/石头）或副效果【生命恢复 I】！\n" +
                    "▸ §c注意§r：信标正上方必须无任何不透明方块阻挡直通天空。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:beacon 1", "BEACON_STRUCTURE"));
        }

        // 10. Ominous Bottle & Trial Omen (1.21)
        if ((q.contains("不祥") && (q.contains("瓶") || q.contains("兆") || q.contains("宝库") || q.contains("钥匙") || q.contains("密室"))) || q.contains("试炼预兆")) {
            String resp = "§5【1.21 不祥之瓶与试炼预兆机制】§r\n" +
                    "▸ §e不祥之瓶 (Ominous Bottle)§r：击败掠夺者巡逻队旗帜队长掉落瓶子（I~V 级），喝下激活不祥之兆。\n" +
                    "▸ §d试炼预兆 (Trial Omen)§r：带着不祥之兆接近试炼密室，自动转为试炼预兆！普通刷怪笼升级为【不祥刷怪笼】。\n" +
                    "▸ §6重型核心获取途径§r：击破不祥刷怪笼掉落【不祥试炼钥匙】，用钥匙开启【不祥宝库】，有概率开出【重型核心 (Heavy Core)】合成重锤！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:trial_chambers", "OMINOUS_TRIAL_1_21"));
        }

        // 11. Warden & Sculk Shrieker
        if (q.contains("循声守卫") || q.contains("warden") || q.contains("监守者") || q.contains("潜声体") || q.contains("深暗之域")) {
            String resp = "§1【循声守卫 (Warden) 触发与应对】§r\n" +
                    "▸ §c召唤条件§r：自然生成的幽匿潜声体 (Sculk Shrieker) 被激活 4 次（潜声警告等级达到 4）时破土而出！\n" +
                    "▸ §4极度危险数据§r：生命值高达 500 点 (250心)；近战单击 30 伤害 (15心)；远程声波尖啸穿甲穿墙造成 10 点魔法伤害。\n" +
                    "▸ §a克制技巧§r：\n" +
                    "  - 【羊毛】和地毯能 100% 阻隔振动波传导；\n" +
                    "  - 始终保持潜行 (Shift) 移动；\n" +
                    "  - 投掷雪球或箭矢向远处方块发出声音诱敌，切勿硬拼！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:ancient_city", "WARDEN_MECHANICS"));
        }

        // 12. Copper Waxing & Scraping
        if (q.contains("铜") && (q.contains("蜡") || q.contains("锈") || q.contains("氧化") || q.contains("绿"))) {
            String resp = "§6【铜块氧化、打蜡与除锈指南】§r\n" +
                    "▸ §e4 阶段氧化§r：未锈蚀 (亮橙) ➔ 斑驳 (暗橙带绿) ➔ 锈蚀 (绿带橙) ➔ 氧化 (青绿)。\n" +
                    "▸ §a打蜡保色§r：手持【蜜脾 (Honeycomb)】右键点击铜块，即可锁定当前颜色（涂蜡的铜块），不再继续生锈。\n" +
                    "▸ §c刮蜡与除锈§r：手持【任意斧头 (Axe)】右键点击剥除蜡层，再次右键可回退一个生锈等级。\n" +
                    "▸ §b雷击奇效§r：附近立引雷针，雷电放电可大面积震落周围铜块的铜锈！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:honeycomb 64", "COPPER_WAXING"));
        }

        return Optional.empty();
    }

    private static Resolution resolveCoordinates(ContextSnapshot ctx) {
        if (ctx == null) {
            return new Resolution(LocalGameRules.NETHER_PORTAL_RULES, null, "COORDINATES_GENERAL");
        }

        if (ctx.isNether()) {
            int[] overworld = ctx.getOverworldEquivalentCoords();
            String text = String.format("§6【下界 ➔ 主界对应坐标】§r\n" +
                            "▸ 当前下界坐标：[%d, %d, %d]\n" +
                            "▸ 对应主界坐标：§a[%d, %d, %d]§r\n" +
                            "▸ 计算公式：主界 X = 下界 X × 8, 主界 Z = 下界 Z × 8",
                    ctx.blockX(), ctx.blockY(), ctx.blockZ(),
                    overworld[0], overworld[1], overworld[2]);
            String cmd = String.format("/tp %d %d %d", overworld[0], overworld[1], overworld[2]);
            return new Resolution(text, cmd, "COORDINATES_OVERWORLD");
        } else {
            int[] nether = ctx.getNetherEquivalentCoords();
            String text = String.format("§c【主界 ➔ 下界对应坐标】§r\n" +
                            "▸ 当前主界坐标：[%d, %d, %d]\n" +
                            "▸ 对应下界坐标：§e[%d, %d, %d]§r\n" +
                            "▸ 计算公式：下界 X = floor(主界 X / 8), 下界 Z = floor(主界 Z / 8)",
                    ctx.blockX(), ctx.blockY(), ctx.blockZ(),
                    nether[0], nether[1], nether[2]);
            String cmd = String.format("/tp %d %d %d", nether[0], nether[1], nether[2]);
            return new Resolution(text, cmd, "COORDINATES_NETHER");
        }
    }

    private FastPathResolver() {}
}
