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

        // 13. Comparator & Container Fill / Item Sorter
        if (q.contains("比较器") || q.contains("分类机") || q.contains("物品分类") || q.contains("漏斗分类") || q.contains("22个") || q.contains("22 个") || q.contains("比较器信号") || q.contains("测箱子")) {
            String resp = "§c【红石比较器容器信号与分类机数学】§r\n" +
                    "▸ §e容器满度公式§r：Signal = floor(1 + (sum(count / max_stack) / slots) * 14)（空容器输出 0）。\n" +
                    "▸ §a经典 22 物品分类漏斗 (18-1-1-1-1)§r：第 1 格放 18 个待分类物品，第 2~5 格各放 1 个重命名杂物；刚好 22 个物品时信号强度为 1，进入第 23 个物品时升至 2。\n" +
                    "▸ §b防串线 41 物品布局§r：避免极端堆积冲至 3 格信号串线。\n" +
                    "▸ §d1.21 自动合成器 (Crafter)§r：比较器输出强度对应有物品或禁用的槽位数 (0~9)！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:comparator 1", "COMPARATOR_SORTING"));
        }

        // 14. Anvil Prior Work Penalty & Binary Tree Merge
        if (q.contains("铁砧") || q.contains("过于昂贵") || q.contains("经验惩罚") || q.contains("二叉树附魔") || q.contains("附魔省经验") || q.contains("修装备太贵")) {
            String resp = "§6【铁砧累积惩罚与二叉树最优附魔】§r\n" +
                    "▸ §c累积惩罚 (Prior Work)§r：附加消耗按 2^n - 1 增长（0 ➔ 1 ➔ 3 ➔ 7 ➔ 15 ➔ 31 级）。\n" +
                    "▸ §4过于昂贵§r：生存模式单次操作所需经验 >= 40 级时会被拒绝。\n" +
                    "▸ §a二叉树最优合并法§r：附魔书两两配对合并，最后将合集书一次性打在装备上，避免单线串联导致经验爆炸！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:anvil 1", "ANVIL_OPTIMIZATION"));
        }

        // 15. Brewing Stand & Potions
        if (q.contains("酿造台") || q.contains("药水配方") || q.contains("怎么酿") || q.contains("隐身药水") || q.contains("神龟药水") || q.contains("抗火药水") || q.contains("粗制药水") || q.contains("变异药水")) {
            String resp = "§d【酿造台配方与药水学快速推演】§r\n" +
                    "▸ §e核心底药§r：水瓶 + 下界疣 ➔ 粗制的药水。\n" +
                    "▸ §b主力材料§r：糖➔迅捷；烈焰粉➔力量；金胡萝卜➔夜视；岩浆膏➔抗火；幻翼膜➔缓降；海龟壳➔神龟药水。\n" +
                    "▸ §c发酵蛛眼§r：夜视➔隐身；迅捷/跳跃➔缓慢；治疗/剧毒➔伤害。红石粉延长时长，荧石粉升 II 级，火药制成喷溅。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:brewing_stand 1", "BREWING_RECIPES"));
        }

        // 16. Iron Golem Spawning & Iron Farm
        if (q.contains("铁傀儡") || q.contains("刷铁机") || q.contains("为什么不刷铁") || q.contains("村民惊吓") || q.contains("不生成铁傀儡")) {
            String resp = "§a【铁傀儡生成判定与刷铁机力学】§r\n" +
                    "▸ §e三大前置条件§r：至少 3 名有效村民绑定床铺；过去 20 分钟内村民必须睡过觉；村民需进入惊吓恐慌态。\n" +
                    "▸ §b生成空间§r：村民中心 16×13×16 空间内需要完整方块表面，上方有 3 格空气或水流。\n" +
                    "▸ §c排查§r：视线受阻无法入睡、附近残留铁傀儡、生成点空间不足，都可能导致不刷铁。";
            return Optional.of(new Resolution(resp, "/summon minecraft:iron_golem", "IRON_GOLEM_MECHANICS"));
        }

        // 17. Nether Portal Linking & Desync
        if (q.contains("传送门对齐") || q.contains("串门") || q.contains("传送门错位") || q.contains("下界门跑偏") || q.contains("双向传送门")) {
            String resp = "§5【下界传送门精准对齐与防串门机制】§r\n" +
                    "▸ §c串门根源§r：下界与主界为 8:1 坐标比例，进门搜索半径高达 128 格，多门会重定向至错误出口。\n" +
                    "▸ §a黄金对齐法§r：主界 [X,Y,Z] 对应下界 [floor(X/8),Y,floor(Z/8)]，在精确点手动搭门并点燃。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:obsidian 14", "PORTAL_LINKING"));
        }

        // 18. Ender Dragon Resummoning & End Gateway / Elytra
        if (q.contains("末影龙") || q.contains("复活龙") || q.contains("折跃门") || q.contains("末地折跃门") || q.contains("末地外岛") || q.contains("鞘翅怎么飞") || q.contains("潜影盒怎么合") || q.contains("龙蛋")) {
            String resp = "§5【末影龙复活、末地折跃门与鞘翅探索】§r\n" +
                    "▸ §e复活末影龙§r：在返回传送门 4 个方向中心各放置 1 个【末影水晶】（共 4 个），水晶光束将重生顶端水晶并孵化末影龙（复活掉落 500 经验，无新龙蛋）。\n" +
                    "▸ §a末地折跃门§r：击杀末影龙后生成 1x1 基岩折跃门，投掷末影珍珠穿透瞬间传送至 1000 格外末地外岛！\n" +
                    "▸ §b鞘翅与火箭§r：末地船物品框获取鞘翅；副手持纯火药+纸合成的烟花火箭推进加速；潜影盒由 2 潜影壳 + 1 木箱合成。";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:end_city", "END_DRAGON_GATEWAY"));
        }

        // 19. Conduit Structure & Power
        if (q.contains("潮涌核心") || q.contains("潮涌能量") || q.contains("导管怎么激活") || q.contains("潮涌核心怎么摆") || q.contains("海洋之心") || q.contains("鹦鹉螺壳") || q.contains("海晶石框架")) {
            String resp = "§3【潮涌核心搭建与水下主宰力学】§r\n" +
                    "▸ §e核心合成§r：1 个海洋之心（藏宝箱）+ 8 个鹦鹉螺壳（钓鱼或溺尸掉落）。\n" +
                    "▸ §a框架搭建§r：核心置于水中心，用海晶石搭建 5×5 正交环。16 块启动基础范围 32 格，42 块满级范围达 96 格！\n" +
                    "▸ §d主宰效果§r：水下无限呼吸、夜视、挖掘不减速；满级对 8 格内溺尸与守卫者持续造成每 2 秒 4 点伤害！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:conduit 1", "CONDUIT_STRUCTURE"));
        }

        // 20. Raid & Hero of the Village
        if (q.contains("突袭怎么触发") || q.contains("村庄袭击") || q.contains("村庄英雄") || q.contains("唤魔者") || q.contains("不死图腾") || q.contains("破坏兽") || q.contains("袭村") || q.contains("袭击波次")) {
            String resp = "§4【村庄突袭 (Raid) 机制与村庄英雄】§r\n" +
                    "▸ §c触发机制 (1.21)§r：击败巡逻队长掉落不祥之瓶，饮用后进村转化为突袭预兆，30 秒倒计时后爆发袭击！\n" +
                    "▸ §e波次规格§r：简单 3 波、普通 5 波、困难 7 波。卫道士斧头高伤，唤魔者掉落不死图腾，女巫丢药水。\n" +
                    "▸ §a胜利奖赏§r：赋予【村庄英雄】Buff，村民全线打折（最低 1 绿宝石换神装）并投掷礼物！";
            return Optional.of(new Resolution(resp, "/effect give @s minecraft:hero_of_the_village 300 1", "RAID_VILLAGE"));
        }

        // 21. Piglin Bartering & Piglin Brute
        if (q.contains("猪灵交易") || q.contains("以物易物") || q.contains("猪灵蛮兵") || q.contains("为什么猪灵打我") || q.contains("猪灵开箱") || q.contains("猪灵金装") || q.contains("猪灵换末影珍珠")) {
            String resp = "§6【猪灵以物易物与猪灵蛮兵权威力学】§r\n" +
                    "▸ §a穿金防身§r：穿戴至少 1 件黄金装备防普通猪灵敌对。\n" +
                    "▸ §4绝对禁忌§r：破坏金矿/金块，或打开/破坏任何箱子、潜影盒、末影箱、木桶，周围 16 格猪灵全员激怒！\n" +
                    "▸ §e以物易物§r：金锭投掷给成年猪灵，掉落末影珍珠、抗火药水、哭泣的黑曜石、灵魂沙等。\n" +
                    "▸ §c猪灵蛮兵§r：堡垒遗迹专属！免疫金装伪装、绝不交易、不可安抚，必须垫高或熔岩优先击杀！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:gold_ingot 64", "PIGLIN_BARTER"));
        }

        // 22. Enchanting Table Geometry & Bookshelves
        if (q.contains("附魔台摆放") || q.contains("15个书架") || q.contains("30级附魔") || q.contains("附魔台被挡") || q.contains("附魔台怎么摆") || q.contains("砂轮洗附魔") || q.contains("附魔台有效距离")) {
            String resp = "§5【30 级附魔台几何摆放与经验洗炼】§r\n" +
                    "▸ §e书架配置§r：需要恰好 15 个书架，围在附魔台周围水平 2 格距离（留出 1 格空气）。\n" +
                    "▸ §c遮挡禁忌§r：附魔台与书架中间 1 格空气严禁有火把、地毯、雪片等任何方块阻挡，否则附魔等级骤降！\n" +
                    "▸ §b附魔技巧§r：消耗 3 级经验 + 3 青金石；词条不满意用砂轮洗掉非诅咒附魔返还经验并刷新种子。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:enchanting_table 1", "ENCHANTING_TABLE"));
        }

        // 23. Java Edition vs Bedrock Edition differences
        if (q.contains("基岩版和java版") || q.contains("java版和基岩版") || q.contains("准连接性") || q.contains("qc") || q.contains("活塞吐方块") || q.contains("基岩版能横扫吗") || q.contains("基岩版副手") || q.contains("基岩版红石区别")) {
            String resp = "§e【Minecraft Java 版 vs 基岩版 (Bedrock) 核心机制差异】§r\n" +
                    "▸ §c战斗机制§r：Java 版武器有攻击冷却 CD，满蓄力横扫之刃 AOE，斧头破盾；基岩版无 CD 可高速连点，无横扫附魔。\n" +
                    "▸ §b副手机制§r：Java 版副手可持几乎任意物品；基岩版副手仅限盾牌、箭矢、图腾、焰火、地图等少数物品。\n" +
                    "▸ §a准连接性 (QC)§r：Java 版支持 QC 且 1-tick 脉冲可使粘性活塞吐出方块；基岩版无 QC，粘性活塞永远黏住方块！";
            return Optional.of(new Resolution(resp, null, "JAVA_BEDROCK_DIFF"));
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
