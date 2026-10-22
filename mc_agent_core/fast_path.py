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
    def try_resolve(raw_query: str, context: Optional[ContextSnapshot]) -> Optional[Resolution]:
        if not raw_query or not raw_query.strip():
            return None
        q = raw_query.strip().lower()

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
        if "不刷怪" in q or ("刷怪" in q and any(k in q for k in ("亮度", "条件", "为什么", "怎么", "不生成"))):
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
        if "村民" in q and any(k in q for k in ("转职", "锁", "刷", "工作台", "职业", "交易", "图书", "经验修补")):
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
        if any(k in q for k in ("比较器", "分类机", "物品分类", "漏斗分类", "22个", "比较器信号", "测箱子")):
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

        # 16. Iron Golem Spawning & Iron Farm
        if any(k in q for k in ("铁傀儡", "刷铁机", "为什么不刷铁", "村民惊吓", "不生成铁傀儡")):
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
        if any(k in q for k in ("潮涌核心", "潮涌能量", "导管怎么激活", "潮涌核心怎么摆", "海洋之心", "鹦鹉螺壳", "海晶石框架")):
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
