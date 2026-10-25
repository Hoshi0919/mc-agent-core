from dataclasses import dataclass
from typing import Optional
from .context import ContextSnapshot
from .rules import (
    LocalGameRules,
    NETHER_PORTAL_RULES,
)


@dataclass(frozen=True)
class Resolution:
    text_response: str
    suggested_command: Optional[str]
    category: str


class FastPathResolver:
    @staticmethod
    def try_resolve(raw_query: str, context: Optional[ContextSnapshot] = None) -> Optional[Resolution]:
        if not raw_query or not raw_query.strip():
            return None
        q = raw_query.strip().lower()

        # 0. Context-Aware Crosshair Target Block Mining
        if context and context.target_block and not context.target_block.is_air:
            if any(k in q for k in ("这怎么挖", "怎么挖眼前", "需要什么工具", "用什么工具", "手里的工具能挖吗", "能掉落吗", "眼前方块", "准星方块", "挖掘要求")):
                tb = context.target_block
                harvest = tb.evaluate_harvest(context.inventory)
                lines = [
                    "§6【准星方块挖掘与掉落检测】§r",
                    f"▸ 目标方块：{tb.block_id} at [{tb.x}, {tb.y}, {tb.z}]",
                    f"▸ 挖掘工具要求：{harvest.tool_requirement_name} (硬度: {tb.hardness:.1f})",
                    f"▸ 当前手持装备：{harvest.current_tool_status}"
                ]
                if harvest.can_harvest_with_drops:
                    lines.append("▸ §a✔ 掉落安全检测通过：符合要求，正常破坏将百分之百产生掉落物！§r")
                else:
                    lines.append(f"▸ §c✖ {harvest.advice}§r")
                cmd = f"/item replace entity @s weapon.mainhand from entity @s hotbar.{harvest.hotbar_alternative_slot}" if harvest.hotbar_alternative_slot is not None else None
                return Resolution(text_response="\n".join(lines), suggested_command=cmd, category="TARGET_BLOCK_HARVEST")

            log = context.target_block.evaluate_logistics_or_redstone()
            if log.is_logistics_or_redstone:
                if any(k in q for k in ("为什么不漏", "为什么不吸", "漏斗锁", "比较器模式", "比较器怎么算", "红石状态", "为什么不动", "眼前红石", "眼前漏斗", "这个漏斗", "这个比较器", "怎么工作", "物流状态", "气泡柱怎么不冒泡")):
                    tb = context.target_block
                    lines = [
                        "§c【准星红石与物流拓扑诊断】§r",
                        f"▸ 目标组件：{tb.block_id} at [{tb.x}, {tb.y}, {tb.z}]",
                        f"▸ 运行状态：{log.state_details}",
                        f"▸ 调优建议：{log.actionable_advice}"
                    ]
                    return Resolution(text_response="\n".join(lines), suggested_command=None, category="TARGET_BLOCK_LOGISTICS")

        # 0.1 Context-Aware Crosshair Target Entity Guidance
        if context and context.target_entity:
            if any(k in q for k in ("眼前生物", "准星生物", "这个生物", "怎么治愈", "怎么救", "怎么驯服", "怎么刷狼铠", "为什么打我", "打不打我")):
                te = context.target_entity
                inv = context.inventory
                if te.is_zombie_villager:
                    lines = [
                        "§d【准星实体：僵尸村民治愈方案】§r",
                        f"▸ 实体生命值：{te.health:.1f} / {te.max_health:.1f}"
                    ]
                    has_apple = inv.has_item("golden_apple", 1) if inv else False
                    if has_apple:
                        lines.append("▸ §a背包材料就绪：持有金苹果！向其投掷喷溅虚弱药水后手持金苹果右键投喂即可开始转化。§r")
                    else:
                        lines.append("▸ §e缺少治愈材料：治愈需要【喷溅型虚弱药水】+【普通金苹果】。§r")
                    lines.append("▸ 治愈后将化身为正常村民并提供终生永久交易超低折扣！")
                    return Resolution(text_response="\n".join(lines), suggested_command="/give @s minecraft:golden_apple 1", category="TARGET_ENTITY_ZOMBIE_VILLAGER")
                elif te.is_piglin:
                    lines = ["§6【准星实体：下界猪灵中立性感知】§r"]
                    if inv and inv.is_wearing_gold_armor:
                        lines.append("▸ §a✔ 安全：您当前已穿戴黄金装备，周围猪灵对您保持中立。§r")
                        lines.append("▸ 向其丢出金锭即可开始以物易物；切勿在其周围 16 格内开箱或破坏金矿！")
                    else:
                        lines.append("▸ §c✖ 极度危险：您当前未穿戴任何黄金护甲！猪灵对您处于敌对状态！§r")
                    return Resolution(text_response="\n".join(lines), suggested_command="/give @s minecraft:golden_boots 1", category="TARGET_ENTITY_PIGLIN")
                elif te.is_armadillo:
                    lines = [
                        "§b【准星实体：犰狳刷鳞与狼铠】§r",
                        "▸ 机制：手持刷子 (Brush) 对犰狳右键点击即可无损刷落 1 枚犰狳鳞甲！",
                        "▸ 6 枚犰狳鳞甲可合成狼铠 (Wolf Armor)，吸收驯服狼受到的所有直接伤害。"
                    ]
                    return Resolution(text_response="\n".join(lines), suggested_command="/give @s minecraft:brush 1", category="TARGET_ENTITY_ARMADILLO")
                elif te.is_iron_golem:
                    lines = [
                        "§e【准星实体：铁傀儡生命与修复】§r",
                        f"▸ 当前生命值：{te.health:.1f} / 100.0 (50 颗心)",
                        "▸ 维护指南：手持铁锭右键每个可恢复 25 点生命并消除裂纹！切勿攻击它防反杀。"
                    ]
                    return Resolution(text_response="\n".join(lines), suggested_command="/give @s minecraft:iron_ingot 4", category="TARGET_ENTITY_IRON_GOLEM")

        # 0.2 Inventory Crafting Readiness
        if any(k in q for k in ("够做", "能做", "能合成", "够合", "材料够", "背包够")):
            report = CraftingReadinessChecker.evaluate(raw_query, context.inventory if context else None)
            if report.is_known_recipe:
                return Resolution(text_response=report.formatted_message, suggested_command=report.suggested_command, category="CRAFTING_READINESS")

        # 1. Nether Portal / Coordinate math
        if any(k in q for k in ("地狱坐标", "下界坐标", "传送门坐标", "对应坐标", "换算坐标")):
            return FastPathResolver._resolve_coordinates(context)

        # 2. Ore depth distribution lookup
        if any(k in q for k in ("在几层", "在第几层", "层数", "在哪挖", "矿石分布", "高度", "怎么挖")):
            ore = LocalGameRules.find_ore(q)
            if ore:
                resp = (
                    f"§6【{ore.name} 生成高度指南 (1.18+)】§r\n"
                    f"▸ 高度区间：Y={ore.min_y} 至 Y={ore.max_y}\n"
                    f"▸ 最优层数：§aY={ore.optimal_y}§r\n"
                    f"▸ 提示：{ore.notes}"
                )
                cmd = f"/waypoint add {ore.name.split()[0]} Y={ore.optimal_y}"
                return Resolution(text_response=resp, suggested_command=cmd, category="ORE_LOOKUP")

        # 3. Mob spawning & light level check
        if not any(k in q for k in ("刷怪塔", "刷怪笼", "刷铁机")) and ("不刷怪" in q or ("刷怪" in q and any(k in q for k in ("亮度", "条件", "为什么", "怎么", "不生成")))):
            lines = ["§b【1.18+ 敌对生物刷怪判定】§r"]
            if context and context.target_block and not context.target_block.is_air:
                tb = context.target_block
                lines.append(
                    f"▸ 您当前注视方块：[{tb.x}, {tb.y}, {tb.z}] | 方块光照：{tb.block_light} | 天空光照：{tb.sky_light}"
                )
                if tb.block_light > 0:
                    lines.append(
                        f"▸ §c注意：当前方块光照为 {tb.block_light} (>=1)，由于 1.18+ 规定方块光照必须为 0，此处绝不可能自然刷怪！§r"
                    )
                else:
                    lines.append("▸ 当前方块光照为 0，满足光照刷怪条件（需检查周围 24~128 格玩家距离及生物群系限制）。")
            else:
                lines.append("▸ 1.18+ 规则：方块内部【方块光照 (Block Light) 必须为 0】才能生成敌对怪！")
            lines.append("▸ 彻底点亮：任意方块光照 >= 1 即安全；刷怪塔必须做到 0 漏光。")
            return Resolution(text_response="\n".join(lines), suggested_command=None, category="MOB_SPAWN_LIGHT")

        # 4. Netherite upgrade (1.20+)
        if "合金" in q and any(k in q for k in ("怎么", "升级", "模板", "锻造", "做", "合")):
            resp = (
                "§6【下界合金装备升级 (1.20+)】§r\n"
                "▸ 1.20+ 锻造台不可直接合！必须放入三样：\n"
                "  ① §e下界合金升级锻造模板§r（堡垒遗迹宝箱获取）\n"
                "  ② 钻石装备/工具\n"
                "  ③ 下界合金锭\n"
                "▸ §a模板复制秘籍§r：工作台放置 7 个钻石 + 1 个下界岩 + 1 个升级模板 ➔ 复制出 2 个模板！"
            )
            return Resolution(
                text_response=resp,
                suggested_command="/locate structure minecraft:bastion_remnant",
                category="NETHERITE_UPGRADE",
            )

        # 5. Mace / Heavy Core (1.21)
        if any(k in q for k in ("重锤", "mace", "重型核心", "旋风棒")):
            resp = (
                "§d【重锤 (Mace) 制作与机制 (1.21)】§r\n"
                "▸ 合成配方：1 个重型核心 (Heavy Core) + 1 个旋风棒 (Breeze Rod)\n"
                "▸ 获取途径：重型核心仅在试炼密室 (Trial Chamber) 的【不祥宝库】用不祥试炼钥匙开启获得\n"
                "▸ 核心特效：坠落攻击伤害随下落高度倍增，击中目标时完全免疫坠落伤害！"
            )
            return Resolution(
                text_response=resp,
                suggested_command="/locate structure minecraft:trial_chambers",
                category="MACE_1_21",
            )

        # 6. Crafter (1.21)
        if any(k in q for k in ("合成器", "自动合成", "crafter")):
            resp = (
                "§b【自动合成器 (Crafter) 指南 (1.21)】§r\n"
                "▸ 激活方式：需要红石脉冲（如时钟信号或侦测器）触发一次合成。\n"
                "▸ 槽位锁定：右键点击 3x3 槽位可禁用该格，使其不接受漏斗漏入物品。\n"
                "▸ 自动化技巧：通过红石比较器检测槽位填满度，满配方后触发脉冲发射成品。"
            )
            return Resolution(text_response=resp, suggested_command=None, category="CRAFTER_1_21")

        # 7. Enchantment conflicts / mutual exclusions
        if any(k in q for k in ("冲突", "互斥", "不能一起")) or ("附魔" in q and any(k in q for k in ("无限", "经验修补", "锋利", "保护", "时运"))):
            resp = (
                "§e【附魔冲突与互斥速查】§r\n"
                "▸ §c弓箭§r：【经验修补】与【无限】互斥，无法共存！\n"
                "▸ §c武器伤害§r：【锋利】/【亡灵杀手】/【节肢杀手】互斥；重锤上【致密】与【破甲】互斥。\n"
                "▸ §c防具防护§r：【保护】/【火焰保护】/【爆炸保护】/【弹射物保护】互斥。\n"
                "▸ §c工具采集§r：【精准采集】与【时运】互斥。\n"
                "▸ §c弩箭特殊§r：【多重射击】与【穿透】互斥；靴子【冰霜行者】与【深海漫游者】互斥。"
            )
            return Resolution(text_response=resp, suggested_command="/enchant @s minecraft:mending", category="ENCHANTMENT_CONFLICT")

        # 8. Villager trade locking & professions
        if not any(k in q for k in ("刷铁", "铁傀儡", "补货")) and "村民" in q and any(k in q for k in ("转职", "锁", "刷", "工作台", "职业", "交易", "图书", "经验修补")):
            resp = (
                "§a【村民职业与锁交易机制】§r\n"
                "▸ §e永久锁定原则§r：只要与村民完成【任意 1 次交易】，其职业和附魔项将永久锁定，敲掉工作台也不会改变！\n"
                "▸ §b无限刷经验修补书技巧§r：在未交易前，放置讲台让无业村民成为图书管理员，检查交易；若不是所需附魔书，空手破坏讲台重放即可无限重置！\n"
                "▸ §f核心工作台对应§r：\n"
                "  - 讲台 ➔ 图书管理员 (附魔书/绿宝石)\n"
                "  - 高炉 ➔ 盔甲匠 | 砂轮 ➔ 武器匠 | 锻造台 ➔ 工具匠\n"
                "  - 制箭台 ➔ 制箭师 (木棍换绿宝石神器)"
            )
            return Resolution(text_response=resp, suggested_command="/locate structure minecraft:village", category="VILLAGER_MECHANICS")

        # 9. Beacon Pyramid structure & layers
        if "信标" in q or ("金字塔" in q and "层" in q) or ("急迫" in q and any(k in q for k in ("2", "二", "ii"))):
            resp = (
                "§b【信标金字塔搭建与效果 (Beacon)】§r\n"
                "▸ §6基座矿物块规格§r（铁/金/绿宝石/钻石/下界合金均可）：\n"
                "  - 1 层：3×3 = 9 块 (范围 20 格，速度I / 急迫I)\n"
                "  - 2 层：5×5+9 = 34 块 (范围 30 格，增加 抗性I / 跳跃I)\n"
                "  - 3 层：7×7+34 = 83 块 (范围 40 格，增加 力量I)\n"
                "  - 4 层满级：9×9+83 = 164 块 (共 2 组+36 块，范围 50 格)\n"
                "▸ §a满级特权§r：解锁【急迫 II】（配合效率V镐实现秒挖深板岩/石头）或副效果【生命恢复 I】！\n"
                "▸ §c注意§r：信标正上方必须无任何不透明方块阻挡直通天空。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:beacon 1", category="BEACON_STRUCTURE")

        # 10. Ominous Bottle & Trial Omen (1.21)
        if ("不祥" in q and any(k in q for k in ("瓶", "兆", "宝库", "钥匙", "密室"))) or "试炼预兆" in q:
            resp = (
                "§5【1.21 不祥之瓶与试炼预兆机制】§r\n"
                "▸ §e不祥之瓶 (Ominous Bottle)§r：击败掠夺者巡逻队旗帜队长掉落瓶子（I~V 级），喝下激活不祥之兆。\n"
                "▸ §d试炼预兆 (Trial Omen)§r：带着不祥之兆接近试炼密室，自动转为试炼预兆！普通刷怪笼升级为【不祥刷怪笼】。\n"
                "▸ §6重型核心获取途径§r：击破不祥刷怪笼掉落【不祥试炼钥匙】，用钥匙开启【不祥宝库】，有概率开出【重型核心 (Heavy Core)】合成重锤！"
            )
            return Resolution(text_response=resp, suggested_command="/locate structure minecraft:trial_chambers", category="OMINOUS_TRIAL_1_21")

        # 11. Warden & Sculk Shrieker
        if any(k in q for k in ("循声守卫", "warden", "监守者", "潜声体", "深暗之域")):
            resp = (
                "§1【循声守卫 (Warden) 触发与应对】§r\n"
                "▸ §c召唤条件§r：自然生成的幽匿潜声体 (Sculk Shrieker) 被激活 4 次（潜声警告等级达到 4）时破土而出！\n"
                "▸ §4极度危险数据§r：生命值高达 500 点 (250心)；近战单击 30 伤害 (15心)；远程声波尖啸穿甲穿墙造成 10 点魔法伤害。\n"
                "▸ §a克制技巧§r：\n"
                "  - 【羊毛】和地毯能 100% 阻隔振动波传导；\n"
                "  - 始终保持潜行 (Shift) 移动；\n"
                "  - 投掷雪球或箭矢向远处方块发出声音诱敌，切勿硬拼！"
            )
            return Resolution(text_response=resp, suggested_command="/locate structure minecraft:ancient_city", category="WARDEN_MECHANICS")

        # 12. Copper Waxing & Scraping
        if "铜" in q and any(k in q for k in ("蜡", "锈", "氧化", "绿")):
            resp = (
                "§6【铜块氧化、打蜡与除锈指南】§r\n"
                "▸ §e4 阶段氧化§r：未锈蚀 (亮橙) ➔ 斑驳 (暗橙带绿) ➔ 锈蚀 (绿带橙) ➔ 氧化 (青绿)。\n"
                "▸ §a打蜡保色§r：手持【蜜脾 (Honeycomb)】右键点击铜块，即可锁定当前颜色（涂蜡的铜块），不再继续生锈。\n"
                "▸ §c刮蜡与除锈§r：手持【任意斧头 (Axe)】右键点击剥除蜡层，再次右键可回退一个生锈等级。\n"
                "▸ §b雷击奇效§r：附近立引雷针，雷电放电可大面积震落周围铜块的铜锈！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:honeycomb 64", category="COPPER_WAXING")

        # 13. Comparator & Container Fill / Item Sorter
        if any(k in q for k in ("比较器", "分类机", "物品分类", "漏斗分类", "22个", "比较器信号", "测箱子")) and not any(k in q for k in ("41", "防串线", "为什么不漏", "传输速率", "减法")):
            resp = (
                "§c【红石比较器容器信号与分类机数学】§r\n"
                "▸ §e容器满度公式§r：Signal = floor(1 + (sum(count / max_stack) / slots) * 14)（空容器输出 0）。\n"
                "▸ §a经典 22 物品分类漏斗 (18-1-1-1-1)§r：\n"
                "  - 第 1 格放 18 个待分类物品，第 2~5 格各放 1 个重命名杂物（占位符）。\n"
                "  - 刚好 22 个物品时输出红石信号 1；进入第 23 个物品时升至 2，点亮红石线解锁下层漏斗漏出 1 个物品，随后复位！\n"
                "▸ §b防串线 41 物品布局§r：若堵塞导致积存 45+ 物品可能冲至 3 格信号串线，可用 3 长度红石线做物理隔离。\n"
                "▸ §d1.21 自动合成器 (Crafter)§r：比较器输出强度精准等于被禁用或有物品的槽位总数 (0~9)！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:comparator 1", category="COMPARATOR_SORTING")

        # 14. Anvil Prior Work Penalty & Binary Tree Merge
        if any(k in q for k in ("铁砧", "过于昂贵", "经验惩罚", "二叉树附魔", "附魔省经验", "修装备太贵")):
            resp = (
                "§6【铁砧累积惩罚与二叉树最优附魔】§r\n"
                "▸ §c累积惩罚公式 (Prior Work)§r：物品每在铁砧操作一次，附加消耗指数暴涨：2^n - 1（0 ➔ 1 ➔ 3 ➔ 7 ➔ 15 ➔ 31 ➔ 63 级）！\n"
                "▸ §4“过于昂贵”死锁§r：生存模式下单次操作所需经验 >= 40 级，游戏将强制锁死不可操作！\n"
                "▸ §a二叉树最优合并法 (Binary Tree Merge)§r：\n"
                "  - 严禁单线串行（先打书1再打书2再打书3...到第6本必爆 40 级）！\n"
                "  - 正确做法：两两配对合并附魔书（书A+书B ➔ 书AB；书C+书D ➔ 书CD；书AB+书CD ➔ 最终合集书），最后将合集书一次性打在装备上，经验暴省 60%+ 且永不超标！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:anvil 1", category="ANVIL_OPTIMIZATION")

        # 15. Brewing Stand & Potions
        if any(k in q for k in ("酿造台", "药水配方", "怎么酿", "隐身药水", "神龟药水", "抗火药水", "粗制药水", "变异药水")):
            resp = (
                "§d【酿造台配方与药水学快速推演】§r\n"
                "▸ §e核心底药§r：水瓶 + 下界疣 ➔ 粗制的药水 (Awkward Potion)。\n"
                "▸ §b主力效果材料§r：\n"
                "  - 糖 ➔ 迅捷 | 烈焰粉 ➔ 力量 | 兔子脚 ➔ 跳跃 | 闪烁西瓜 ➔ 治疗 | 蜘蛛眼 ➔ 剧毒\n"
                "  - 金胡萝卜 ➔ 夜视 | 岩浆膏 ➔ 抗火 | 河豚 ➔ 水下呼吸 | 幻翼膜 ➔ 缓降\n"
                "  - 海龟壳 ➔ 神龟药水 (缓慢IV + 抗性III) | 旋风棒 ➔ 1.21 蓄风药水\n"
                "▸ §c发酵蛛眼变异反转§r：夜视 ➔ 隐身；迅捷/跳跃 ➔ 缓慢；治疗/剧毒 ➔ 伤害 (Harming)。\n"
                "▸ §f调节剂§r：红石粉延长时长；荧石粉升为 II 级；火药制成喷溅药水；龙息制成滞留药水。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:brewing_stand 1", category="BREWING_RECIPES")

        # 32. Iron Golem Repair
        if "铁傀儡" in q and any(k in q for k in ("修", "加血", "裂纹", "回血", "铁锭")):
            resp = (
                "§e【铁傀儡修复维护与村庄防卫】§r\n"
                "▸ §e生命值与裂纹§r：拥有 100 点生命值 (50 颗心)；随生命降低呈现 4 阶段肉眼可见裂纹。\n"
                "▸ §a铁锭右键修复§r：手持【铁锭】右键铁傀儡，每个铁锭消耗立即恢复 25 点生命值并修复裂纹！\n"
                "▸ §c反击戒律§r：单次攻击 7~21 点高额击退伤害；声望低于 -15 或主动攻击会招致致命围攻。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:iron_ingot 4", category="IRON_GOLEM_REPAIR")

        # 16. Iron Golem Spawning & Iron Farm
        if not any(k in q for k in ("失眠", "破视", "失效")) and any(k in q for k in ("铁傀儡", "刷铁机", "为什么不刷铁", "村民惊吓", "不生成铁傀儡")):
            resp = (
                "§a【铁傀儡生成判定与刷铁机力学】§r\n"
                "▸ §e三大必备前置条件§r：\n"
                "  ① 至少 3 名有效村民绑定床铺；\n"
                "  ② 过去 20 分钟内（24000 Tick）村民必须曾睡过觉（哪怕躺下 1 刻即醒）；\n"
                "  ③ 惊吓恐慌态：村民视线 8 格水平（或 16 格通视）内目击僵尸/灾厄村民。\n"
                "▸ §b生成空间检测§r：以村民为中心 16×13×16 空间内必须有完整方块表面，且上方有 3 格空气或水流空间。\n"
                "▸ §c常见不刷怪排查§r：村民长时间无法入睡（视线受阻或恐惧时间过长）、上方空间不足 3 格高、附近 16 格内存在遗留铁傀儡未清除。"
            )
            return Resolution(text_response=resp, suggested_command="/summon minecraft:iron_golem", category="IRON_GOLEM_MECHANICS")

        # 17. Nether Portal Linking & Desync
        if any(k in q for k in ("传送门对齐", "串门", "传送门错位", "下界门跑偏", "双向传送门")):
            resp = (
                "§5【下界传送门精准对齐与防串门机制】§r\n"
                "▸ §c串门根源§r：下界与主界为 8:1 坐标比例，游戏进门搜索半径高达 128 格（对应主界 1024 格！）。若未精确手动校准，多扇门会错误重定向至同一出口。\n"
                "▸ §a黄金对齐法则§r：\n"
                "  - 主界记下门底脚坐标：[X, Y, Z]；\n"
                "  - 进入下界后，敲掉自动生成的门，手动移步至精确对应点：[floor(X/8), Y, floor(Z/8)] 搭建新门并点燃；\n"
                "  - 垂直高度 Y 尽量保持一致，杜绝任何串门与重定向偏差！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:obsidian 14", category="PORTAL_LINKING")

        # 18. Ender Dragon Resummoning & End Gateway / Elytra
        if any(k in q for k in ("末影龙", "复活龙", "折跃门", "末地折跃门", "末地外岛", "鞘翅怎么飞", "潜影盒怎么合", "龙蛋")):
            resp = (
                "§5【末影龙复活、末地折跃门与鞘翅探索】§r\n"
                "▸ §e复活末影龙§r：在末地中央返回传送门基岩池边缘的 4 个方向中心各放置 1 个【末影水晶】（共 4 个），水晶光束将重生黑曜石柱顶水晶并孵化末影龙（复活击杀奖励 500 经验，无新龙蛋）。\n"
                "▸ §a末地折跃门 (End Gateway)§r：击杀末影龙后生成的浮空 1x1 基岩折跃门，投掷末影珍珠穿透即可瞬间跨越 1000 格到达末地外岛！\n"
                "▸ §b鞘翅与动力火箭§r：\n"
                "  - 鞘翅位于外岛末地船船头物品展示框内；\n"
                "  - 滑翔时副手手持【纯纸+火药合成的烟花火箭】（无爆炸星，飞行时间 1~3）右键提供喷射加速；\n"
                "  - 潜影盒：2 个潜影壳 + 1 个木箱合成，打破保留内部物品的便携神包！"
            )
            return Resolution(text_response=resp, suggested_command="/locate structure minecraft:end_city", category="END_DRAGON_GATEWAY")

        # 19. Conduit Structure & Power
        if any(k in q for k in ("潮涌核心", "潮涌能量", "导管怎么激活", "潮涌核心怎么摆", "海洋之心", "鹦鹉螺壳", "海晶石框架")) and not any(k in q for k in ("42", "满级", "三环", "攻击", "电击")):
            resp = (
                "§3【潮涌核心搭建与水下主宰力学】§r\n"
                "▸ §e核心合成§r：1 个【海洋之心】（埋藏的宝藏箱）+ 8 个【鹦鹉螺壳】（钓鱼或溺尸掉落）。\n"
                "▸ §a海晶石环形框架搭建§r：\n"
                "  - 核心置于水中心（5×5×5 水域中）；\n"
                "  - 外围用海晶石/海晶石砖/暗海晶石/海晶灯搭建 5×5 的正交环；\n"
                "  - §b16 块方块 (单环)§r：启动基础潮涌能量，作用半径 32 格；\n"
                "  - §642 块方块 (三环满级)§r：作用半径满载至 §a96 格§r！\n"
                "▸ §d主宰效果§r：水下无限呼吸、水下高清晰夜视、挖掘不减速；满级框架对 8 格内溺尸与守卫者持续造成每 2 秒 4 点穿透伤害！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:conduit 1", category="CONDUIT_STRUCTURE")

        # 20. Raid & Hero of the Village
        if any(k in q for k in ("突袭怎么触发", "村庄袭击", "村庄英雄", "唤魔者", "不死图腾", "破坏兽", "袭村", "袭击波次")):
            resp = (
                "§4【村庄突袭 (Raid) 机制与村庄英雄】§r\n"
                "▸ §c触发机制 (1.21)§r：击败巡逻队长掉落【不祥之瓶】，饮用后进村转化为【突袭预兆 (Raid Omen)】，30 秒倒计时后爆发袭击！\n"
                "▸ §e波次规格§r：简单难度 3 波、普通难度 5 波、困难难度 7 波。\n"
                "▸ §b高危怪物威胁§r：\n"
                "  - 卫道士：高移速铁斧重劈，近战爆发极高；\n"
                "  - 唤魔者：地刺与穿墙恼鬼 (Vex)，击杀掉落神级保命物【不死图腾 (Totem of Undying)】；\n"
                "  - 女巫：远程丢剧毒与迟缓药水，治疗友军；破坏兽冲撞击退。\n"
                "▸ §a胜利奖赏§r：全村欢呼赋予【村庄英雄 (Hero of the Village)】，村民全线打折（最低 1 绿宝石换神装）并向你抛洒礼物！"
            )
            return Resolution(text_response=resp, suggested_command="/effect give @s minecraft:hero_of_the_village 300 1", category="RAID_VILLAGE")

        # 21. Piglin Bartering & Piglin Brute
        if any(k in q for k in ("猪灵交易", "以物易物", "猪灵蛮兵", "为什么猪灵打我", "猪灵开箱", "猪灵金装", "猪灵换末影珍珠")):
            resp = (
                "§6【猪灵以物易物与猪灵蛮兵权威力学】§r\n"
                "▸ §a穿金防身§r：身上穿戴至少 1 件黄金装备（金头盔/金靴等），普通成年猪灵便不会主动攻击。\n"
                "▸ §4绝对禁忌（瞬间激怒）§r：\n"
                "  - 破坏任何金块或金矿；\n"
                "  - 打开或破坏任何【箱子、潜影盒、末影箱、木桶、陷阱箱】，周围 16 格所有猪灵立刻全员敌对追杀！\n"
                "▸ §e以物易物 (Bartering)§r：右键或丢给猪灵金锭，掉落末影珍珠 (大量获取主途径)、抗火药水、哭泣的黑曜石、黑曜石、灵魂沙、魂疾铁靴等。\n"
                "▸ §c猪灵蛮兵 (Piglin Brute)§r：堡垒遗迹专属！【免疫金装伪装、绝不交易、不可安抚】，伤害极高，必须用垫高或熔岩优先铲除！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:gold_ingot 64", category="PIGLIN_BARTER")

        # 22. Enchanting Table Geometry & Bookshelves
        if any(k in q for k in ("附魔台摆放", "15个书架", "30级附魔", "附魔台被挡", "附魔台怎么摆", "砂轮洗附魔", "附魔台有效距离")):
            resp = (
                "§5【30 级附魔台几何摆放与经验洗炼】§r\n"
                "▸ §e书架配置规格§r：需要恰好 §a15 个书架§r，围在附魔台周围水平 2 格距离（与附魔台相隔 1 格空气）。常见为 5×5 外圈留 1 格缺口进出。\n"
                "▸ §c致命遮挡禁忌§r：附魔台与书架中间的 1 格空气空间必须【完全洁净】！不能有任何火把、地毯、雪片、红石、花草等阻碍视线，否则直接阻断吸收符文，导致附魔等级骤跌！\n"
                "▸ §b附魔与重置技巧§r：\n"
                "  - 3 级最高附魔消耗 3 级经验 + 3 个青金石（要求角色达 30 级）；\n"
                "  - 若词条不满意，可在【砂轮 (Grindstone)】上洗掉所有非诅咒附魔并返还部分经验，或附魔 1 级木棒/废书刷新词条种子。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:enchanting_table 1", category="ENCHANTING_TABLE")

        # 23. Java Edition vs Bedrock Edition differences
        if any(k in q for k in ("基岩版和java版", "java版和基岩版", "准连接性", "qc", "活塞吐方块", "基岩版能横扫吗", "基岩版副手", "基岩版红石区别")):
            resp = (
                "§e【Minecraft Java 版 vs 基岩版 (Bedrock) 核心机制差异】§r\n"
                "▸ §c战斗机制§r：Java 版武器具有攻击冷却 CD，满蓄力挥剑触发【横扫之刃】AOE，斧头破盾 5 秒；基岩版无冷却槽可高速连点输出，无横扫附魔。\n"
                "▸ §b副手机制§r：Java 版副手可放置火把、食物、方块、工具、烟花等任意物品；基岩版副手仅限盾牌、箭矢、图腾、焰火、地图等少数物品。\n"
                "▸ §a红石准连接性 (QC)§r：\n"
                "  - Java 版活塞/发射器可被上方或斜上方红石间接激发（需 BUD 方块更新），1-tick 脉冲可使粘性活塞吐出或吸回方块；\n"
                "  - 基岩版完全不支持准连接性 (No QC)，活塞运动更严格，粘性活塞永远黏住方块不吐出！"
            )
            return Resolution(text_response=resp, suggested_command=None, category="JAVA_BEDROCK_DIFF")

        
        # 24. Sugar Cane / Bamboo Farm Blueprint
        if any(k in q for k in ("甘蔗机", "竹子机", "全自动甘蔗", "甘蔗农场", "甘蔗怎么做", "侦测器甘蔗")):
            resp = (
                "§a【全自动甘蔗/竹子机搭建指南】§r\n"
                "▸ §e切片结构§r：底层水槽+泥土，中层活塞，顶层侦测器（观察脸朝前看甘蔗第 3 格）。\n"
                "▸ §b传导电路§r：活塞背后垫实心方块，上面撒红石粉连接侦测器输出。\n"
                "▸ §c避坑提示§r：沙子和泥土种植生长速度完全相同；侦测器切勿装在第 2 格防止频繁空推。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:sugar_cane 64", category="SUGAR_CANE_FARM")

        # 25. Stone / Cobblestone Generator Blueprint
        if any(k in q for k in ("刷石机", "造石机", "刷圆石", "刷石头", "安全刷石", "造石头")):
            resp = (
                "§6【高效安全造石机与刷石力学】§r\n"
                "▸ §a圆石生成§r：流动水与流动岩浆在同一水平高度对撞。\n"
                "▸ §e石头生成§r：岩浆流自上而下注入流动水上方瞬间冷凝（出平滑石）。\n"
                "▸ §c防灭大忌§r：水流流速远快于岩浆，水流一侧必须下挖 2 格深坑阻断水势，严禁水流直接冲入岩浆源块！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:lava_bucket 1", category="STONE_GENERATOR")

        # 26. Redstone Clocks & Oscillators
        if any(k in q for k in ("红石时钟", "漏斗时钟", "比较器时钟", "脉冲发生器", "高频红石", "红石脉冲")):
            resp = (
                "§c【经典红石时钟与高频脉冲器】§r\n"
                "▸ §e极速脉冲§r：比较器打至减法模式（前置火把点亮），后方通电，输出红石线回环引至侧面，输出 1~2 tick 超高频脉冲。\n"
                "▸ §b长周期时钟§r：Etho 双漏斗对吸时钟，两端接比较器+粘性活塞推移红石块，放入物品数 × 0.4 秒精确控制周期。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:comparator 1", category="REDSTONE_CLOCKS")

        # 27. Pumpkin / Melon Farm Blueprint
        if any(k in q for k in ("南瓜机", "西瓜机", "全自动南瓜", "全自动西瓜", "结瓜农场", "南瓜农场")):
            resp = (
                "§6【全自动南瓜/西瓜机搭建指南】§r\n"
                "▸ §e生长原理§r：成熟瓜梗向相邻泥土/草方块结瓜，结瓜瞬间触发方块状态更新。\n"
                "▸ §a自动化构型§r：侦测器感应结瓜更新，驱动活塞推碎瓜果（南瓜掉落整瓜，西瓜掉落西瓜片）。\n"
                "▸ §b无损收集§r：底层使用漏斗矿车穿透泥土隔空吸物，损耗最低。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:pumpkin_seeds 64", category="PUMPKIN_MELON_FARM")

        # 28. Villager Breeding Dynamics
        if any(k in q for k in ("村民繁殖", "村民生小村民", "村民生孩子", "村民不生", "村民生小人", "村民怎么繁殖", "村民床位")):
            resp = (
                "§6【村民繁殖与有效床位动力学】§r\n"
                "▸ §a有效床位§r：村内有效床位必须多于村民总数；且床头正上方必须留出至少 2 格完整透明/空气高度（供幼年村民跳床寻路判定）！\n"
                "▸ §e食物意愿§r：每只村民需消耗 3 面包，或 12 胡萝卜，或 12 马铃薯，或 12 甜菜根。\n"
                "▸ §b生长周期§r：幼年村民 20 分钟（24000 ticks）成年，双亲繁育后冷却 5 分钟。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:bread 64", category="VILLAGER_BREEDING")

        # 29. Automatic Villager Crop Farm
        if any(k in q for k in ("村民农场", "村民农田", "全自动农田", "农民自动收菜", "自动收小麦", "自动收胡萝卜", "自动收马铃薯")):
            resp = (
                "§6【全自动村民农田机制】§r\n"
                "▸ §a农民特征§r：只有棕袍农民拥有自动耕作与补种 AI；背包拥有 8 个独立物品槽。\n"
                "▸ §e背包防堵§r：入场前主动投喂 8 组单一作物（如胡萝卜）将背包填满，杜绝拾取杂物卡死。\n"
                "▸ §b收集方案§r：隔着栅栏向饥饿村民投喂拦截（中间漏斗截取），或耕地下方漏斗矿车穿透吸物。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:carrot 64", category="VILLAGER_CROP_FARM")

        # 30. Smelting & High-Efficiency Fuels
        if any(k in q for k in ("熔炼燃料", "熔炉燃料", "烧矿燃料", "最划算的燃料", "岩浆桶能烧几个", "干海带块能烧几个", "熔炼时间", "燃料效率")):
            resp = (
                "§6【高能自动化燃料与熔炼动力学】§r\n"
                "▸ §e标准耗时§r：单件物品熔炼需 200 ticks (10.0 秒)；高炉/烟熏炉减半至 100 ticks。\n"
                "▸ §c顶尖热值§r：岩浆桶烧 100 个（返还空桶，最高单体）；煤炭块烧 80 个；干海带块烧 20 个（可再生首选）；烈焰棒 12 个；煤炭 8 个。\n"
                "▸ §b熔炉阵列§r：顶端输入原料，侧面输入燃料，底端漏斗抽取成品。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:dried_kelp_block 64", category="SMELTING_FUEL_EFFICIENCY")

        # 31. Zombie Villager Curing
        if "僵尸村民" in q and any(k in q for k in ("治愈", "变回", "怎么救", "金苹果", "虚弱药水", "打折")):
            resp = (
                "§d【僵尸村民治愈机制与永久交易折扣】§r\n"
                "▸ §e两大核心道具§r：喷溅型虚弱药水 (Splash Potion of Weakness) + 普通金苹果 (Golden Apple)。\n"
                "▸ §a治愈流程§r：先向僵尸村民投掷喷溅虚弱药水，随后手持金苹果右键投喂，伴随剧烈红色粒子抖动；耗时 3~5 分钟 (3600~6000 ticks) 转化完成。\n"
                "▸ §b转化加速与保护§r：周围放置铁栏杆与床可微幅加速转化；转化期间其具有力量I且仍会反击，需严密隔离！\n"
                "▸ §6永久福利§r：治愈后成为村民并给予永久超低折扣！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:golden_apple 1", category="ZOMBIE_VILLAGER_CURE")



        # 33. Armadillo & Wolf Armor (1.21+)
        if any(k in q for k in ("犰狳", "狼铠", "狼装甲", "犰狳鳞甲", "刷子")):
            resp = (
                "§b【犰狳刷鳞与狼铠防御系统 (1.21+)】§r\n"
                "▸ §e犰狳与刷子§r：生成于热带草原与恶地；手持【刷子 (Brush)】右键无损刷取【犰狳鳞甲】，每次耗 16 点刷子耐久。\n"
                "▸ §a狼铠制作与染色§r：6 枚犰狳鳞甲合成狼铠，支持染料定制颜色；穿戴于驯服狼身上吸收 100% 直接伤害。\n"
                "▸ §b耐久维护§r：狼铠产生裂纹后，手持犰狳鳞甲右键即可原位修复耐久；剪刀右键无损脱下。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:brush 1", category="ARMADILLO_WOLF_ARMOR")

        # 34. Trial Spawner & Breeze (1.21+)
        if any(k in q for k in ("旋风人", "breeze", "试炼刷怪笼", "trial spawner", "试炼钥匙")):
            resp = (
                "§3【试炼刷怪笼与旋风人攻防动力学 (1.21+)】§r\n"
                "▸ §e试炼刷怪笼§r：按玩家人数动态调整怪量；清除后喷出试炼钥匙并进入 30 分钟冷却；带灾厄兆头触发重装不祥试炼。\n"
                "▸ §c旋风人投射物绝对免疫§r：覆盖风暴气流，【完全反弹弓箭、弩箭、三叉戟等所有远程投射物】！\n"
                "▸ §a克制策略§r：盾牌可 100% 弹反风弹；使用重锤/钻石剑等近战武器贴脸速杀。"
            )
            return Resolution(text_response=resp, suggested_command="/locate structure minecraft:trial_chambers", category="TRIAL_SPAWNER_BREEZE")

        # 35. Hopper Logistics & Anti-Spill Sorter
        if any(k in q for k in ("漏斗为什么不漏", "漏斗不工作", "漏斗锁了", "41个", "41 物品", "防串线", "漏斗传输速率")) or ("漏斗" in q and any(k in q for k in ("分类", "速率", "锁"))):
            resp = (
                "§6【漏斗传输力学与防串线分类器】§r\n"
                "▸ §e传输规格§r：漏斗固定传输速率为 2.5 组/秒（每 8 游戏刻 / 4 红石刻传输 1 个物品）。\n"
                "▸ §c红石锁定警告§r：当漏斗接收到红石充能时立即被锁定 (enabled=false)，停止吸物与漏物！排查紧邻红石粉、火把或充能方块。\n"
                "▸ §a防串线 41 物品布局§r：第 1 格放 41 个目标物品，第 2~5 格各放 1 个重命名杂物（合计 45 个输出 2 级信号）；进入第 42 个（合计 46）冲至 3 级信号放行，永不并联串线！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:hopper 5", category="HOPPER_LOGISTICS_SORTING")

        # 36. Comparator Subtraction & Algebra
        if any(k in q for k in ("比较器减法", "减法模式")) or ("比较器" in q and any(k in q for k in ("怎么算", "前置火把", "模式区别"))):
            resp = (
                "§c【红石比较器减法模式与代数运算】§r\n"
                "▸ §e减法模式特征§r：前端单根红石火把点亮（右键切换比较/减法模式）。\n"
                "▸ §a减法核心公式§r：输出信号强度 S_out = max(0, S_rear - max(S_left, S_right))。\n"
                "▸ §b超频时钟搭建§r：减法模式下，输出端红石线引回侧面输入端，形成自衰减负反馈闭环，产生 1~2 tick 极速高频脉冲！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:comparator 1", category="COMPARATOR_SUBTRACTION_ALGEBRA")

        # 37. Bubble Column Elevator & Water Dynamics
        if any(k in q for k in ("水电梯", "气泡柱", "灵魂沙电梯", "岩浆块电梯", "气泡柱上不去", "海带水源", "灵魂沙为什么不冒泡")):
            resp = (
                "§3【水力流体动力学与灵魂沙气泡柱电梯】§r\n"
                "▸ §b上升与下沉§r：水底灵魂沙产生上升气泡柱 (约 11 格/秒，无限氧气)；岩浆块产生下沉涡流。\n"
                "▸ §c水源铁律§r：气泡柱必须在每一格均为【水源 (Water Source)】中形成，流动水绝不冒泡！\n"
                "▸ §a海带转化神技§r：垂直管道顶端倒一桶水，底部种植海带催熟插满至顶端，即可将整条流动水瞬间转化为水源；再将底部换为灵魂沙即刻激活！\n"
                "▸ §e出入口阻水§r：底部出入口放置告示牌或打开的栅栏门挡水通人。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:soul_sand 1", category="WATER_BUBBLE_COLUMN_ELEVATOR")

        # 38. Observer Clocks & Pulse Mechanics
        if any(k in q for k in ("侦测器时钟", "侦测器高频", "侦测器脉冲", "观察者时钟", "侦测器怎么摆", "粘性活塞吐方块")):
            resp = (
                "§4【侦测器脉冲发生与无损时钟调度】§r\n"
                "▸ §e侦测与输出§r：前方感应方块状态更新 (BlockState Update)，后侧输出持续 1 红石刻（2 游戏刻 / 0.1s）瞬时脉冲。\n"
                "▸ §a面迎面 2-Tick 极速时钟§r：两个侦测器侦测脸紧贴相对放置，互为更新源产生 10Hz 极速振荡！活塞推移其一可作为物理启停开关。\n"
                "▸ §bJava 版 1-Tick 吐方块§r：粘性活塞接收 1-tick 极短脉冲时推出方块无暇收回（T-Flip-Flop 双稳态开关）。"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:observer 2", category="OBSERVER_PULSE_CLOCKS")


        # 39. Conduit Multiblock Full Power & Defensive Strike
        if any(k in q for k in ("潮涌核心42", "潮涌核心满级", "潮涌核心三环", "潮涌核心攻击", "潮涌核心电击", "潮涌核心放电")):
            resp = (
                "§3【潮涌核心多方块环架与水下主宰力学】\n"
                "▸ §e激活三要素§r：中心潮涌核心置于 3x3x3 水体中央；外部由 5x5x5 海晶石系方块环绕。\n"
                "▸ §b阶梯激活与满级三环§r：最少 16 块启动单环 (32格半径)；满级 42 块构成三环相互垂直闭合框架 (96格半径最大范围)。\n"
                "▸ §d防卫电击伤害§r：42 块满级框架下，对 8 格内侵入水体或雨中的敌对生物（溺尸、守卫者等）每 2 秒施加 4 点 (2心) 电击伤害！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:prismarine 42", category="CONDUIT_MULTIBLOCK_ACTIVATION")

        # 40. Nether Portal Geometry & Chunk Loading
        if any(k in q for k in ("传送门最小", "传送门最大", "地狱门尺寸", "传送门尺寸", "传送门强加载", "传送门区块加载")):
            resp = (
                "§5【下界传送门几何极值与区块强加载动力学】\n"
                "▸ §e几何极值规格§r：内部传送门帷幕最小 2x3（总框架 4x5，四角留空只需 10 块黑曜石），最大 21x21（总框架 23x23）。\n"
                "▸ §a点火与熄灭§r：打火石、火焰弹或可燃方块引燃即可点亮；任一黑曜石破损或遭遇爆炸瞬间熄灭。\n"
                "▸ §b跨维度常载区块加载器§r：实体/物品穿过传送门时，目标维度对应区块立即获得持续 15 秒（300 ticks）的实体处理强加载！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:obsidian 14", category="NETHER_PORTAL_GEOMETRY_AND_CHUNKLOAD")

        # 41. Smelting Array Throughput & Bottleneck
        if any(k in q for k in ("熔炉阵列供料", "漏斗供料瓶颈", "熔炉漏斗跟不上", "高炉供料", "熔炼阵列瓶颈", "熔炉阵列怎么设计")):
            resp = (
                "§6【熔炼炉阵列吞吐瓶颈与供料动力学】\n"
                "▸ §e单机消耗基准§r：普通熔炉 10.0s/物 (0.1 items/s)；高炉/烟熏炉 5.0s/物 (0.2 items/s)。\n"
                "▸ §c单漏斗输送致命瓶颈§r：单漏斗固定吞吐仅为 2.5 items/s！进料主干最多仅能供给 25 台普通熔炉，或仅能供给 12 台满载高炉！\n"
                "▸ §a工业级优化拓扑§r：若超过 12 台高炉（如 16 台高炉需 3.2 items/s），必须采用【双漏斗对称并联】(5.0/s，支持 25 台) 或【漏斗矿车穿透极速分流】(20.0/s，支持 100 台)！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:hopper 16", category="SMELTING_ARRAY_THROUGHPUT_BOTTLENECK")

        # 42. Hopper Minecart Unloader Dynamics
        if any(k in q for k in ("漏斗矿车卸料", "漏斗矿车吸物", "漏斗矿车站", "漏斗矿车速度", "矿车卸料站", "漏斗矿车穿透")):
            resp = (
                "§e【漏斗矿车穿透吸物与单次往返卸料站动力学】\n"
                "▸ §e8倍极速吸物§r：漏斗矿车吸取速率为每 tick 1 个物品 (20 items/s)，为原版漏斗 (2.5/s) 的整整 8 倍！\n"
                "▸ §b隔空穿透特性§r：能够隔着正上方 1 个完整实心方块直接吸取上方容器或铁轨表面掉落物。\n"
                "▸ §a单次往返极速卸料站§r：矿车驶入停在漏斗上方，比较器检测漏斗非空触发充能铁轨断电锁车；漏斗排空瞬间比较器熄灭，非门恢复铁轨供电弹射矿车巡回！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:hopper_minecart 1", category="HOPPER_MINECART_UNLOADER_DYNAMICS")


        # 43. Hostile Mob Spawn & Despawn Spheres
        if any(k in q for k in ("刷怪塔不刷怪", "刷怪塔怎么不刷怪", "清除球", "128格", "挂机点怎么选", "刷怪半径", "mobcap", "生物上限")):
            resp = (
                "§4【敌对生物生成动力学与 128 格清除球】\n"
                "▸ §c四大清除几何球§r：0~24格绝对禁刷；24~32格黄金高频活动圈；33~128格随机清除区(每tick 1/800几率消失)；>128格瞬间蒸发！\n"
                "▸ §e单人 70 生物Cap占用§r：挂机点128格内若有未点亮天然矿洞，怪物迅速占满70上限导致刷怪塔断崖式停产！必须高空挂机或照亮洞穴。\n"
                "▸ §a基岩低Y轴优势§r：算法从最高方块高度向下抽样，深层挖空基岩(Y=-58)效率比常规地表高 3~4 倍！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi mobfarm 120 64 false", category="HOSTILE_MOB_SPAWN_AND_DESPAWN_SPHERES")

        # 44. Spawner Cage Mechanics & Suppression
        if any(k in q for k in ("刷怪笼怎么封", "刷怪笼怎么不刷", "刷怪笼激活距离", "刷怪笼光照", "刷怪笼机制", "刷怪箱")):
            resp = (
                "§6【刷怪笼生成空间与光照压制力学】\n"
                "▸ §e激活半径与扫描盒§r：玩家必须在刷怪笼 16 格以内；周围 9x9x3 空间内同类实体 < 6 只方可继续生成。\n"
                "▸ §a光照彻底压制§r：1.18+ 普通刷怪笼需方块光照 >= 11 彻底熄灭（刷怪笼各面插火把或红石灯）；烈焰人需 >= 12。\n"
                "▸ §b高效收集管道§r：底部铺设流水快速移出 9x9x3 区域，引至 23 格摔落井残血收割或三叉戟杀手自动挂机！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:torch 8", category="SPAWNER_CAGE_MECHANICS_AND_SUPPRESSION")

        # 45. Iron Farm Panic & LOS Sleep Timing
        if any(k in q for k in ("刷铁机不刷铁傀儡", "刷铁机怎么不刷", "刷铁机失效", "村民失眠", "铁傀儡生成条件", "刷铁机僵尸")):
            resp = (
                "§3【铁傀儡农场恐慌时序与破视睡眠机制】\n"
                "▸ §e刷新硬性三要素§r：至少 3 名村民；在过去 20 分钟内必须入睡过至少 1 tick；目视敌对实体进入恐慌状态。\n"
                "▸ §c致命失眠陷阱§r：若僵尸视线未遮挡，村民 24 小时恐慌无法入睡，20分钟后因失眠彻底停产！\n"
                "▸ §a破视时序优化§r：必须用活塞遮挡板或水流颠簸进行周期性视线遮断 (LOS Break)，让村民每隔数秒能偷睡 1 tick！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi villager iron", category="IRON_FARM_PANIC_AND_LOS_SLEEP")

        # 46. Villager Workstation Pathing & Restocking
        if any(k in q for k in ("村民怎么不补货", "村民转职", "村民怎么转职", "村民锁定职业", "村民不工作", "村民交易锁")):
            resp = (
                "§b【村民工作站点路径寻路与交易补货动力学】\n"
                "▸ §e物理寻路可达§r：村民必须拥有到达工作站点脚部的物理可行寻路路径，隔着全实心方块或落差断崖无法绑定。\n"
                "▸ §c职业永久锁定§r：一旦产生过任何交易（经验 XP > 0），职业与交易树永久锁定，拆除工作台也绝不转职！\n"
                "▸ §a补货时钟法则§r：村民每天在日间工作时段 (2000~9000 ticks) 前往工作站至多补货 2 次；接触不到工作台将永久无法补货！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi villager trading", category="VILLAGER_WORKSTATION_PATHING_AND_RESTOCK")

        # 47. Anvil Penalty & Binary Tree Optimizer
        if any(k in q for k in ["神装怎么合", "二叉树附魔合并", "铁砧二叉树", "铁砧合并方案", "附魔书怎么合最省"]):
            resp = (
                "§6【铁砧累积惩罚与二叉树最优合并规避算法】\n"
                "▸ §c指数爆炸惩罚§r：累积惩罚为 2^N - 1 级；单步 >= 40 级直接触发【过于昂贵！】彻底无法锻造。\n"
                "▸ §a二叉树合并对数降维§r：将 6~8 本书两两配对合并成复合书，树高压制在 3 层内，最后一次性拍上装备，最终惩罚仅 7 级！\n"
                "▸ §e一键规划指令§r：使用 `/hoshi anvil <装备> <附魔1> <附魔2>...` 即可生成零失误单步工序！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi anvil netherite_sword sharpness:5 unbreaking:3 mending:1 looting:3", category="ANVIL_PENALTY_AND_BINARY_TREE_OPTIMIZER")

        # 48. Enchantment Compatibility & Gear Rules
        if any(k in q for k in ["附魔互斥", "精准和时运", "无限和经验修补", "保护和火保", "重锤附魔"]):
            resp = (
                "§d【附魔互斥矩阵与神装配方验证】\n"
                "▸ §e严格互斥对§r：精准采集 vs 时运；无限 vs 经验修补；多重射击 vs 穿透；激流 vs 忠诚/引雷。\n"
                "▸ §b护甲四保互斥§r：保护、火焰保护、爆炸保护、弹射物保护不可共存于同一防具。\n"
                "▸ §a1.21 重锤专属神装§r：致密 (Density 增伤) + 破甲 (Breach 穿透) + 风爆 (Wind Burst 击中滞空)！"
            )
            return Resolution(text_response=resp, suggested_command="/give @s minecraft:enchanted_book 1", category="ENCHANTMENT_COMPATIBILITY_AND_GEAR_RULES")

        # 49. Create Stress Capacity & Kinetics
        if any(k in q for k in ["create应力", "机械动力过载", "create转速", "蒸汽机配置", "齿轮比", "应力过载"]):
            resp = (
                "§e【Create 机械动力学应力网络与过载断裂力学】\n"
                "▸ §c过载断裂机制§r：机器消耗 Impact(SU) = kappa * RPM。若总消耗 > 总容量，全线转速归零停摆！\n"
                "▸ §b齿轮传动法则§r：大齿轮带小齿轮 2:1 提速但消耗翻倍；小齿轮带大齿轮 1:2 降速消耗减半。\n"
                "▸ §a动力阶梯与蒸汽机§r：水轮 256 SU，大水轮 512 SU，风车满配 8,192 SU；18 级超频蒸汽机锅炉最高释放 294,912 SU！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi create stress steam 9", category="CREATE_STRESS_CAPACITY_AND_KINETICS")

        # 50. Portal Permaloader & Chunk Ticking
        if any(k in q for k in ["常载区块", "强加载器", "传送门加载器", "permaloader", "下界门串门", "传送门对齐"]):
            resp = (
                "§b【生电传送门常载网与 Ticket 30 强加载拓扑】\n"
                "▸ §e15秒时钟律§r：实体穿越传送门赋予 15.0 秒 (300 ticks) Ticket 30 强加载票；投掷时钟建议控制在 8~12 秒防断流。\n"
                "▸ §a三阶辐射圈§r：3x3 实体完全处理区、5x5 方块红石区、7x7 懒惰区。\n"
                "▸ §c8:1 坐标对齐§r：实际门偏离理想坐标超过 16 格将诱发单向串门撕裂；使用 `/hoshi chunkloader portal <主界X> <主界Z> <下界X> <下界Z>` 诊断漂移！"
            )
            return Resolution(text_response=resp, suggested_command="/hoshi chunkloader permaloader 10.0", category="PORTAL_PERMALOADER_AND_CHUNK_TICKING")

        return None

    @staticmethod
    def _resolve_coordinates(ctx: Optional[ContextSnapshot]) -> Resolution:
        if ctx is None:
            return Resolution(
                text_response=NETHER_PORTAL_RULES,
                suggested_command=None,
                category="COORDINATES_GENERAL",
            )

        if ctx.is_nether:
            ox, oy, oz = ctx.get_overworld_equivalent_coords()
            text = (
                f"§6【下界 ➔ 主界对应坐标】§r\n"
                f"▸ 当前下界坐标：[{ctx.block_x}, {ctx.block_y}, {ctx.block_z}]\n"
                f"▸ 对应主界坐标：§a[{ox}, {oy}, {oz}]§r\n"
                f"▸ 计算公式：主界 X = 下界 X × 8, 主界 Z = 下界 Z × 8"
            )
            cmd = f"/tp {ox} {oy} {oz}"
            return Resolution(text_response=text, suggested_command=cmd, category="COORDINATES_OVERWORLD")
        else:
            nx, ny, nz = ctx.get_nether_equivalent_coords()
            text = (
                f"§c【主界 ➔ 下界对应坐标】§r\n"
                f"▸ 当前主界坐标：[{ctx.block_x}, {ctx.block_y}, {ctx.block_z}]\n"
                f"▸ 对应下界坐标：§e[{nx}, {ny}, {nz}]§r\n"
                f"▸ 计算公式：下界 X = floor(主界 X / 8), 下界 Z = floor(主界 Z / 8)"
            )
            cmd = f"/tp {nx} {ny} {nz}"
            return Resolution(text_response=text, suggested_command=cmd, category="COORDINATES_NETHER")
