from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OreDistribution:
    name: str
    min_y: int
    max_y: int
    optimal_y: int
    notes: str


ORE_TABLE: dict[str, OreDistribution] = {
    "diamond": OreDistribution(
        name="钻石 (Diamond)",
        min_y=-64,
        max_y=16,
        optimal_y=-58,
        notes="1.18+ 深度越深越丰富，推荐在 Y=-58 或 Y=-59 支路挖掘，避开基岩层（-60 以下）。暴露在空气中的概率降低（深板岩洞穴暴率降低，水下或实心岩挖掘效率最高）。"
    ),
    "iron": OreDistribution(
        name="铁矿 (Iron)",
        min_y=-64,
        max_y=320,
        optimal_y=16,
        notes="1.18+ 呈双峰分布：主峰在 Y=16，次峰在高山 Y=232。推荐在风蚀丘陵/高山露天挖掘或地下 Y=16 附近。"
    ),
    "coal": OreDistribution(
        name="煤炭 (Coal)",
        min_y=0,
        max_y=256,
        optimal_y=96,
        notes="1.18+ 不在 Y=0 以下生成！最佳高度为 Y=96（山地地表大量露天生成）。"
    ),
    "copper": OreDistribution(
        name="铜矿 (Copper)",
        min_y=-16,
        max_y=112,
        optimal_y=48,
        notes="最佳高度 Y=48。在滴水石洞穴（Dripstone Caves）生成量显著提升。"
    ),
    "ancient_debris": OreDistribution(
        name="远古残骸 (Ancient Debris)",
        min_y=8,
        max_y=119,
        optimal_y=15,
        notes="下界矿石，不会暴露在空气中。主生成带在 Y=8~22，峰值高度在 Y=15（推荐用床爆或TNT横向挖掘）。"
    ),
    "gold": OreDistribution(
        name="金矿 (Gold)",
        min_y=-64,
        max_y=32,
        optimal_y=-16,
        notes="普通生物群系中在 Y=-16 附近最多；但在恶地/荒野群系（Badlands），可在 Y=-64 到 Y=256 大量生成！"
    ),
    "redstone": OreDistribution(
        name="红石 (Redstone)",
        min_y=-64,
        max_y=16,
        optimal_y=-58,
        notes="与钻石类似，越接近基岩越丰富，Y=-58 浓度最高。"
    ),
    "lapis": OreDistribution(
        name="青金石 (Lapis Lazuli)",
        min_y=-64,
        max_y=64,
        optimal_y=0,
        notes="三角分布，正中心峰值在海平面下方 Y=0 处。"
    ),
}

MOB_SPAWNING_RULE = (
    "【刷怪机制 (1.18+)】\n"
    "1. 敌对生物自然生成要求【方块内部方块光照 (Block Light) 必须完全为 0】！天空光照 (Sky Light) 在夜晚允许 <= 7。\n"
    "2. 只要放置火把、红石灯、荧石等光源使方块光照 >= 1，即可彻底杜绝普通怪物生成。\n"
    "3. 史莱姆在史莱姆区块（Y<40）不受此光照限制；烈焰人与潜影贝刷怪笼有单独机制。"
)

NETHERITE_UPGRADE_RULE = (
    "【下界合金升级机制 (1.20+)】\n"
    "1. 1.20 之后升级下界合金装备必须在锻造台放置 3 样物品：\n"
    "   - 锻造模板：【下界合金升级锻造模板 (Netherite Upgrade Smithing Template)】\n"
    "   - 基础装备：钻石工具/护甲\n"
    "   - 升级材料：下界合金锭 (Netherite Ingot)\n"
    "2. 模板获取：仅在堡垒遗迹 (Bastion Remnant) 的宝箱中生成（藏宝室宝箱 100% 出现 1 个）。\n"
    "3. 模板复制：在工作台用 7 个钻石 + 1 个下界岩 + 1 个下界合金升级模板，可复制出 2 个模板。"
)

