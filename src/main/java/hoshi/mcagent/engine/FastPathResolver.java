package hoshi.mcagent.engine;

import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.InventorySnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.context.TargetEntity;
import hoshi.mcagent.crafting.CraftingReadinessChecker;

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

        // 0. Context-Aware Crosshair Target Block Mining & Tool Compatibility
        if (context != null && context.targetBlock() != null && !context.targetBlock().isAir()) {
            if (q.contains("这怎么挖") || q.contains("怎么挖眼前") || q.contains("需要什么工具") ||
                    q.contains("用什么工具") || q.contains("手里的工具能挖吗") || q.contains("能掉落吗") ||
                    q.contains("眼前方块") || q.contains("准星方块") || q.contains("挖掘要求")) {
                TargetBlock tb = context.targetBlock();
                TargetBlock.HarvestReport harvest = tb.evaluateHarvest(context.inventory());
                StringBuilder sb = new StringBuilder();
                sb.append(String.format("§6【准星方块挖掘与掉落检测】§r\n"));
                sb.append(String.format("▸ 目标方块：%s at [%d, %d, %d]\n", tb.blockId(), tb.x(), tb.y(), tb.z()));
                sb.append(String.format("▸ 挖掘工具要求：%s (硬度: %.1f)\n", harvest.toolRequirementName(), tb.hardness()));
                sb.append(String.format("▸ 当前手持装备：%s\n", harvest.currentToolStatus()));
                if (harvest.canHarvestWithDrops()) {
                    sb.append(String.format("▸ §a✔ 掉落安全检测通过：符合要求，正常破坏将百分之百产生掉落物！§r\n"));
                } else {
                    sb.append(String.format("▸ §c✖ %s§r\n", harvest.advice()));
                }
                String cmd = harvest.hotbarAlternativeSlot().map(slot ->
                        String.format("/item replace entity @s weapon.mainhand from entity @s hotbar.%d", slot)
                ).orElse(null);
                return Optional.of(new Resolution(sb.toString(), cmd, "TARGET_BLOCK_HARVEST"));
            }

            TargetBlock.LogisticsReport log = context.targetBlock().evaluateLogisticsOrRedstone();
            if (log.isLogisticsOrRedstone()) {
                if (q.contains("为什么不漏") || q.contains("为什么不吸") || q.contains("漏斗锁") ||
                        q.contains("比较器模式") || q.contains("比较器怎么算") || q.contains("红石状态") ||
                        q.contains("为什么不动") || q.contains("眼前红石") || q.contains("眼前漏斗") ||
                        q.contains("这个漏斗") || q.contains("这个比较器") || q.contains("怎么工作") ||
                        q.contains("物流状态") || q.contains("气泡柱怎么不冒泡")) {
                    StringBuilder sb = new StringBuilder();
                    sb.append("§c【准星红石与物流拓扑诊断】§r\n");
                    TargetBlock tb = context.targetBlock();
                    sb.append(String.format("▸ 目标组件：%s at [%d, %d, %d]\n", tb.blockId(), tb.x(), tb.y(), tb.z()));
                    sb.append(String.format("▸ 运行状态：%s\n", log.stateDetails()));
                    sb.append(String.format("▸ 调优建议：%s", log.actionableAdvice()));
                    return Optional.of(new Resolution(sb.toString(), null, "TARGET_BLOCK_LOGISTICS"));
                }
            }
        }

        // 0.1 Context-Aware Crosshair Target Entity Guidance
        if (context != null && context.targetEntity() != null) {
            if (q.contains("眼前生物") || q.contains("准星生物") || q.contains("这个生物") ||
                    q.contains("怎么治愈") || q.contains("怎么救") || q.contains("怎么驯服") ||
                    q.contains("怎么刷狼铠") || q.contains("为什么打我") || q.contains("打不打我")) {
                TargetEntity te = context.targetEntity();
                InventorySnapshot inv = context.inventory();
                StringBuilder sb = new StringBuilder();

                if (te.isZombieVillager()) {
                    sb.append("§d【准星实体：僵尸村民治愈方案】§r\n");
                    sb.append(String.format("▸ 实体生命值：%.1f / %.1f\n", te.health(), te.maxHealth()));
                    boolean hasWeakness = inv != null && (inv.countItem("splash_potion") > 0 || inv.countItem("potion") > 0);
                    boolean hasApple = inv != null && inv.countItem("golden_apple") > 0;
                    if (hasApple) {
                        sb.append("▸ §a背包材料就绪：持有金苹果！向其投掷喷溅虚弱药水后手持金苹果右键投喂即可开始转化。§r\n");
                    } else {
                        sb.append("▸ §e缺少治愈材料：治愈需要【喷溅型虚弱药水】+【普通金苹果】。§r\n");
                    }
                    sb.append("▸ 治愈后将化身为正常村民并提供终生永久交易超低折扣！");
                    return Optional.of(new Resolution(sb.toString(), "/give @s minecraft:golden_apple 1", "TARGET_ENTITY_ZOMBIE_VILLAGER"));
                }

                if (te.isPiglin()) {
                    sb.append("§6【准星实体：下界猪灵中立性感知】§r\n");
                    boolean gold = inv != null && inv.isWearingGoldArmor();
                    if (gold) {
                        sb.append("▸ §a✔ 安全：您当前已穿戴黄金装备，周围猪灵对您保持中立。§r\n");
                        sb.append("▸ 向其丢出金锭即可开始以物易物；切勿在其周围 16 格内开箱或破坏金矿！");
                    } else {
                        sb.append("▸ §c✖ 极度危险：您当前未穿戴任何黄金护甲！猪灵对您处于敌对状态！§r\n");
                        if (inv != null && inv.findHotbarSlot("golden_boots").isPresent()) {
                            sb.append("▸ 提示：快捷栏中检测到金靴子，请立即穿戴！");
                        } else {
                            sb.append("▸ 请尽快穿戴任意 1 件黄金装备平息敌意。");
                        }
                    }
                    return Optional.of(new Resolution(sb.toString(), "/give @s minecraft:golden_boots 1", "TARGET_ENTITY_PIGLIN"));
                }

                if (te.isArmadillo()) {
                    sb.append("§b【准星实体：犰狳刷鳞与狼铠】§r\n");
                    sb.append("▸ 机制：手持刷子 (Brush) 对犰狳右键点击即可无损刷落 1 枚犰狳鳞甲！\n");
                    sb.append("▸ 6 枚犰狳鳞甲可合成狼铠 (Wolf Armor)，吸收驯服狼受到的所有直接伤害。");
                    return Optional.of(new Resolution(sb.toString(), "/give @s minecraft:brush 1", "TARGET_ENTITY_ARMADILLO"));
                }

                if (te.isIronGolem()) {
                    sb.append("§e【准星实体：铁傀儡生命与修复】§r\n");
                    sb.append(String.format("▸ 当前生命值：%.1f / 100.0 (50 颗心)\n", te.health()));
                    sb.append("▸ 维护指南：手持铁锭右键每个可恢复 25 点生命并消除裂纹！切勿攻击它防反杀。");
                    return Optional.of(new Resolution(sb.toString(), "/give @s minecraft:iron_ingot 4", "TARGET_ENTITY_IRON_GOLEM"));
                }
            }
        }

        // 0.2 Inventory Crafting Readiness Checker
        if (q.contains("够做") || q.contains("能做") || q.contains("能合成") || q.contains("够合") || q.contains("材料够") || q.contains("背包够")) {
            var report = CraftingReadinessChecker.evaluate(rawQuery, context != null ? context.inventory() : null);
            if (report.isKnownRecipe()) {
                return Optional.of(new Resolution(report.formattedMessage(), report.suggestedCommand(), "CRAFTING_READINESS"));
            }
        }

        // 1. Nether Portal / Coordinate math
        if (q.contains("地狱坐标") || q.contains("下界坐标") || q.contains("传送门坐标") || q.contains("对应坐标") || q.contains("换算坐标")) {
            return Optional.of(resolveCoordinates(context));
        }

        // 2. Ore depth distribution lookup
        if (q.contains("在几层") || q.contains("在第几层") || q.contains("层数") || q.contains("在哪挖") || q.contains("矿石分布") || q.contains("高度") || (q.contains("怎么挖") && !q.contains("眼前"))) {
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
        if (!q.contains("刷怪塔") && !q.contains("刷怪笼") && !q.contains("刷铁机") && (q.contains("不刷怪") || (q.contains("刷怪") && (q.contains("亮度") || q.contains("条件") || q.contains("为什么") || q.contains("怎么") || q.contains("不生成"))))) {
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
        if (!q.contains("刷铁") && !q.contains("铁傀儡") && !q.contains("补货") && q.contains("村民") && (q.contains("转职") || q.contains("锁") || q.contains("刷") || q.contains("工作台") || q.contains("职业") || q.contains("交易") || q.contains("图书") || q.contains("经验修补"))) {
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
        if ((q.contains("比较器") || q.contains("分类机") || q.contains("物品分类") || q.contains("漏斗分类") || q.contains("22个") || q.contains("22 个") || q.contains("比较器信号") || q.contains("测箱子"))
                && !q.contains("41") && !q.contains("防串线") && !q.contains("为什么不漏") && !q.contains("传输速率") && !q.contains("减法")) {
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
                    "▸ §4过于昂贵§r：生存模式单次操作所需经验 >= 40 级时会被拒绝。\\n\" +\n" +
                    "▸ §a二叉树最优合并法§r：附魔书两两配对合并，最后将合集书一次性打在装备上，避免单线串联导致经验爆炸！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:anvil 1", "ANVIL_OPTIMIZATION"));
        }

        // 15. Brewing Stand & Potions
        if (q.contains("酿造台") || q.contains("药水配方") || q.contains("怎么酿") || q.contains("隐身药水") || q.contains("神龟药水") || q.contains("抗火药水") || q.contains("粗制药水") || q.contains("变异药水")) {
            String resp = "§d【酿造台配方与药水学快速推演】§r\n" +
                    "▸ §e核心底药§r：水瓶 + 下界疣 ➔ 粗制的药水。\\n\" +\n" +
                    "▸ §b主力材料§r：糖➔迅捷；烈焰粉➔力量；金胡萝卜➔夜视；岩浆膏➔抗火；幻翼膜➔缓降；海龟壳➔神龟药水。\\n\" +\n" +
                    "▸ §c发酵蛛眼§r：夜视➔隐身；迅捷/跳跃➔缓慢；治疗/剧毒➔伤害。红石粉延长时长，荧石粉升 II 级，火药制成喷溅。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:brewing_stand 1", "BREWING_RECIPES"));
        }

        // 32. Iron Golem Repair
        if (q.contains("铁傀儡") && (q.contains("修") || q.contains("加血") || q.contains("裂纹") || q.contains("回血") || q.contains("铁锭"))) {
            String resp = "§e【铁傀儡修复维护与村庄防卫】§r\n" +
                    "▸ §e生命值与裂纹§r：拥有 100 点生命值 (50 颗心)；随生命降低呈现 4 阶段肉眼可见裂纹。\n" +
                    "▸ §a铁锭右键修复§r：手持【铁锭】右键铁傀儡，每个铁锭消耗立即恢复 25 点生命值并修复裂纹！\n" +
                    "▸ §c反击戒律§r：单次攻击 7~21 点高额击退伤害；声望低于 -15 或主动攻击会招致致命围攻。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:iron_ingot 4", "IRON_GOLEM_REPAIR"));
        }


        // 16. Iron Golem Spawning & Iron Farm
        if (!q.contains("失眠") && !q.contains("破视") && !q.contains("失效") && (q.contains("铁傀儡") || q.contains("刷铁机") || q.contains("为什么不刷铁") || q.contains("村民惊吓") || q.contains("不生成铁傀儡"))) {
            String resp = "§a【铁傀儡生成判定与刷铁机力学】§r\n" +
                    "▸ §e三大前置条件§r：至少 3 名有效村民绑定床铺；过去 20 分钟内村民必须睡过觉；村民需进入惊吓恐慌态。\\n\" +\n" +
                    "▸ §b生成空间§r：村民中心 16×13×16 空间内需要完整方块表面，上方有 3 格空气或水流。\\n\" +\n" +
                    "▸ §c排查§r：视线受阻无法入睡、附近残留铁傀儡、生成点空间不足，都可能导致不刷铁。";
            return Optional.of(new Resolution(resp, "/summon minecraft:iron_golem", "IRON_GOLEM_MECHANICS"));
        }

        // 17. Nether Portal Linking & Desync
        if (q.contains("传送门对齐") || q.contains("串门") || q.contains("传送门错位") || q.contains("下界门跑偏") || q.contains("双向传送门")) {
            String resp = "§5【下界传送门精准对齐与防串门机制】§r\n" +
                    "▸ §c串门根源§r：下界与主界为 8:1 坐标比例，进门搜索半径高达 128 格，多门会重定向至错误出口。\\n\" +\n" +
                    "▸ §a黄金对齐法§r：主界 [X,Y,Z] 对应下界 [floor(X/8),Y,floor(Z/8)]，在精确点手动搭门并点燃。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:obsidian 14", "PORTAL_LINKING"));
        }

        // 18. Ender Dragon Resummoning & End Gateway / Elytra
        if (q.contains("末影龙") || q.contains("复活龙") || q.contains("折跃门") || q.contains("末地折跃门") || q.contains("末地外岛") || q.contains("鞘翅怎么飞") || q.contains("潜影盒怎么合") || q.contains("龙蛋")) {
            String resp = "§5【末影龙复活、末地折跃门与鞘翅探索】§r\n" +
                    "▸ §e复活末影龙§r：在返回传送门 4 个方向中心各放置 1 个【末影水晶】（共 4 个），水晶光束将重生顶端水晶并孵化末影龙（复活掉落 500 经验，无新龙蛋）。\\n\" +\n" +
                    "▸ §a末地折跃门§r：击杀末影龙后生成 1x1 基岩折跃门，投掷末影珍珠穿透瞬间传送至 1000 格外末地外岛！\\n\" +\n" +
                    "▸ §b鞘翅与火箭§r：末地船物品框获取鞘翅；副手持纯火药+纸合成的烟花火箭推进加速；潜影盒由 2 潜影壳 + 1 木箱合成。";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:end_city", "END_DRAGON_GATEWAY"));
        }

        // 19. Conduit Structure & Power
        if ((q.contains("潮涌核心") || q.contains("潮涌能量") || q.contains("导管怎么激活") || q.contains("潮涌核心怎么摆") || q.contains("海洋之心") || q.contains("鹦鹉螺壳") || q.contains("海晶石框架")) && !q.contains("42") && !q.contains("满级") && !q.contains("三环") && !q.contains("攻击") && !q.contains("电击")) {
            String resp = "§3【潮涌核心搭建与水下主宰力学】§r\n" +
                    "▸ §e核心合成§r：1 个海洋之心（藏宝箱）+ 8 个鹦鹉螺壳（钓鱼或溺尸掉落）。\\n\" +\n" +
                    "▸ §a框架搭建§r：核心置于水中心，用海晶石搭建 5×5 正交环。16 块启动基础范围 32 格，42 块满级范围达 96 格！\\n\" +\n" +
                    "▸ §d主宰效果§r：水下无限呼吸、夜视、挖掘不减速；满级对 8 格内溺尸与守卫者持续造成每 2 秒 4 点伤害！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:conduit 1", "CONDUIT_STRUCTURE"));
        }

        // 20. Raid & Hero of the Village
        if (q.contains("突袭怎么触发") || q.contains("村庄袭击") || q.contains("村庄英雄") || q.contains("唤魔者") || q.contains("不死图腾") || q.contains("破坏兽") || q.contains("袭村") || q.contains("袭击波次")) {
            String resp = "§4【村庄突袭 (Raid) 机制与村庄英雄】§r\n" +
                    "▸ §c触发机制 (1.21)§r：击败巡逻队长掉落不祥之瓶，饮用后进村转化为突袭预兆，30 秒倒计时后爆发袭击！\\n\" +\n" +
                    "▸ §e波次规格§r：简单 3 波、普通 5 波、困难 7 波。卫道士斧头高伤，唤魔者掉落不死图腾，女巫丢药水。\\n\" +\n" +
                    "▸ §a胜利奖赏§r：赋予【村庄英雄】Buff，村民全线打折（最低 1 绿宝石换神装）并投掷礼物！";
            return Optional.of(new Resolution(resp, "/effect give @s minecraft:hero_of_the_village 300 1", "RAID_VILLAGE"));
        }

        // 21. Piglin Bartering & Piglin Brute
        if (q.contains("猪灵交易") || q.contains("以物易物") || q.contains("猪灵蛮兵") || q.contains("为什么猪灵打我") || q.contains("猪灵开箱") || q.contains("猪灵金装") || q.contains("猪灵换末影珍珠")) {
            String resp = "§6【猪灵以物易物与猪灵蛮兵权威力学】§r\n" +
                    "▸ §a穿金防身§r：穿戴至少 1 件黄金装备防普通猪灵敌对。\\n\" +\n" +
                    "▸ §4绝对禁忌§r：破坏金矿/金块，或打开/破坏任何箱子、潜影盒、末影箱、木桶，周围 16 格猪灵全员激怒！\\n\" +\n" +
                    "▸ §e以物易物§r：金锭投掷给成年猪灵，掉落末影珍珠、抗火药水、哭泣的黑曜石、灵魂沙等。\\n\" +\n" +
                    "▸ §c猪灵蛮兵§r：堡垒遗迹专属！免疫金装伪装、绝不交易、不可安抚，必须垫高或熔岩优先击杀！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:gold_ingot 64", "PIGLIN_BARTER"));
        }

        // 22. Enchanting Table Geometry & Bookshelves
        if (q.contains("附魔台摆放") || q.contains("15个书架") || q.contains("30级附魔") || q.contains("附魔台被挡") || q.contains("附魔台怎么摆") || q.contains("砂轮洗附魔") || q.contains("附魔台有效距离")) {
            String resp = "§5【30 级附魔台几何摆放与经验洗炼】§r\n" +
                    "▸ §e书架配置§r：需要恰好 15 个书架，围在附魔台周围水平 2 格距离（留出 1 格空气）。\\n\" +\n" +
                    "▸ §c遮挡禁忌§r：附魔台与书架中间 1 格空气严禁有火把、地毯、雪片等任何方块阻挡，否则附魔等级骤降！\\n\" +\n" +
                    "▸ §b附魔技巧§r：消耗 3 级经验 + 3 青金石；词条不满意用砂轮洗掉非诅咒附魔返还经验并刷新种子。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:enchanting_table 1", "ENCHANTING_TABLE"));
        }

        // 23. Java Edition vs Bedrock Edition differences
        if (q.contains("基岩版和java版") || q.contains("java版和基岩版") || q.contains("准连接性") || q.contains("qc") || q.contains("活塞吐方块") || q.contains("基岩版能横扫吗") || q.contains("基岩版副手") || q.contains("基岩版红石区别")) {
            String resp = "§e【Minecraft Java 版 vs 基岩版 (Bedrock) 核心机制差异】§r\n" +
                    "▸ §c战斗机制§r：Java 版武器有攻击冷却 CD，满蓄力横扫之刃 AOE，斧头破盾；基岩版无 CD 可高速连点，无横扫附魔。\\n\" +\n" +
                    "▸ §b副手机制§r：Java 版副手可持几乎任意物品；基岩版副手仅限盾牌、箭矢、图腾、焰火、地图等少数物品。\\n\" +\n" +
                    "▸ §a准连接性 (QC)§r：Java 版支持 QC 且 1-tick 脉冲可使粘性活塞吐出方块；基岩版无 QC，粘性活塞永远黏住方块！";
            return Optional.of(new Resolution(resp, null, "JAVA_BEDROCK_DIFF"));
        }

        // 24. Sugar Cane / Bamboo Farm Blueprint
        if (q.contains("甘蔗机") || q.contains("竹子机") || q.contains("全自动甘蔗") || q.contains("甘蔗农场") || q.contains("甘蔗怎么做") || q.contains("侦测器甘蔗")) {
            String resp = "§a【全自动甘蔗/竹子机搭建指南】§r\n" +
                    "▸ §e切片结构§r：底层水槽+泥土，中层活塞，顶层侦测器（观察脸朝前看甘蔗第 3 格）。\\n\" +\n" +
                    "▸ §b传导电路§r：活塞背后垫实心方块，上面撒红石粉连接侦测器输出。\\n\" +\n" +
                    "▸ §c避坑提示§r：沙子和泥土种植生长速度完全相同；侦测器切勿装在第 2 格防止频繁空推。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:sugar_cane 64", "SUGAR_CANE_FARM"));
        }

        // 25. Stone / Cobblestone Generator Blueprint
        if (q.contains("刷石机") || q.contains("造石机") || q.contains("刷圆石") || q.contains("刷石头") || q.contains("安全刷石") || q.contains("造石头")) {
            String resp = "§6【高效安全造石机与刷石力学】§r\n" +
                    "▸ §a圆石生成§r：流动水与流动岩浆在同一水平高度对撞。\\n\" +\n" +
                    "▸ §e石头生成§r：岩浆流自上而下注入流动水上方瞬间冷凝（出平滑石）。\\n\" +\n" +
                    "▸ §c防灭大忌§r：水流流速远快于岩浆，水流一侧必须下挖 2 格深坑阻断水势，严禁水流直接冲入岩浆源块！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:lava_bucket 1", "STONE_GENERATOR"));
        }

        // 26. Redstone Clocks & Oscillators
        if (q.contains("红石时钟") || q.contains("漏斗时钟") || q.contains("比较器时钟") || q.contains("脉冲发生器") || q.contains("高频红石") || q.contains("红石脉冲") || q.contains("极速时钟")) {
            String resp = "§c【经典红石时钟与高频脉冲器】§r\n" +
                    "▸ §e极速脉冲§r：比较器打至减法模式（前置火把点亮），后方通电，输出红石线回环引至侧面，输出 1~2 tick 超高频脉冲。\\n\" +\n" +
                    "▸ §b长周期时钟§r：Etho 双漏斗对吸时钟，两端接比较器+粘性活塞推移红石块，放入物品数 × 0.4 秒精确控制周期。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:comparator 1", "REDSTONE_CLOCKS"));
        }

        // 27. Pumpkin / Melon Farm Blueprint
        if (q.contains("南瓜机") || q.contains("西瓜机") || q.contains("全自动南瓜") || q.contains("全自动西瓜") || q.contains("结瓜农场") || q.contains("南瓜农场")) {
            String resp = "§6【全自动南瓜/西瓜机搭建指南】§r\n" +
                    "▸ §e生长原理§r：成熟瓜梗向相邻泥土/草方块结瓜，结瓜瞬间触发方块状态更新。\\n\" +\n" +
                    "▸ §a自动化构型§r：侦测器感应结瓜更新，驱动活塞推碎瓜果（南瓜掉落整瓜，西瓜掉落西瓜片）。\\n\" +\n" +
                    "▸ §b无损收集§r：底层使用漏斗矿车穿透泥土隔空吸物，损耗最低。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:pumpkin_seeds 64", "PUMPKIN_MELON_FARM"));
        }

        // 28. Villager Breeding Dynamics
        if (q.contains("村民繁殖") || q.contains("村民生小村民") || q.contains("村民生孩子") || q.contains("村民不生") || q.contains("村民生小人") || q.contains("村民怎么繁殖") || q.contains("村民床位") || q.contains("村民繁育")) {
            String resp = "§6【村民繁殖与有效床位动力学】§r\n" +
                    "▸ §a有效床位§r：村内有效床位必须多于村民总数；且床头正上方必须留出至少 2 格完整透明/空气高度（供幼年村民跳床寻路判定）！\\n\" +\n" +
                    "▸ §e食物意愿§r：每只村民需消耗 3 面包，或 12 胡萝卜，或 12 马铃薯，或 12 甜菜根。\\n\" +\n" +
                    "▸ §b生长周期§r：幼年村民 20 分钟（24000 ticks）成年，双亲繁育后冷却 5 分钟。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:bread 64", "VILLAGER_BREEDING"));
        }

        // 29. Automatic Villager Crop Farm
        if (q.contains("村民农场") || q.contains("村民农田") || q.contains("全自动农田") || q.contains("农民自动收菜") || q.contains("自动收小麦") || q.contains("自动收胡萝卜") || q.contains("自动收马铃薯")) {
            String resp = "§6【全自动村民农田机制】§r\n" +
                    "▸ §a农民特征§r：只有棕袍农民拥有自动耕作与补种 AI；背包拥有 8 个独立物品槽。\\n\" +\n" +
                    "▸ §e背包防堵§r：入场前主动投喂 8 组单一作物（如胡萝卜）将背包填满，杜绝拾取杂物卡死。\\n\" +\n" +
                    "▸ §b收集方案§r：隔着栅栏向饥饿村民投喂拦截（中间漏斗截取），或耕地下方漏斗矿车穿透吸物。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:carrot 64", "VILLAGER_CROP_FARM"));
        }

        // 30. Smelting & High-Efficiency Fuels
        if (q.contains("熔炼燃料") || q.contains("熔炉燃料") || q.contains("烧矿燃料") || q.contains("最划算的燃料") || q.contains("岩浆桶能烧几个") || q.contains("干海带块能烧几个") || q.contains("熔炼时间") || q.contains("燃料效率")) {
            String resp = "§6【高能自动化燃料与熔炼动力学】§r\n" +
                    "▸ §e标准耗时§r：单件物品熔炼需 200 ticks (10.0 秒)；高炉/烟熏炉减半至 100 ticks。\\n\" +\n" +
                    "▸ §c顶尖热值§r：岩浆桶烧 100 个（返还空桶，最高单体）；煤炭块烧 80 个；干海带块烧 20 个（可再生首选）；烈焰棒 12 个；煤炭 8 个。\\n\" +\n" +
                    "▸ §b熔炉阵列§r：顶端输入原料，侧面输入燃料，底端漏斗抽取成品。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:dried_kelp_block 64", "SMELTING_FUEL_EFFICIENCY"));
        }

        // 31. Zombie Villager Curing
        if (q.contains("僵尸村民") && (q.contains("治愈") || q.contains("变回") || q.contains("怎么救") || q.contains("金苹果") || q.contains("虚弱药水") || q.contains("打折"))) {
            String resp = "§d【僵尸村民治愈机制与永久交易折扣】§r\n" +
                    "▸ §e两大核心道具§r：喷溅型虚弱药水 (Splash Potion of Weakness) + 普通金苹果 (Golden Apple)。\n" +
                    "▸ §a治愈流程§r：先向僵尸村民投掷喷溅虚弱药水，随后手持金苹果右键投喂，伴随剧烈红色粒子抖动；耗时 3~5 分钟 (3600~6000 ticks) 转化完成。\n" +
                    "▸ §b转化加速与保护§r：周围放置铁栏杆与床可微幅加速转化；转化期间其具有力量I且仍会反击，需严密隔离！\n" +
                    "▸ §6永久福利§r：治愈后成为村民并给予永久超低折扣！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:golden_apple 1", "ZOMBIE_VILLAGER_CURE"));
        }

        // 33. Armadillo & Wolf Armor (1.21+)
        if (q.contains("犰狳") || q.contains("狼铠") || q.contains("狼装甲") || q.contains("犰狳鳞甲") || q.contains("刷子")) {
            String resp = "§b【犰狳刷鳞与狼铠防御系统 (1.21+)】§r\n" +
                    "▸ §e犰狳与刷子§r：生成于热带草原与恶地；手持【刷子 (Brush)】右键无损刷取【犰狳鳞甲】，每次耗 16 点刷子耐久。\n" +
                    "▸ §a狼铠制作与染色§r：6 枚犰狳鳞甲合成狼铠，支持染料定制颜色；穿戴于驯服狼身上吸收 100% 直接伤害。\n" +
                    "▸ §b耐久维护§r：狼铠产生裂纹后，手持犰狳鳞甲右键即可原位修复耐久；剪刀右键无损脱下。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:brush 1", "ARMADILLO_WOLF_ARMOR"));
        }

        // 34. Trial Spawner & Breeze (1.21+)
        if (q.contains("旋风人") || q.contains("breeze") || q.contains("试炼刷怪笼") || q.contains("trial spawner") || q.contains("试炼钥匙")) {
            String resp = "§3【试炼刷怪笼与旋风人攻防动力学 (1.21+)】§r\n" +
                    "▸ §e试炼刷怪笼§r：按玩家人数动态调整怪量；清除后喷出试炼钥匙并进入 30 分钟冷却；带灾厄兆头触发重装不祥试炼。\n" +
                    "▸ §c旋风人投射物绝对免疫§r：覆盖风暴气流，【完全反弹弓箭、弩箭、三叉戟等所有远程投射物】！\n" +
                    "▸ §a克制策略§r：盾牌可 100% 弹反风弹；使用重锤/钻石剑等近战武器贴脸速杀。";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:trial_chambers", "TRIAL_SPAWNER_BREEZE"));
        }

        // 35. Hopper Logistics & Anti-Spill Sorter
        if (q.contains("漏斗为什么不漏") || q.contains("漏斗不工作") || q.contains("漏斗锁了") ||
                q.contains("41个") || q.contains("41 物品") || q.contains("防串线") ||
                q.contains("漏斗传输速率") || (q.contains("漏斗") && (q.contains("分类") || q.contains("速率") || q.contains("锁")))) {
            String resp = "§6【漏斗传输力学与防串线分类器】§r\n" +
                    "▸ §e传输规格§r：漏斗固定传输速率为 2.5 组/秒（每 8 游戏刻 / 4 红石刻传输 1 个物品）。\n" +
                    "▸ §c红石锁定警告§r：当漏斗接收到红石充能时立即被锁定 (enabled=false)，停止吸物与漏物！排查紧邻红石粉、火把或充能方块。\n" +
                    "▸ §a防串线 41 物品布局§r：第 1 格放 41 个目标物品，第 2~5 格各放 1 个重命名杂物（合计 45 个输出 2 级信号）；进入第 42 个（合计 46）冲至 3 级信号放行，永不并联串线！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:hopper 5", "HOPPER_LOGISTICS_SORTING"));
        }

        // 36. Comparator Subtraction & Algebra
        if (q.contains("比较器减法") || q.contains("减法模式") || (q.contains("比较器") && (q.contains("怎么算") || q.contains("前置火把") || q.contains("模式区别")))) {
            String resp = "§c【红石比较器减法模式与代数运算】§r\n" +
                    "▸ §e减法模式特征§r：前端单根红石火把点亮（右键切换比较/减法模式）。\n" +
                    "▸ §a减法核心公式§r：输出信号强度 S_out = max(0, S_rear - max(S_left, S_right))。\n" +
                    "▸ §b超频时钟搭建§r：减法模式下，输出端红石线引回侧面输入端，形成自衰减负反馈闭环，产生 1~2 tick 极速高频脉冲！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:comparator 1", "COMPARATOR_SUBTRACTION_ALGEBRA"));
        }

        // 37. Bubble Column Elevator & Water Dynamics
        if (q.contains("水电梯") || q.contains("气泡柱") || q.contains("灵魂沙电梯") || q.contains("岩浆块电梯") ||
                q.contains("气泡柱上不去") || q.contains("海带水源") || q.contains("灵魂沙为什么不冒泡")) {
            String resp = "§3【水力流体动力学与灵魂沙气泡柱电梯】§r\n" +
                    "▸ §b上升与下沉§r：水底灵魂沙产生上升气泡柱 (约 11 格/秒，无限氧气)；岩浆块产生下沉涡流。\n" +
                    "▸ §c水源铁律§r：气泡柱必须在每一格均为【水源 (Water Source)】中形成，流动水绝不冒泡！\n" +
                    "▸ §a海带转化神技§r：垂直管道顶端倒一桶水，底部种植海带催熟插满至顶端，即可将整条流动水瞬间转化为水源；再将底部换为灵魂沙即刻激活！\n" +
                    "▸ §e出入口阻水§r：底部出入口放置告示牌或打开的栅栏门挡水通人。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:soul_sand 1", "WATER_BUBBLE_COLUMN_ELEVATOR"));
        }

        // 38. Observer Clocks & Pulse Mechanics
        if (q.contains("侦测器时钟") || q.contains("侦测器高频") || q.contains("侦测器脉冲") ||
                q.contains("观察者时钟") || q.contains("侦测器怎么摆") || q.contains("粘性活塞吐方块")) {
            String resp = "§4【侦测器脉冲发生与无损时钟调度】§r\n" +
                    "▸ §e侦测与输出§r：前方感应方块状态更新 (BlockState Update)，后侧输出持续 1 红石刻（2 游戏刻 / 0.1s）瞬时脉冲。\n" +
                    "▸ §a面迎面 2-Tick 极速时钟§r：两个侦测器侦测脸紧贴相对放置，互为更新源产生 10Hz 极速振荡！活塞推移其一可作为物理启停开关。\n" +
                    "▸ §bJava 版 1-Tick 吐方块§r：粘性活塞接收 1-tick 极短脉冲时推出方块无暇收回（T-Flip-Flop 双稳态开关）。";
            return Optional.of(new Resolution(resp, "/give @s minecraft:observer 2", "OBSERVER_PULSE_CLOCKS"));
        }


        // 39. Conduit Multiblock Full Power & Defensive Strike
        if (q.contains("潮涌核心42") || q.contains("潮涌核心满级") || q.contains("潮涌核心三环") ||
                q.contains("潮涌核心攻击") || q.contains("潮涌核心电击") || q.contains("潮涌核心放电")) {
            String resp = "§3【潮涌核心多方块环架与水下主宰力学】\n" +
                    "▸ §e激活三要素§r：中心潮涌核心置于 3x3x3 水体中央；外部由 5x5x5 海晶石系方块环绕。\n" +
                    "▸ §b阶梯激活与满级三环§r：最少 16 块启动单环 (32格半径)；满级 42 块构成三环相互垂直闭合框架 (96格半径最大范围)。\n" +
                    "▸ §d防卫电击伤害§r：42 块满级框架下，对 8 格内侵入水体或雨中的敌对生物（溺尸、守卫者等）每 2 秒施加 4 点 (2心) 电击伤害！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:prismarine 42", "CONDUIT_MULTIBLOCK_ACTIVATION"));
        }

        // 40. Nether Portal Geometry & Chunk Loading
        if (q.contains("传送门最小") || q.contains("传送门最大") || q.contains("地狱门尺寸") ||
                q.contains("传送门尺寸") || q.contains("传送门强加载") || q.contains("传送门区块加载")) {
            String resp = "§5【下界传送门几何极值与区块强加载动力学】\n" +
                    "▸ §e几何极值规格§r：内部传送门帷幕最小 2x3（总框架 4x5，四角留空只需 10 块黑曜石），最大 21x21（总框架 23x23）。\n" +
                    "▸ §a点火与熄灭§r：打火石、火焰弹或可燃方块引燃即可点亮；任一黑曜石破损或遭遇爆炸瞬间熄灭。\n" +
                    "▸ §b跨维度常载区块加载器§r：实体/物品穿过传送门时，目标维度对应区块立即获得持续 15 秒（300 ticks）的实体处理强加载！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:obsidian 14", "NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD"));
        }

        // 41. Smelting Array Throughput & Bottleneck
        if (q.contains("熔炉阵列供料") || q.contains("漏斗供料瓶颈") || q.contains("熔炉漏斗跟不上") ||
                q.contains("高炉供料") || q.contains("熔炼阵列瓶颈") || q.contains("熔炉阵列怎么设计")) {
            String resp = "§6【熔炼炉阵列吞吐瓶颈与供料动力学】\n" +
                    "▸ §e单机消耗基准§r：普通熔炉 10.0s/物 (0.1 items/s)；高炉/烟熏炉 5.0s/物 (0.2 items/s)。\n" +
                    "▸ §c单漏斗输送致命瓶颈§r：单漏斗固定吞吐仅为 2.5 items/s！进料主干最多仅能供给 25 台普通熔炉，或仅能供给 12 台满载高炉！\n" +
                    "▸ §a工业级优化拓扑§r：若超过 12 台高炉（如 16 台高炉需 3.2 items/s），必须采用【双漏斗对称并联】(5.0/s，支持 25 台) 或【漏斗矿车穿透极速分流】(20.0/s，支持 100 台)！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:hopper 16", "SMELTING_ARRAY_THROUGHPUT_BOTTLENECK"));
        }

        // 42. Hopper Minecart Unloader Dynamics
        if (q.contains("漏斗矿车卸料") || q.contains("漏斗矿车吸物") || q.contains("漏斗矿车站") ||
                q.contains("漏斗矿车速度") || q.contains("矿车卸料站") || q.contains("漏斗矿车穿透")) {
            String resp = "§e【漏斗矿车穿透吸物与单次往返卸料站动力学】\n" +
                    "▸ §e8倍极速吸物§r：漏斗矿车吸取速率为每 tick 1 个物品 (20 items/s)，为原版漏斗 (2.5/s) 的整整 8 倍！\n" +
                    "▸ §b隔空穿透特性§r：能够隔着正上方 1 个完整实心方块直接吸取上方容器或铁轨表面掉落物。\n" +
                    "▸ §a单次往返极速卸料站§r：矿车驶入停在漏斗上方，比较器检测漏斗非空触发充能铁轨断电锁车；漏斗排空瞬间比较器熄灭，非门恢复铁轨供电弹射矿车巡回！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:hopper_minecart 1", "HOPPER_MINECART_UNLOADER_DYNAMICS"));
        }


        // 43. Hostile Mob Spawn & Despawn Spheres
        if (q.contains("刷怪塔不刷怪") || q.contains("刷怪塔怎么不刷怪") || q.contains("清除球") ||
                q.contains("128格") || q.contains("挂机点怎么选") || q.contains("刷怪半径") ||
                q.contains("mobcap") || q.contains("生物上限")) {
            String resp = "§4【敌对生物生成动力学与 128 格清除球】\n" +
                    "▸ §c四大清除几何球§r：0~24格绝对禁刷；24~32格黄金高频活动圈；33~128格随机清除区(每tick 1/800几率消失)；>128格瞬间蒸发！\n" +
                    "▸ §e单人 70 生物Cap占用§r：挂机点128格内若有未点亮天然矿洞，怪物迅速占满70上限导致刷怪塔断崖式停产！必须高空挂机或照亮洞穴。\n" +
                    "▸ §a基岩低Y轴优势§r：算法从最高方块高度向下抽样，深层挖空基岩(Y=-58)效率比常规地表高 3~4 倍！";
            return Optional.of(new Resolution(resp, "/hoshi mobfarm 120 64 false", "HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES"));
        }

        // 44. Spawner Cage Mechanics & Suppression
        if (q.contains("刷怪笼怎么封") || q.contains("刷怪笼怎么不刷") || q.contains("刷怪笼激活距离") ||
                q.contains("刷怪笼光照") || q.contains("刷怪笼机制") || q.contains("刷怪箱")) {
            String resp = "§6【刷怪笼生成空间与光照压制力学】\n" +
                    "▸ §e激活半径与扫描盒§r：玩家必须在刷怪笼 16 格以内；周围 9x9x3 空间内同类实体 < 6 只方可继续生成。\n" +
                    "▸ §a光照彻底压制§r：1.18+ 普通刷怪笼需方块光照 >= 11 彻底熄灭（刷怪笼各面插火把或红石灯）；烈焰人需 >= 12。\n" +
                    "▸ §b高效收集管道§r：底部铺设流水快速移出 9x9x3 区域，引至 23 格摔落井残血收割或三叉戟杀手自动挂机！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:torch 8", "SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION"));
        }

        // 45. Iron Farm Panic & LOS Sleep Timing
        if (q.contains("刷铁机不刷铁傀儡") || q.contains("刷铁机怎么不刷") || q.contains("刷铁机失效") ||
                q.contains("村民失眠") || q.contains("铁傀儡生成条件") || q.contains("刷铁机僵尸")) {
            String resp = "§3【铁傀儡农场恐慌时序与破视睡眠机制】\n" +
                    "▸ §e刷新硬性三要素§r：至少 3 名村民；在过去 20 分钟内必须入睡过至少 1 tick；目视敌对实体进入恐慌状态。\n" +
                    "▸ §c致命失眠陷阱§r：若僵尸视线未遮挡，村民 24 小时恐慌无法入睡，20分钟后因失眠彻底停产！\n" +
                    "▸ §a破视时序优化§r：必须用活塞遮挡板或水流颠簸进行周期性视线遮断 (LOS Break)，让村民每隔数秒能偷睡 1 tick！";
            return Optional.of(new Resolution(resp, "/hoshi villager iron", "IRON_FARM_PANIC_AND_LOS_SLEEP"));
        }

        // 46. Villager Workstation Pathing & Restocking
        if (q.contains("村民怎么不补货") || q.contains("村民转职") || q.contains("村民怎么转职") ||
                q.contains("村民锁定职业") || q.contains("村民不工作") || q.contains("村民交易锁")) {
            String resp = "§b【村民工作站点路径寻路与交易补货动力学】\n" +
                    "▸ §e物理寻路可达§r：村民必须拥有到达工作站点脚部的物理可行寻路路径，隔着全实心方块或落差断崖无法绑定。\n" +
                    "▸ §c职业永久锁定§r：一旦产生过任何交易（经验 XP > 0），职业与交易树永久锁定，拆除工作台也绝不转职！\n" +
                    "▸ §a补货时钟法则§r：村民每天在日间工作时段 (2000~9000 ticks) 前往工作站至多补货 2 次；接触不到工作台将永久无法补货！";
            return Optional.of(new Resolution(resp, "/hoshi villager trading", "VILLAGER_WORKSTATION_PATHING_AND_RESTOCK"));
        }


        // 47. Anvil Penalty & Binary Tree Optimizer
        if (q.contains("神装怎么合") || q.contains("二叉树附魔合并") || q.contains("铁砧二叉树") || q.contains("铁砧合并方案") || q.contains("附魔书怎么合最省")) {
            String resp = "§6【铁砧累积惩罚与二叉树最优合并规避算法】\n" +
                    "▸ §c指数爆炸惩罚§r：累积惩罚为 2^N - 1 级；单步 >= 40 级直接触发【过于昂贵！】彻底无法锻造。\n" +
                    "▸ §a二叉树合并对数降维§r：将 6~8 本书两两配对合并成复合书，树高压制在 3 层内，最后一次性拍上装备，最终惩罚仅 7 级！\n" +
                    "▸ §e一键规划指令§r：使用 `/hoshi anvil <装备> <附魔1> <附魔2>...` 即可生成零失误单步工序！";
            return Optional.of(new Resolution(resp, "/hoshi anvil netherite_sword sharpness:5 unbreaking:3 mending:1 looting:3", "ANVIL_PENALTY_AND_BINARY_TREE_OPTIMIZER"));
        }

        // 48. Enchantment Compatibility & Gear Rules
        if (q.contains("附魔互斥") || q.contains("精准和时运") || q.contains("无限和经验修补") || q.contains("保护和火保") || q.contains("重锤附魔")) {
            String resp = "§d【附魔互斥矩阵与神装配方验证】\n" +
                    "▸ §e严格互斥对§r：精准采集 vs 时运；无限 vs 经验修补；多重射击 vs 穿透；激流 vs 忠诚/引雷。\n" +
                    "▸ §b护甲四保互斥§r：保护、火焰保护、爆炸保护、弹射物保护不可共存于同一防具。\n" +
                    "▸ §a1.21 重锤专属神装§r：致密 (Density 增伤) + 破甲 (Breach 穿透) + 风爆 (Wind Burst 击中滞空)！";
            return Optional.of(new Resolution(resp, "/give @s minecraft:enchanted_book 1", "ENCHANTMENT_COMPATIBILITY_AND_GEAR_RULES"));
        }

        // 49. Create Stress Capacity & Kinetics
        if (q.contains("create应力") || q.contains("机械动力过载") || q.contains("create转速") || q.contains("蒸汽机配置") || q.contains("齿轮比") || q.contains("应力过载")) {
            String resp = "§e【Create 机械动力学应力网络与过载断裂力学】\n" +
                    "▸ §c过载断裂机制§r：机器消耗 Impact(SU) = kappa * RPM。若总消耗 > 总容量，全线转速归零停摆！\n" +
                    "▸ §b齿轮传动法则§r：大齿轮带小齿轮 2:1 提速但消耗翻倍；小齿轮带大齿轮 1:2 降速消耗减半。\n" +
                    "▸ §a动力阶梯与蒸汽机§r：水轮 256 SU，大水轮 512 SU，风车满配 8,192 SU；18 级超频蒸汽机锅炉最高释放 294,912 SU！";
            return Optional.of(new Resolution(resp, "/hoshi create stress steam 9", "CREATE_STRESS_CAPACITY_AND_KINETICS"));
        }

        // 50. Portal Permaloader & Chunk Ticking
        if (q.contains("常载区块") || q.contains("强加载器") || q.contains("传送门加载器") || q.contains("permaloader") || q.contains("下界门串门") || q.contains("传送门对齐")) {
            String resp = "§b【生电传送门常载网与 Ticket 30 强加载拓扑】\n" +
                    "▸ §e15秒时钟律§r：实体穿越传送门赋予 15.0 秒 (300 ticks) Ticket 30 强加载票；投掷时钟建议控制在 8~12 秒防断流。\n" +
                    "▸ §a三阶辐射圈§r：3x3 实体完全处理区、5x5 方块红石区、7x7 懒惰区。\n" +
                    "▸ §c8:1 坐标对齐§r：实际门偏离理想坐标超过 16 格将诱发单向串门撕裂；使用 `/hoshi chunkloader portal <主界X> <主界Z> <下界X> <下界Z>` 诊断漂移！";
            return Optional.of(new Resolution(resp, "/hoshi chunkloader permaloader 10.0", "PORTAL_PERMALOADER_AND_CHUNK_TICKING"));
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
