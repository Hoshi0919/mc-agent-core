import math
from dataclasses import dataclass
from typing import List, Optional
from .formatter import ChatComponent
from .tellraw import TellrawJsonBuilder


@dataclass(frozen=True)
class ItemStack:
    item_id: str
    display_name: str
    count: int

    def __post_init__(self):
        if self.count < 0:
            raise ValueError(f"Item count cannot be negative: {self.count}")

    @property
    def stacks(self) -> int:
        return self.count // 64

    @property
    def remainder(self) -> int:
        return self.count % 64

    def format_stacks(self) -> str:
        s = self.stacks
        r = self.remainder
        if s > 0 and r > 0:
            return f"{self.count} ({s} 组 + {r} 个)"
        elif s > 0:
            return f"{self.count} ({s} 组整)"
        else:
            return f"{self.count} 个"

    def __str__(self) -> str:
        return f"{self.display_name} x{self.format_stacks()}"


@dataclass(frozen=True)
class BlueprintBOM:
    blueprint_id: str
    title: str
    scale: int
    components: List[ItemStack]
    raw_materials: List[ItemStack]

    def to_formatted_text(self) -> str:
        lines = [
            f"§6【{self.title} - 材料清单 (规模: {self.scale})】§r",
            "§e▸ 核心构件清单：§r",
        ]
        for item in self.components:
            lines.append(f"  • §b{item.display_name}§r: §a{item.format_stacks()}§r")
        if self.raw_materials:
            lines.append("§e▸ 基础原料折算（合成所需）：§r")
            for raw in self.raw_materials:
                lines.append(f"  • §7{raw.display_name}§r: §e{raw.format_stacks()}§r")
        return "\n".join(lines).strip()

    def to_tellraw_json(self) -> str:
        comps = []
        comps.append(ChatComponent(
            text=f"【{self.title} 材料清单 (x{self.scale})】\n",
            color="gold", bold=True, italic=False, click_action=None, click_value=None, hover_text=None
        ))
        comps.append(ChatComponent(
            text="▸ 核心构件清单（点击填入获取指令）：\n",
            color="yellow", bold=False, italic=False, click_action=None, click_value=None, hover_text=None
        ))
        for item in self.components:
            cmd = f"/give @s {item.item_id} {item.count}"
            comps.append(ChatComponent(
                text="  • ", color="gray", bold=False, italic=False, click_action=None, click_value=None, hover_text=None
            ))
            comps.append(ChatComponent(
                text=f"{item.display_name} x{item.format_stacks()}\n",
                color="aqua", bold=False, italic=False,
                click_action="SUGGEST_COMMAND", click_value=cmd,
                hover_text=f"点击填入: {cmd}"
            ))
        if self.raw_materials:
            comps.append(ChatComponent(
                text="▸ 基础原料折算（合成所需）：\n",
                color="gray", bold=False, italic=False, click_action=None, click_value=None, hover_text=None
            ))
            for raw in self.raw_materials:
                comps.append(ChatComponent(
                    text=f"  • {raw.display_name}: {raw.format_stacks()}\n",
                    color="gray", bold=False, italic=True, click_action=None, click_value=None, hover_text=None
                ))
        return TellrawJsonBuilder.to_json(comps)