VERSION_1_21_MECHANICS = (
    "【试炼密室与 1.21 核心机制】\n"
    "1. 重锤 (Mace)：\n"
    "   - 合成：1 个重型核心 (Heavy Core，试炼密室不祥宝库开启获得) + 1 个旋风棒 (Breeze Rod，旋风人掉落)。\n"
    "   - 坠落粉碎击：下落时攻击敌人将下落动能转化为伤害（每格坠落增加基础伤害），且成功命中后完全免疫坠落伤害！\n"
    "2. 自动合成器 (Crafter)：\n"
    "   - 接收红石脉冲信号时自动读取 3x3 九宫格内的材料并吐出合成成品。\n"
    "   - 可以右键点击禁用特定格子，用于固定非全满合成表（例如剑、镐、靴子）。\n"
    "3. 旋风弹 (Wind Charge)：\n"
    "   - 旋风棒分解或旋风人掉落，右键发射可击退生物、推动拉杆/按钮、实现高跳火箭跳。"
)

NETHER_PORTAL_RULES = (
    "【下界传送门换算与链接机制】\n"
    "1. 水平坐标换算比例为 8:1：主界坐标除以 8 对应下界坐标；下界坐标乘以 8 对应主界坐标。\n"
    "2. 公式：X_nether = floor(X_overworld / 8), Z_nether = floor(Z_overworld / 8)。高度 Y 不受 8 倍缩放影响。\n"
    "3. 搜索半径：主界进入下界搜索半径为下界 16 格；下界进入主界搜索半径为主界 128 格。多门串门时需手动在精确对应坐标立门！"
)

ENCHANTMENT_CONFLICT_RULES = (
    "【附魔互斥与冲突权威规则】\n"
    "1. 弓箭类：【经验修补 (Mending)】与【无限 (Infinity)】绝对互斥！不可在同一把弓上共存。\n"
    "2. 近战伤害类：【锋利 (Sharpness)】、【亡灵杀手 (Smite)】、【节肢杀手 (Bane of Arthropods)】互斥（只能选其一）。重锤上【致密 (Density)】与【破甲 (Breach)】亦互斥。\n"
    "3. 护甲减伤类：【保护 (Protection)】、【火焰保护 (Fire Protection)】、【爆炸保护 (Blast Protection)】、【弹射物保护 (Projectile Protection)】互斥。\n"
    "4. 工具采集类：【精准采集 (Silk Touch)】与【时运 (Fortune)】互斥。\n"
    "5. 弩箭类：【多重射击 (Multishot)】与【穿透 (Piercing)】互斥。\n"
    "6. 靴子特殊：【冰霜行者 (Frost Walker)】与【深海漫游者 (Depth Strider)】互斥。"
)

VILLAGER_RULES = (
    "【村民职业、交易与锁交易机制】\n"
    "1. 永久锁定机制：只要与村民完成【任意一次交易】，该村民的职业与所有交易项将永久锁定！即使敲掉工作台也不会转职或洗掉。\n"
    "2. 刷新附魔书（核心技巧）：未交易前，放置【讲台 (Lectern)】让无业村民成为图书管理员；若第一层未刷出心仪的附魔书（如经验修补、锋利V），直接空手破坏讲台并重新放置，村民会瞬间重置并刷新全新交易表！\n"
    "3. 常见工作台对应：\n"
    "   - 讲台 (Lectern) ➔ 图书管理员（附魔书）\n"
    "   - 高炉 (Blast Furnace) ➔ 盔甲匠（钻石防具）\n"
    "   - 砂轮 (Grindstone) ➔ 武器匠（钻石武器）\n"
    "   - 锻造台 (Smithing Table) ➔ 工具匠（钻石工具）\n"
    "   - 制箭台 (Fletching Table) ➔ 制箭师（木棍换绿宝石）\n"
    "   - 堆肥桶 (Composter) ➔ 农夫（作物换绿宝石）\n"
    "4. 补货时间：村民每天在工作时间段（Tick 2000~9000）前往工作台补货至多 2 次。"
)

