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