class MaterialCalculator:
    ID_SUGAR_CANE_FARM = "SUGAR_CANE_FARM"
    ID_PUMPKIN_MELON_FARM = "PUMPKIN_MELON_FARM"
    ID_BEACON_STRUCTURE = "BEACON_STRUCTURE"
    ID_STONE_GENERATOR = "STONE_GENERATOR"
    ID_ITEM_SORTER = "ITEM_SORTER_MODULE"
    ID_ETHO_CLOCK = "ETHO_HOPPER_CLOCK"

    @classmethod
    def get_sugar_cane_farm_bom(cls, modules: int = 8) -> BlueprintBOM:
        n = max(1, modules)
        comps = [
            ItemStack("minecraft:piston", "普通活塞", n),
            ItemStack("minecraft:observer", "侦测器 (Observer)", n),
            ItemStack("minecraft:redstone", "红石粉", n),
            ItemStack("minecraft:sugar_cane", "甘蔗", n),
            ItemStack("minecraft:dirt", "泥土/沙子", n),
            ItemStack("minecraft:stone_bricks", "实心建筑方块", n * 2),
            ItemStack("minecraft:water_bucket", "水桶", max(1, (n + 7) // 8)),
            ItemStack("minecraft:hopper", "漏斗", 1),
            ItemStack("minecraft:chest", "箱子", 2),
        ]
        raw = [
            ItemStack("minecraft:iron_ingot", "铁锭 (活塞+漏斗)", n + 5),
            ItemStack("minecraft:redstone", "红石粉总消耗", n * 3),
            ItemStack("minecraft:nether_quartz", "下界石英 (侦测器)", n),
            ItemStack("minecraft:cobblestone", "圆石 (活塞+侦测器)", n * 10),
            ItemStack("minecraft:oak_planks", "木板 (活塞+箱子+漏斗)", n * 3 + 16),
        ]
        return BlueprintBOM(cls.ID_SUGAR_CANE_FARM, "全自动甘蔗/竹子机", n, comps, raw)

    @classmethod
    def get_pumpkin_melon_farm_bom(cls, modules: int = 4) -> BlueprintBOM:
        n = max(1, modules)
        comps = [
            ItemStack("minecraft:piston", "普通活塞", n),
            ItemStack("minecraft:observer", "侦测器 (Observer)", n),
            ItemStack("minecraft:redstone", "红石粉", n),
            ItemStack("minecraft:pumpkin_seeds", "南瓜/西瓜种子", n),
            ItemStack("minecraft:stone_bricks", "实心建筑方块", n * 3),
            ItemStack("minecraft:hopper_minecart", "漏斗矿车", 1),
            ItemStack("minecraft:rail", "普通铁轨", max(2, n)),
            ItemStack("minecraft:powered_rail", "充能铁轨", 2),
            ItemStack("minecraft:hopper", "漏斗", 1),
            ItemStack("minecraft:chest", "箱子", 2),
        ]
        raw = [
            ItemStack("minecraft:iron_ingot", "铁锭", n + 16),
            ItemStack("minecraft:redstone", "红石粉总消耗", n * 3 + 2),
            ItemStack("minecraft:nether_quartz", "下界石英", n),
            ItemStack("minecraft:cobblestone", "圆石", n * 10),
        ]
        return BlueprintBOM(cls.ID_PUMPKIN_MELON_FARM, "全自动南瓜/西瓜机", n, comps, raw)

    @classmethod
    def get_beacon_bom(cls, tier: int = 4) -> BlueprintBOM:
        t = max(1, min(4, tier))
        blocks_map = {1: 9, 2: 34, 3: 83, 4: 164}
        blocks = blocks_map[t]
        comps = [
            ItemStack("minecraft:beacon", "信标", 1),
            ItemStack("minecraft:iron_block", "矿物方块 (铁/金/绿宝石/钻石块)", blocks),
        ]
        raw = [
            ItemStack("minecraft:iron_ingot", "对应矿物原锭 (9 倍)", blocks * 9),
            ItemStack("minecraft:nether_star", "下界之星 (信标合成)", 1),
            ItemStack("minecraft:obsidian", "黑曜石 (信标合成)", 3),
            ItemStack("minecraft:glass", "玻璃 (信标合成)", 5),
        ]
        return BlueprintBOM(cls.ID_BEACON_STRUCTURE, f"{t} 级信标金字塔底座", t, comps, raw)

    @classmethod
    def get_stone_generator_bom(cls) -> BlueprintBOM:
        comps = [
            ItemStack("minecraft:water_bucket", "水桶", 1),
            ItemStack("minecraft:lava_bucket", "岩浆桶", 1),
            ItemStack("minecraft:piston", "普通活塞", 1),
            ItemStack("minecraft:observer", "侦测器", 1),
            ItemStack("minecraft:redstone", "红石粉", 2),
            ItemStack("minecraft:stone_bricks", "耐火建筑方块", 16),
            ItemStack("minecraft:hopper", "漏斗", 1),
            ItemStack("minecraft:chest", "箱子", 2),
        ]
        return BlueprintBOM(cls.ID_STONE_GENERATOR, "安全高效刷石机", 1, comps, [])

    @classmethod
    def get_item_sorter_bom(cls, modules: int = 1) -> BlueprintBOM:
        n = max(1, modules)
        comps = [
            ItemStack("minecraft:hopper", "漏斗", n * 3),
            ItemStack("minecraft:comparator", "红石比较器", n),
            ItemStack("minecraft:repeater", "红石中继器", n),
            ItemStack("minecraft:redstone_torch", "红石火把", n),
            ItemStack("minecraft:redstone", "红石粉", n * 3),
            ItemStack("minecraft:chest", "箱子", n * 2),
            ItemStack("minecraft:stone_bricks", "实心方块", n * 8),
        ]
        raw = [
            ItemStack("minecraft:iron_ingot", "铁锭 (漏斗)", n * 15),
            ItemStack("minecraft:redstone", "红石粉总消耗", n * 6),
            ItemStack("minecraft:nether_quartz", "下界石英", n),
            ItemStack("minecraft:oak_planks", "木板", n * 30),
        ]
        return BlueprintBOM(cls.ID_ITEM_SORTER, "22物品标准漏斗分类机", n, comps, raw)

    @classmethod
    def get_etho_clock_bom(cls) -> BlueprintBOM:
        comps = [
            ItemStack("minecraft:hopper", "漏斗", 2),
            ItemStack("minecraft:comparator", "红石比较器", 2),
            ItemStack("minecraft:sticky_piston", "粘性活塞", 2),
            ItemStack("minecraft:redstone_block", "红石块", 1),
            ItemStack("minecraft:redstone", "红石粉", 2),
            ItemStack("minecraft:stone_bricks", "实心方块", 2),
            ItemStack("minecraft:cobblestone", "计时填充物品 (如圆石)", 64),
        ]
        return BlueprintBOM(cls.ID_ETHO_CLOCK, "Etho 双漏斗长周期时钟", 1, comps, [])

    @classmethod
    def get_bom(cls, blueprint_id: Optional[str], scale: int = 1) -> BlueprintBOM:
        if not blueprint_id:
            return cls.get_sugar_cane_farm_bom(8)
        bid = blueprint_id.upper()
        if "SUGAR_CANE" in bid or "甘蔗" in bid or "竹子" in bid:
            return cls.get_sugar_cane_farm_bom(8 if scale <= 0 else scale)
        if "PUMPKIN" in bid or "MELON" in bid or "南瓜" in bid or "西瓜" in bid:
            return cls.get_pumpkin_melon_farm_bom(4 if scale <= 0 else scale)
        if "BEACON" in bid or "信标" in bid:
            return cls.get_beacon_bom(4 if scale <= 0 else scale)
        if "STONE" in bid or "刷石" in bid or "造石" in bid:
            return cls.get_stone_generator_bom()
        if "SORT" in bid or "分类" in bid:
            return cls.get_item_sorter_bom(1 if scale <= 0 else scale)
        if "CLOCK" in bid or "时钟" in bid or "ETHO" in bid:
            return cls.get_etho_clock_bom()
        return cls.get_sugar_cane_farm_bom(8 if scale <= 0 else scale)

    @classmethod
    def match_bom(cls, query: Optional[str]) -> Optional[BlueprintBOM]:
        if not query:
            return None
        q = query.lower()
        is_mat = any(k in q for k in ("材料", "原料", "清单", "要多少", "需要什么", "需要多少", "bom"))
        if not is_mat:
            return None

        if "甘蔗" in q or "竹子" in q:
            return cls.get_sugar_cane_farm_bom(8)
        if "南瓜" in q or "西瓜" in q:
            return cls.get_pumpkin_melon_farm_bom(4)
        if "信标" in q or "金字塔" in q:
            tier = 4
            if "1级" in q or "一级" in q: tier = 1
            elif "2级" in q or "二级" in q: tier = 2
            elif "3级" in q or "三级" in q: tier = 3
            return cls.get_beacon_bom(tier)
        if "刷石" in q or "造石" in q or "圆石" in q:
            return cls.get_stone_generator_bom()
        if "分类机" in q or "分类漏斗" in q or "物品分类" in q:
            return cls.get_item_sorter_bom(1)
        if "时钟" in q or "漏斗时钟" in q or "etho" in q:
            return cls.get_etho_clock_bom()

        return None
