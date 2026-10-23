from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


@dataclass(frozen=True)
class ItemInstance:
    item_id: str
    count: int = 1
    durability: int = 0
    max_durability: int = 0
    custom_name: Optional[str] = None
    enchantments: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.item_id or self.item_id == "minecraft:air" or self.count <= 0

    @property
    def is_pickaxe(self) -> bool:
        return "pickaxe" in self.item_id.lower()

    @property
    def is_axe(self) -> bool:
        return "axe" in self.item_id.lower() and "pickaxe" not in self.item_id.lower()

    @property
    def is_shovel(self) -> bool:
        return "shovel" in self.item_id.lower()

    @property
    def is_hoe(self) -> bool:
        return "hoe" in self.item_id.lower()

    @property
    def harvest_tier(self) -> int:
        s = self.item_id.lower()
        if "netherite" in s:
            return 5
        if "diamond" in s:
            return 4
        if "iron" in s:
            return 3
        if "stone" in s:
            return 2
        if "golden" in s or "wooden" in s:
            return 1
        return 0


@dataclass(frozen=True)
class InventorySnapshot:
    main_hand: Optional[ItemInstance] = None
    off_hand: Optional[ItemInstance] = None
    helmet: Optional[ItemInstance] = None
    chestplate: Optional[ItemInstance] = None
    leggings: Optional[ItemInstance] = None
    boots: Optional[ItemInstance] = None
    hotbar: Dict[int, ItemInstance] = field(default_factory=dict)
    main_inventory: Dict[int, ItemInstance] = field(default_factory=dict)

    def count_item(self, item_id: str) -> int:
        if not item_id:
            return 0
        target = item_id.lower().replace("minecraft:", "").strip()
        total = 0

        for it in (self.main_hand, self.off_hand, self.helmet, self.chestplate, self.leggings, self.boots):
            if it and it.item_id.lower().replace("minecraft:", "").strip() == target:
                total += it.count

        for it in self.hotbar.values():
            if it and it.item_id.lower().replace("minecraft:", "").strip() == target:
                total += it.count

        for it in self.main_inventory.values():
            if it and it.item_id.lower().replace("minecraft:", "").strip() == target:
                total += it.count

        return total

    def has_item(self, item_id: str, count: int = 1) -> bool:
        return self.count_item(item_id) >= count

    def find_hotbar_slot(self, item_id: str) -> Optional[int]:
        target = item_id.lower().replace("minecraft:", "").strip()
        for slot, it in self.hotbar.items():
            if it and it.item_id.lower().replace("minecraft:", "").strip() == target:
                return slot
        return None

    def find_hotbar_tool(self, tool_type: str, min_tier: int) -> Optional[int]:
        t = tool_type.lower()
        for slot, it in self.hotbar.items():
            if it and not it.is_empty:
                matches = False
                if "pickaxe" in t and it.is_pickaxe:
                    matches = True
                elif "axe" in t and it.is_axe:
                    matches = True
                elif "shovel" in t and it.is_shovel:
                    matches = True
                elif "hoe" in t and it.is_hoe:
                    matches = True
                if matches and it.harvest_tier >= min_tier:
                    return slot
        return None

    @property
    def is_wearing_gold_armor(self) -> bool:
        for it in (self.helmet, self.chestplate, self.leggings, self.boots):
            if it and "golden_" in it.item_id.lower():
                return True
        return False

    @property
    def total_armor_points(self) -> int:
        score = 0
        for it in (self.helmet, self.chestplate, self.leggings, self.boots):
            if it:
                s = it.item_id.lower()
                if "netherite" in s or "diamond" in s:
                    score += 8 if "chestplate" in s else (6 if "leggings" in s else 3)
                elif "iron" in s:
                    score += 6 if "chestplate" in s else (5 if "leggings" in s else 2)
                elif "chainmail" in s or "golden" in s:
                    score += 5 if "chestplate" in s else (3 if "leggings" in s else 2)
                elif "leather" in s:
                    score += 3 if "chestplate" in s else (2 if "leggings" in s else 1)
        return min(20, score)


@dataclass(frozen=True)
class TargetEntity:
    entity_id: str
    custom_name: Optional[str] = None
    health: float = 20.0
    max_health: float = 20.0
    is_hostile: bool = False
    is_baby: bool = False
    is_tamed: bool = False
    profession: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)

    @property
    def is_villager(self) -> bool:
        return "villager" in self.entity_id and "zombie_villager" not in self.entity_id

    @property
    def is_zombie_villager(self) -> bool:
        return "zombie_villager" in self.entity_id

    @property
    def is_piglin(self) -> bool:
        return "piglin" in self.entity_id and "piglin_brute" not in self.entity_id

    @property
    def is_piglin_brute(self) -> bool:
        return "piglin_brute" in self.entity_id

    @property
    def is_warden(self) -> bool:
        return "warden" in self.entity_id

    @property
    def is_armadillo(self) -> bool:
        return "armadillo" in self.entity_id

    @property
    def is_iron_golem(self) -> bool:
        return "iron_golem" in self.entity_id

    def to_summary(self) -> str:
        name = self.custom_name if self.custom_name else self.entity_id
        prof = f" ({self.profession})" if self.profession else ""
        return f"{name}{prof} [HP: {self.health:.1f}/{self.max_health:.1f}, Hostile: {self.is_hostile}, Baby: {self.is_baby}]"