BEACON_RULES = (
    "【信标金字塔搭建与效果计算】\n"
    "1. 基座金字塔层级与消耗（矿物块可用铁/金/绿宝石/钻石/下界合金混搭）：\n"
    "   - 1 层 (3×3 = 9 块)：范围 20 格，可选 速度 I 或 急迫 I\n"
    "   - 2 层 (5×5 + 9 = 34 块)：范围 30 格，增加可选 抗性提升 I 或 跳跃提升 I\n"
    "   - 3 层 (7×7 + 34 = 83 块)：范围 40 格，增加可选 力量 I\n"
    "   - 4 层满级 (9×9 + 83 = 164 块，共 2 组多 36 块)：范围 50 格，可解锁【急迫 II】（配合效率V镐实现秒挖深板岩与石头）或额外【生命恢复 I】！\n"
    "2. 露天要求：信标正上方至天空建筑上限高度内不能有任何不透明完整方块阻挡（玻璃等透明方块允许）。"
)

OMINOUS_AND_TRIAL_RULES = (
    "【1.21 不祥之兆与试炼密室不祥事件】\n"
    "1. 不祥之瓶 (Ominous Bottle)：击败带旗帜的袭击队长后掉落瓶子（I~V 级），不再自动给玩家上 buff。玩家可自由选择何时饮用获得不祥之兆。\n"
    "2. 试炼预兆 (Trial Omen)：带着不祥之兆接近试炼密室，效果自动转化为试炼预兆，密室内的普通刷怪笼升级为【不祥刷怪笼】（生成穿戴附魔装备的强力怪并从头顶掉落喷溅药水与弹射物）。\n"
    "3. 不祥宝库 (Ominous Vault)：击败不祥刷怪笼掉落【不祥试炼钥匙】，用于开启不祥宝库，是获取【重型核心 (Heavy Core)】合成重锤的唯一途径！"
)

WARDEN_SCULK_RULES = (
    "【循声守卫 (Warden) 与幽匿潜声体机制】\n"
    "1. 召唤条件：自然生成的幽匿潜声体 (Sculk Shrieker) 累计触发 4 次（潜声警告等级达到 4），循声守卫会从地下钻出。人工放置的潜声体不会召唤循声守卫。\n"
    "2. 属性威慑：500 点生命值（250 颗心）；近战攻击力高达 30 点（15 颗心）；远程声波尖啸穿透护甲与方块掩体造成 10 点魔法伤害。\n"
    "3. 潜行与隔音：潜行移动（Shift）、羊毛 (Wool) 和地毯能 100% 阻隔声音振动波向潜声感测体传播。若无新激活，警告等级每 10 分钟衰减 1 级。建议投掷雪球/箭矢声东击西，避免正面冲突。"
)

COPPER_AND_WAXING_RULES = (
    "【铜块氧化、打蜡与除锈指南】\n"
    "1. 4 阶段氧化状态：未锈蚀 (亮橙) ➔ 斑驳 (暗橙带绿) ➔ 锈蚀 (绿带橙) ➔ 氧化 (完全青绿)。\n"
    "2. 打蜡锁定：手持【蜜脾 (Honeycomb)】右键点击铜块，即可锁定当前氧化外观（涂蜡铜块），永久不再继续生锈。\n"
    "3. 刮蜡与除锈：手持【任意斧头 (Axe)】右键点击可剥除蜡层，再次右键可将氧化状态削减一个等级（恢复亮橙色）。雷雨天在附近立引雷针，雷击放电可一次性震落大范围铜块的铜锈！"
)

COMPARATOR_CONTAINER_RULES = (
    "【红石比较器容器信号与分类机数学】\n"
    "1. 容器信号计算公式：Signal = floor(1 + (sum(count / max_stack) / slots) * 14)（空容器输出 0）。\n"
    "2. 经典 22 物品分类漏斗 (18-1-1-1-1)：第 1 格放 18 个待分类物品，第 2~5 格各放 1 个重命名杂物。刚好 22 物品时信号强度为 1；进第 23 物品时升至 2 触发解锁！\n"
    "3. 41 物品防串线分类 (41-1-1-1-1)：避免极端堆积冲至 3 格信号串线。\n"
    "4. 1.21 自动合成器 (Crafter)：比较器输出强度精准等于被禁用或有物品的槽位数 (0~9)。"
)

