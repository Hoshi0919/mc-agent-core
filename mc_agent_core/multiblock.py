"""
Multiblock Blueprint Validator & Assembly Guide (Python simulation).
Supports Conduit, Beacon, Nether Portal, End Portal, Wither and Iron Golem structures.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Collection

@dataclass(frozen=True)
class MultiblockBlueprint:
    id: str
    name: str
    width_x: int
    height_y: int
    depth_z: int
    required_blocks: Dict[str, int]
    layer_schematics: List[List[str]] = field(default_factory=list)
    core_activation_condition: str = ""
    perks_and_range: str = ""

    @property
    def total_block_count(self) -> int:
        return sum(self.required_blocks.values())

@dataclass(frozen=True)
class MaterialGap:
    item_id: str
    required_count: int
    available_count: int
    missing_count: int

    @property
    def is_satisfied(self) -> bool:
        return self.missing_count <= 0

@dataclass(frozen=True)
class MultiblockReport:
    blueprint: MultiblockBlueprint
    is_fully_ready: bool
    completion_rate: float
    gaps: List[MaterialGap]
    summary_text: str

    def format_report(self) -> str:
        bp = self.blueprint
        lines = [
            f"§6【多方块装配蓝图：{bp.name}】§r",
            f"▸ §7几何规格§r：{bp.width_x}×{bp.height_y}×{bp.depth_z} | 方块总量: §e{bp.total_block_count} 块§r | 背包满足度: §{'a' if self.is_fully_ready else 'c'}{self.completion_rate * 100:.1f}%§r",
            "▸ §b原料核验§r:"
        ]
        for g in self.gaps:
            if g.is_satisfied:
                lines.append(f"  §a✔ {g.item_id}: {g.available_count}/{g.required_count}§r")
            else:
                lines.append(f"  §c✘ {g.item_id}: {g.available_count}/{g.required_count} (还缺 {g.missing_count} 个)§r")

        lines.append(f"▸ §e激活条件§r：{bp.core_activation_condition}")
        lines.append(f"▸ §a增益效果§r：{bp.perks_and_range}")

        if self.is_fully_ready:
            lines.append("§a[Hoshi 校验] 恭喜！当前背包材料已 100% 齐备，可直接开工搭建！§r")
        else:
            lines.append("§e[Hoshi 提示] 材料尚未完全备齐，请收集齐上述红叉原料后再行封顶激活。§r")
        return "\n".join(lines)

_BLUEPRINTS: Dict[str, MultiblockBlueprint] = {
    "conduit": MultiblockBlueprint(
        id="conduit",
        name="潮涌核心满级三环 (Conduit 3-Ring Frame)",
        width_x=5, height_y=5, depth_z=5,
        required_blocks={"minecraft:prismarine": 42, "minecraft:conduit": 1},
        layer_schematics=[
            ["  #  ", " ### ", "#####", " ### ", "  #  "],
            [" # # ", "#   #", "#   #", "#   #", " # # "],
            ["##C##", "#   #", "# C #", "#   #", "##C##"],
            [" # # ", "#   #", "#   #", "#   #", " # # "],
            ["  #  ", " ### ", "#####", " ### ", "  #  "]
        ],
        core_activation_condition="中心潮涌核心必须被 3x3x3 范围内的水体（水源/流水/含水方块）完全包裹；外部海晶石框架不可接触空气",
        perks_and_range="满级 42 块海晶石激活：潮涌能量范围达到最大 96 格半径（水下呼吸、夜视、极速挖掘），且对 8 格内敌对生物每 2 秒施加 4 点电击伤害"
    ),
    "beacon_tier4": MultiblockBlueprint(
        id="beacon_tier4",
        name="四级信标金字塔 (Tier 4 Beacon Pyramid)",
        width_x=9, height_y=5, depth_z=9,
        required_blocks={"minecraft:iron_block": 164, "minecraft:beacon": 1},
        core_activation_condition="信标正上方必须直视天空（高度 320），严禁有任何不透明实体方块阻挡（玻璃、水、栅栏等透明方块允许）",
        perks_and_range="四层完整金字塔 (164 矿物块)：激活急迫 II (Haste II) 与生命恢复 (Regeneration)，影响半径 50 格，持下界合金镐可实现秒挖深板岩"
    ),
    "beacon_tier1": MultiblockBlueprint(
        id="beacon_tier1",
        name="一级信标基座 (Tier 1 Beacon)",
        width_x=3, height_y=2, depth_z=3,
        required_blocks={"minecraft:iron_block": 9, "minecraft:beacon": 1},
        core_activation_condition="信标正上方直视天空无遮挡",
        perks_and_range="一层基座 (9 矿物块)：基础速度 I 或急迫 I，影响半径 20 格"
    ),
    "nether_portal": MultiblockBlueprint(
        id="nether_portal",
        name="下界传送门标准框架 (Nether Portal 4x5)",
        width_x=4, height_y=5, depth_z=1,
        required_blocks={"minecraft:obsidian": 14, "minecraft:flint_and_steel": 1},
        core_activation_condition="黑曜石框架内空至少 2x3，最大 21x21；内部使用打火石、火弹或引燃火焰即可激活紫光帷幕",
        perks_and_range="跨维度穿梭：主界与下界水平坐标 8:1 欧氏映射；投掷物/实体穿过可触发目标区块瞬时 15 秒强加载"
    ),
    "end_portal": MultiblockBlueprint(
        id="end_portal",
        name="末地传送门悬空环 (End Portal Ring)",
        width_x=5, height_y=1, depth_z=5,
        required_blocks={"minecraft:end_portal_frame": 12, "minecraft:ender_eye": 12},
        core_activation_condition="所有 12 个末地传送门框架的正面朝向 (facing) 必须向内朝向中心；每个框架嵌入末影之眼后激活 3x3 星空传送门",
        perks_and_range="单向传送至末地中心岛黑曜石平台 (100, 49, 0)；通往末影龙主战场"
    ),
    "wither": MultiblockBlueprint(
        id="wither",
        name="凋灵召唤构架 (Wither Boss Assembly)",
        width_x=3, height_y=3, depth_z=1,
        required_blocks={"minecraft:soul_sand": 4, "minecraft:wither_skeleton_skull": 3},
        core_activation_condition="必须保证头颅最后安放，且周围无草丛或积雪阻挡空气；生成后拥有数秒充能无敌期并释放巨大爆炸",
        perks_and_range="击败掉落下界之星 (Nether Star)，用于合成信标"
    ),
    "iron_golem": MultiblockBlueprint(
        id="iron_golem",
        name="铁傀儡装配构架 (Iron Golem Assembly)",
        width_x=3, height_y=3, depth_z=1,
        required_blocks={"minecraft:iron_block": 4, "minecraft:carved_pumpkin": 1},
        core_activation_condition="南瓜必须最后放置，且傀儡生成空间 2x3x2 内不得有其他实体阻挡",
        perks_and_range="生成 100 HP 强力守卫；手持铁锭可右键回血修复"
    )
}

def find_blueprint(query: str) -> Optional[MultiblockBlueprint]:
    if not query:
        return None
    clean = query.strip().lower().replace(" ", "_").replace("minecraft:", "")
    if clean in _BLUEPRINTS:
        return _BLUEPRINTS[clean]
    if "conduit" in clean or "潮涌" in clean or "海晶" in clean:
        return _BLUEPRINTS["conduit"]
    if clean == "beacon" or "信标" in clean or "金字塔" in clean:
        return _BLUEPRINTS["beacon_tier4"]
    if "beacon_t1" in clean or "一级信标" in clean:
        return _BLUEPRINTS["beacon_tier1"]
    if "portal" in clean or "地狱门" in clean or "传送门" in clean or "下界门" in clean:
        return _BLUEPRINTS["nether_portal"]
    if "end_portal" in clean or "末地门" in clean or "末地传送门" in clean:
        return _BLUEPRINTS["end_portal"]
    if "wither" in clean or "凋灵" in clean or "凋零" in clean:
        return _BLUEPRINTS["wither"]
    if "golem" in clean or "铁傀儡" in clean:
        return _BLUEPRINTS["iron_golem"]
    for bp in _BLUEPRINTS.values():
        if clean in bp.id or clean in bp.name.lower():
            return bp
    return None

def validate_inventory(bp: MultiblockBlueprint, inventory=None) -> MultiblockReport:
    gaps = []
    satisfied_types = 0
    total_required = 0
    total_available = 0

    for item_id, req in bp.required_blocks.items():
        total_required += req
        available = 0
        if inventory:
            available = inventory.count_item(item_id)
            if item_id == "minecraft:prismarine":
                available += inventory.count_item("minecraft:prismarine_bricks")
                available += inventory.count_item("minecraft:dark_prismarine")
                available += inventory.count_item("minecraft:sea_lantern")
            elif item_id == "minecraft:iron_block":
                available += inventory.count_item("minecraft:gold_block")
                available += inventory.count_item("minecraft:emerald_block")
                available += inventory.count_item("minecraft:diamond_block")
                available += inventory.count_item("minecraft:netherite_block")
            elif item_id == "minecraft:soul_sand":
                available += inventory.count_item("minecraft:soul_soil")
            elif item_id == "minecraft:carved_pumpkin":
                available += inventory.count_item("minecraft:jack_o_lantern")

        missing = max(0, req - available)
        gaps.append(MaterialGap(item_id, req, available, missing))
        total_available += min(available, req)
        if missing == 0:
            satisfied_types += 1

    fully_ready = (satisfied_types == len(bp.required_blocks))
    rate = (total_available / total_required) if total_required > 0 else 1.0
    return MultiblockReport(
        blueprint=bp,
        is_fully_ready=fully_ready,
        completion_rate=rate,
        gaps=gaps,
        summary_text="MATERIALS_READY" if fully_ready else "MATERIALS_MISSING"
    )