@dataclass(frozen=True)
class LogisticsReport:
    is_logistics_or_redstone: bool
    component_type: str
    state_details: str
    actionable_advice: str

    @classmethod
    def none(cls):
        return cls(False, "NONE", "非红石/物流交互方块", "")


@dataclass(frozen=True)
class HarvestReport:
    can_harvest_with_drops: bool
    tool_requirement_name: str
    min_tier: int
    current_tool_status: str
    hotbar_alternative_slot: Optional[int]
    advice: str


@dataclass(frozen=True)
class TargetBlock:
    block_id: str
    x: int
    y: int
    z: int
    block_light: int = 0
    sky_light: int = 0
    hardness: float = 1.0
    required_tool: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)

    @property
    def is_air(self) -> bool:
        return self.block_id in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")

    @property
    def total_light(self) -> int:
        return max(self.block_light, self.sky_light)

    @property
    def min_mining_tier(self) -> int:
        s = self.block_id.lower()
        if "ancient_debris" in s or "obsidian" in s:
            return 4
        if "diamond_ore" in s or "emerald_ore" in s or "gold_ore" in s or "redstone_ore" in s:
            return 3
        if "iron_ore" in s or "copper_ore" in s or "lapis_ore" in s:
            return 2
        if "stone" in s or "cobblestone" in s or "deepslate" in s:
            return 1
        return 0

    @property
    def canonical_tool_type(self) -> str:
        if self.required_tool:
            return self.required_tool.lower()
        s = self.block_id.lower()
        if "ore" in s or "stone" in s or "deepslate" in s or "obsidian" in s or "debris" in s:
            return "pickaxe"
        if "log" in s or "wood" in s or "planks" in s:
            return "axe"
        if "dirt" in s or "sand" in s or "gravel" in s:
            return "shovel"
        return "none"

    def evaluate_harvest(self, inventory: Optional[InventorySnapshot]) -> HarvestReport:
        if self.is_air:
            return HarvestReport(True, "无", 0, "准星对准空气", None, "无需工具")

        min_tier = self.min_mining_tier
        tool_type = self.canonical_tool_type
        held = inventory.main_hand if inventory else None

        drops_by_hand = min_tier == 0 and tool_type in ("none", "shovel", "axe")
        held_tier = held.harvest_tier if held else 0
        matches_type = False
        if held:
            if "pickaxe" in tool_type and held.is_pickaxe:
                matches_type = True
            elif "axe" in tool_type and held.is_axe:
                matches_type = True
            elif "shovel" in tool_type and held.is_shovel:
                matches_type = True

        if drops_by_hand or (matches_type and held_tier >= min_tier):
            return HarvestReport(
                True,
                f"{tool_type.upper()} (Tier {min_tier}+)",
                min_tier,
                held.item_id if held else "空手",
                None,
                "当前手持工具符合挖掘与掉落要求"
            )

        alt_slot = inventory.find_hotbar_tool(tool_type, min_tier) if inventory else None
        if alt_slot is not None:
            advice = f"警告：当前手持无法正常掉落！请按 [{alt_slot + 1}] 切换至快捷栏第 {alt_slot + 1} 格的可用工具！"
        else:
            advice = f"严重警告：该方块需要 {tool_type.upper()} (等级 ≥ {min_tier})，当前手持破坏将不会掉落任何物品！"

        return HarvestReport(
            False,
            f"{tool_type.upper()} (Tier {min_tier}+)",
            min_tier,
            held.item_id if held else "空手",
            alt_slot,
            advice
        )

    def evaluate_logistics_or_redstone(self) -> LogisticsReport:
        if self.is_air or not self.block_id:
            return LogisticsReport.none()
        s = self.block_id.lower()

        # 1. Hopper
        if "hopper" in s:
            facing = self.properties.get("facing", "down")
            enabled_str = self.properties.get("enabled", "true")
            locked = enabled_str.lower() == "false"
            state = (
                f"⚡ [已锁定 LOCKED] 漏斗被红石信号强充能锁定！当前朝向: {facing}"
                if locked
                else f"✔ [流通就绪 UNLOCKED] 漏斗处于正常非锁定流通状态。当前朝向: {facing}"
            )
            advice = (
                "警告：红石充能导致停止吸取与漏出物品！请检查紧邻红石粉、红石火把或强充能方块。"
                if locked
                else (
                    "传输速率: 2.5 组/秒 (4红石刻/个)。物品分类器推荐 41+1+1+1+1 (防串线) 或 18+1+1+1+1 布局。"
                    if facing == "down"
                    else "朝向侧方推入容器。若需向下传输请调整漏斗放置对准底部。"
                )
            )
            return LogisticsReport(True, "HOPPER", state, advice)

        # 2. Comparator
        if "comparator" in s:
            mode = self.properties.get("mode", "compare")
            is_sub = mode.lower() == "subtract"
            state = (
                "⚡ [减法模式 SUBTRACT (前置火把点亮)] 输出 = max(0, 后端信号 - max(左侧信号, 右侧信号))"
                if is_sub
                else "✔ [比较模式 COMPARE (前置火把熄灭)] 若后端输入 ≥ 两侧最大输入则输出后端信号，否则输出 0"
            )
            advice = "容器满度公式: 信号强度 = floor(1 + (当前物品数 / (格数 × 64)) × 14)。只要有 1 个物品至少输出 1 格信号。"
            return LogisticsReport(True, "COMPARATOR", state, advice)

        # 3. Repeater
        if "repeater" in s:
            delay = int(self.properties.get("delay", "1")) if self.properties.get("delay", "1").isdigit() else 1
            locked = self.properties.get("locked", "false").lower() == "true"
            state = f"{'🔒 [锁存锁定 LATCHED] ' if locked else '✔ [正常传导] '}延迟: {delay} 红石刻 ({delay * 2} 游戏刻 / {delay * 0.1:.1f}s)"
            advice = (
                "侧向通电的中继器正将此前状态锁存锁定！解除侧向信号方可恢复动态传导。"
                if locked
                else "满格 15 级信号强中继输出；右键可循环调节 1~4 刻延迟。"
            )
            return LogisticsReport(True, "REPEATER", state, advice)

        # 4. Observer
        if "observer" in s:
            facing = self.properties.get("facing", "south")
            powered = self.properties.get("powered", "false").lower() == "true"
            state = f"侦测面朝向: {facing} | 当前脉冲状态: {'发射中 (ACTIVE)' if powered else '待命 (IDLE)'}"
            advice = "感应前方方块状态更新 (BlockState Update)，后侧输出持续 1 红石刻 (2 游戏刻 / 0.1s) 瞬时脉冲。双侦测器面迎面相对可构成 2-tick 超高频时钟。"
            return LogisticsReport(True, "OBSERVER", state, advice)

        # 5. Crafter
        if "crafter" in s:
            orientation = self.properties.get("orientation", "north_up")
            triggered = self.properties.get("triggered", "false")
            state = f"1.21 自动合成器 | 朝向: {orientation} | 触发状态: {triggered}"
            advice = "接收红石上升沿脉冲瞬时合成并弹出成品！配合比较器可读取被禁用或有物品的槽位数 (0~9)。"
            return LogisticsReport(True, "CRAFTER", state, advice)

        # 6. Daylight Detector
        if "daylight_detector" in s:
            inverted = self.properties.get("inverted", "false").lower() == "true"
            state = "🌙 [夜间/反转模式 (月光探测)]" if inverted else "☀️ [白昼/正常模式 (日光探测)]"
            advice = (
                "黑夜与雷雨天光照降低时输出高电平，常用于全自动路灯与夜间警报。"
                if inverted
                else "白昼正午输出最高 15 级强电平，随太阳高度角升降动态衰减。右键可切换为反转模式。"
            )
            return LogisticsReport(True, "DAYLIGHT_DETECTOR", state, advice)

        # 7. Sculk Sensor
        if "sculk_sensor" in s:
            calibrated = "calibrated" in s
            phase = self.properties.get("sculk_sensor_phase", "inactive")
            state = f"{'💎 [校准型] ' if calibrated else '📡 [标准型] '}幽匿感测体 | 状态: {phase}"
            advice = (
                "通过后方/侧方红石信号 (1~15) 过滤单一频率 (1=移动, 6=装填, 12=受击, 13=死亡)；羊毛可 100% 阻隔振动传导。"
                if calibrated
                else "感应半径 8 格内振动波，输出强度对应振动频率 (1~15)；羊毛可 100% 隔音。"
            )
            return LogisticsReport(True, "SCULK_SENSOR", state, advice)

        # 8. Bubble Column (Soul sand & Magma)
        if "soul_sand" in s or "magma_block" in s:
            is_soul = "soul_sand" in s
            state = "🫧 [上升气泡柱基座]" if is_soul else "🌀 [下沉涡流基座]"
            advice = (
                "上方水域生成极速上升气泡柱 (约 11 格/秒) 并补充氧气。前置关键：垂直水柱每一格必须全部为【水源 (Water Source)】，可用海带顺水种植一键转化！"
                if is_soul
                else "上方水域生成极速向下涡流并消耗氧气。前置关键：垂直水柱每一格必须全部为【水源】。"
            )
            return LogisticsReport(True, "SOUL_SAND_BUBBLE" if is_soul else "MAGMA_BUBBLE", state, advice)

        # 9. Dropper & Dispenser
        if "dropper" in s or "dispenser" in s:
            is_dispenser = "dispenser" in s
            state = "🏹 [发射器 (Dispenser)]" if is_dispenser else "📦 [投掷器 (Dropper)]"
            advice = (
                "具备专属执行逻辑：射箭/药水、装填护甲/鞘翅、放置水桶岩浆、剪羊毛、点燃 TNT 等。不可用于常规无损物品管道！"
                if is_dispenser
                else "无论盛装何物，均以掉落物实体 (Item Entity) 吐出。适合垂直级联搭建投掷器物品升降机。"
            )
            return LogisticsReport(True, "DISPENSER" if is_dispenser else "DROPPER", state, advice)

        return LogisticsReport.none()

    def to_summary(self) -> str:
        if self.is_air:
            return "None (Looking at air / open sky)"
        tool = self.canonical_tool_type
        return (
            f"{self.block_id} at [{self.x}, {self.y}, {self.z}] "
            f"(Light: block={self.block_light}, sky={self.sky_light}, Hardness: {self.hardness:.1f}, Tool: {tool})"
        )