ANVIL_PENALTY_RULES = (
    "【铁砧累积惩罚与二叉树最优附魔】\n"
    "1. 累积惩罚公式 (Prior Work)：物品每在铁砧操作一次，惩罚等级加倍：2^n - 1（0 ➔ 1 ➔ 3 ➔ 7 ➔ 15 ➔ 31 ➔ 63 级额外消耗）。\n"
    "2. “过于昂贵 (Too Expensive!)”：生存模式下单次操作所需经验 >= 40 级，游戏强制拒绝操作！\n"
    "3. 二叉树最优合并法则 (Binary Tree Merge)：严禁单线串联！将多本附魔书两两对半分组合并（A+B, C+D -> AB+CD），最后一次性打在装备上，经验暴降 60%+ 且永不超标。"
)

BREWING_POTION_RULES = (
    "【酿造台全配方与药水学推演】\n"
    "1. 基础药水：水瓶 + 下界疣 (Nether Wart) = 粗制的药水 (Awkward Potion)。\n"
    "2. 主力材料：糖➔迅捷 | 烈焰粉➔力量 | 兔子脚➔跳跃 | 闪烁西瓜➔治疗 | 蜘蛛眼➔剧毒 | 金胡萝卜➔夜视 | 岩浆膏➔抗火 | 河豚➔水下呼吸 | 幻翼膜➔缓降 | 海龟壳➔神龟药水 | 旋风棒➔蓄风药水。\n"
    "3. 发酵蛛眼反转：夜视➔隐身；迅捷/跳跃➔缓慢；治疗/剧毒➔伤害 (Harming)。\n"
    "4. 调节剂：红石粉延长时长；荧石粉升为 II 级；火药制成喷溅；龙息制成滞留。"
)

IRON_GOLEM_SPAWN_RULES = (
    "【铁傀儡生成机制与刷铁机力学】\n"
    "1. 三大核心条件：① 至少 3 名有效村民绑定床铺；② 过去 20 分钟内（24000 Tick）必须睡过觉；③ 惊吓恐慌态（8 格水平/16 格视线内目击敌对生物）。\n"
    "2. 生成空间：以村民为中心 16×13×16 空间内必须有完整方块表面，且上方有 3 格空气或水流空间。\n"
    "3. 常见不刷怪原因：村民因视线受阻无法入睡、附近 16 格有残留铁傀儡、生成点上方空间不足 3 格。"
)

PORTAL_LINKING_RULES = (
    "【下界传送门精准对齐与防串门机制】\n"
    "1. 串门根源：下界与主界 8:1 坐标比例，进门搜索半径达 128 格（主界 1024 格），多门容易重定向至同一错误出口。\n"
    "2. 黄金对齐法：记下主界坐标 [X, Y, Z]，进入下界后摧毁自动生成的门，在 [floor(X/8), Y, floor(Z/8)] 处手动搭建新门并点燃，实现精准 1:1 双向对应。"
)


class LocalGameRules:
    @staticmethod
    def find_ore(query: str) -> Optional[OreDistribution]:
        lower = query.lower()
        if any(k in lower for k in ("远古残骸", "下界合金", "残骸", "debris")):
            return ORE_TABLE["ancient_debris"]
        if any(k in lower for k in ("钻石", "diamond")):
            return ORE_TABLE["diamond"]
        if any(k in lower for k in ("青金石", "lapis")):
            return ORE_TABLE["lapis"]
        if any(k in lower for k in ("红石", "redstone")):
            return ORE_TABLE["redstone"]
        if any(k in lower for k in ("铁", "iron")):
            return ORE_TABLE["iron"]
        if any(k in lower for k in ("煤", "coal")):
            return ORE_TABLE["coal"]
        if any(k in lower for k in ("铜", "copper")):
            return ORE_TABLE["copper"]
        if ("金" in lower and "合金" not in lower) or "gold" in lower:
            return ORE_TABLE["gold"]
        if "合金" in lower:
            return ORE_TABLE["ancient_debris"]
        return None