@dataclass(frozen=True)
class ContextSnapshot:
    player_name: str
    dimension: str
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    biome: str = "minecraft:plains"
    target_block: Optional[TargetBlock] = None
    main_hand_item: str = "minecraft:air"
    off_hand_item: str = "minecraft:air"
    health: float = 20.0
    hunger: int = 20
    active_effects: List[str] = field(default_factory=list)
    world_time_ticks: int = 6000
    is_raining: bool = False
    is_thundering: bool = False
    inventory: Optional[InventorySnapshot] = None
    target_entity: Optional[TargetEntity] = None

    @property
    def is_overworld(self) -> bool:
        dim = self.dimension.lower()
        return "overworld" in dim

    @property
    def is_nether(self) -> bool:
        dim = self.dimension.lower()
        return "nether" in dim

    @property
    def is_end(self) -> bool:
        dim = self.dimension.lower()
        return "end" in dim

    @property
    def block_x(self) -> int:
        return math.floor(self.x)

    @property
    def block_y(self) -> int:
        return math.floor(self.y)

    @property
    def block_z(self) -> int:
        return math.floor(self.z)

    @property
    def time_of_day_ticks(self) -> int:
        return self.world_time_ticks % 24000

    @property
    def is_night(self) -> bool:
        t = self.time_of_day_ticks
        return 13000 <= t <= 23000

    def get_nether_equivalent_coords(self) -> Tuple[int, int, int]:
        return (math.floor(self.x / 8.0), self.block_y, math.floor(self.z / 8.0))

    def get_overworld_equivalent_coords(self) -> Tuple[int, int, int]:
        return (math.floor(self.x * 8.0), self.block_y, math.floor(self.z * 8.0))

    def to_prompt_block(self) -> str:
        lines = [
            "<player_context>",
            f"Player: {self.player_name} | Health: {self.health:.1f}/20 | Hunger: {self.hunger}/20",
            f"Dimension: {self.dimension} | Biome: {self.biome}",
            f"Position: X={self.x:.1f}, Y={self.y:.1f}, Z={self.z:.1f} (Block: [{self.block_x}, {self.block_y}, {self.block_z}])",
            f"Facing: Yaw={self.yaw:.1f}, Pitch={self.pitch:.1f}",
            f"Main Hand: {self.main_hand_item} | Off Hand: {self.off_hand_item}",
        ]
        if self.inventory:
            lines.append(f"Armor Defense: {self.inventory.total_armor_points}/20 (Gold: {self.inventory.is_wearing_gold_armor})")
        if self.active_effects:
            lines.append(f"Active Effects: {', '.join(self.active_effects)}")
        lines.append(
            f"Environment: TimeTicks={self.time_of_day_ticks} ({'Night' if self.is_night else 'Day'}) | Rain={self.is_raining} | Thunder={self.is_thundering}"
        )
        if self.target_block and not self.target_block.is_air:
            lines.append(f"Target Block: {self.target_block.to_summary()}")
        if self.target_entity:
            lines.append(f"Target Entity: {self.target_entity.to_summary()}")
        lines.append("</player_context>")
        return "\n".join(lines)
