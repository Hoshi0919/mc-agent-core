class _CallableBool(int):
    def __call__(self):
        return bool(self)

from enum import Enum
import collections
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


@dataclass(frozen=True)
class BlockPos:
    x: int
    y: int
    z: int

    def offset(self, facing: Optional[str] = None, dx: int = 0, dy: int = 0, dz: int = 0) -> "BlockPos":
        if facing:
            f = facing.lower()
            if f == "down":
                return BlockPos(self.x, self.y - 1, self.z)
            elif f == "up":
                return BlockPos(self.x, self.y + 1, self.z)
            elif f == "north":
                return BlockPos(self.x, self.y, self.z - 1)
            elif f == "south":
                return BlockPos(self.x, self.y, self.z + 1)
            elif f == "west":
                return BlockPos(self.x - 1, self.y, self.z)
            elif f == "east":
                return BlockPos(self.x + 1, self.y, self.z)
        return BlockPos(self.x + dx, self.y + dy, self.z + dz)

    def manhattan_distance(self, other: "BlockPos") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)

    def neighbors(self) -> List["BlockPos"]:
        return self.get_direct_neighbors()

    def get_direct_neighbors(self) -> List["BlockPos"]:
        return [
            BlockPos(self.x, self.y - 1, self.z),
            BlockPos(self.x, self.y + 1, self.z),
            BlockPos(self.x, self.y, self.z - 1),
            BlockPos(self.x, self.y, self.z + 1),
            BlockPos(self.x - 1, self.y, self.z),
            BlockPos(self.x + 1, self.y, self.z),
        ]

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}, {self.z}]"


@dataclass(frozen=True)
class LocalBlock:
    pos: BlockPos
    block_id: str
    properties: Dict[str, str] = field(default_factory=dict)

    def get_property(self, key: str, default_val: str = "") -> str:
        return self.properties.get(key, default_val)

    def facing(self) -> str:
        return self.get_property("facing", "down").lower()

    def axis(self) -> str:
        return self.get_property("axis", "y").lower()

    @property
    def is_create_kinetics(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return any(k in bid for k in ["cogwheel", "shaft", "gearbox", "clutch", "gearshift", "water_wheel"])

    @property
    def is_cogwheel(self) -> bool:
        return "cogwheel" in self.block_id.lower() and "large" not in self.block_id.lower()

    @property
    def is_large_cogwheel(self) -> bool:
        return "large_cogwheel" in self.block_id.lower()

    @property
    def is_hopper(self) -> bool:
        return "hopper" in self.block_id.lower()

    @property
    def is_crafter(self) -> bool:
        return "crafter" in self.block_id.lower()

    @property
    def is_ae2(self) -> bool:
        if not self.block_id: return False
        bid = self.block_id.lower()
        return any(k in bid for k in ["ae2:", "controller", "cable", "p2p", "me_", "bus", "drive", "terminal", "interface", "assembler"])

    @property
    def is_ae2_controller(self) -> bool:
        if not self.block_id: return False
        bid = self.block_id.lower()
        return bid == "ae2:controller" or bid.endswith(":controller")

    @property
    def is_ae2_dense_cable(self) -> bool:
        if not self.block_id: return False
        bid = self.block_id.lower()
        return "dense" in bid and ("cable" in bid or "smart" in bid or "glass" in bid)

    @property
    def is_ae2_cable(self) -> bool:
        if not self.block_id: return False
        bid = self.block_id.lower()
        return ("cable" in bid or "glass_cable" in bid or "smart_cable" in bid) and not self.is_ae2_dense_cable

    @property
    def is_ae2_p2p_tunnel(self) -> bool:
        if not self.block_id: return False
        bid = self.block_id.lower()
        return "p2p" in bid or "me_p2p_tunnel" in bid

    @property
    def is_ae2_device(self) -> bool:
        if not self.block_id: return False
        if self.is_ae2_controller or self.is_ae2_cable or self.is_ae2_dense_cable: return False
        bid = self.block_id.lower()
        return any(k in bid for k in ["bus", "drive", "terminal", "interface", "provider", "assembler"]) or self.is_ae2_p2p_tunnel

    @property
    def is_water(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return "water" in bid or "bubble_column" in bid

    @property
    def is_water_source(self) -> bool:
        if not self.is_water:
            return False
        if "bubble_column" in self.block_id.lower():
            return True
        return self.get_property("level", "0") == "0"

    @property
    def is_flowing_water(self) -> bool:
        return self.is_water and not self.is_water_source

    @property
    def is_soul_sand(self) -> bool:
        return bool(self.block_id and "soul_sand" in self.block_id.lower())

    @property
    def is_magma_block(self) -> bool:
        return bool(self.block_id and "magma_block" in self.block_id.lower())

    @property
    def is_bubble_column(self) -> bool:
        return bool(self.block_id and "bubble_column" in self.block_id.lower())

    @property
    def is_ice(self) -> bool:
        return bool(self.block_id and "ice" in self.block_id.lower())

    @property
    def is_blue_ice(self) -> bool:
        return bool(self.block_id and "blue_ice" in self.block_id.lower())

    @property
    def is_honey_block(self) -> bool:
        return bool(self.block_id and "honey_block" in self.block_id.lower())

    @property
    def is_chest(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return "chest" in bid and "ender" not in bid

    @property
    def is_dropper(self) -> bool:
        return bool(self.block_id and "dropper" in self.block_id.lower())

    @property
    def is_sign(self) -> bool:
        return bool(self.block_id and "sign" in self.block_id.lower())

    @property
    def is_note_block(self) -> bool:
        return bool(self.block_id and "note_block" in self.block_id.lower())

    @property
    def is_trapdoor(self) -> bool:
        return bool(self.block_id and "trapdoor" in self.block_id.lower())

    @property
    def is_obsidian(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return "obsidian" in bid or "reinforced_deepslate" in bid

    @property
    def is_flying_component(self) -> bool:
        return (self.is_piston or self.is_observer or self.is_slime_block or
                self.is_honey_block or self.is_glazed_terracotta or self.is_note_block or
                self.is_trapdoor or self.is_obsidian)

    @property
    def is_air(self) -> bool:
        if not self.block_id:
            return True
        bid = self.block_id.lower()
        return bid in ("air", "minecraft:air", "cave_air", "minecraft:cave_air", "void_air", "minecraft:void_air")


    @property
    def is_rail(self) -> bool:
        return bool(self.block_id and "rail" in self.block_id.lower())

    @property
    def is_powered_rail(self) -> bool:
        return bool(self.block_id and "powered_rail" in self.block_id.lower())

    @property
    def is_detector_rail(self) -> bool:
        return bool(self.block_id and "detector_rail" in self.block_id.lower())

    @property
    def is_activator_rail(self) -> bool:
        return bool(self.block_id and "activator_rail" in self.block_id.lower())

    @property
    def is_normal_rail(self) -> bool:
        return self.is_rail and not (self.is_powered_rail or self.is_detector_rail or self.is_activator_rail)

    @property
    def rail_shape(self) -> str:
        return self.get_property("shape", "north_south").lower()

    @property
    def is_ascending_rail(self) -> bool:
        return self.rail_shape.startswith("ascending")


    @property
    def is_solid_conductive_block(self) -> bool:
        if not self.block_id or self.is_air:
            return False
        bid = self.block_id.lower()
        if any(k in bid for k in ["glass", "slab", "stairs", "glowstone", "leaves", "ice", "hopper", "chest", "fence", "wall", "piston", "door", "trapdoor", "wire", "torch", "lever", "button", "pressure_plate", "rail"]):
            return False
        return True

    @property
    def is_comparator(self) -> bool:
        return bool(self.block_id and "comparator" in self.block_id.lower())

    @property
    def is_repeater(self) -> bool:
        return bool(self.block_id and "repeater" in self.block_id.lower())

    @property
    def is_observer(self) -> bool:
        return bool(self.block_id and "observer" in self.block_id.lower())


    @property
    def is_copper_bulb(self) -> bool:
        return bool(self.block_id and "copper_bulb" in self.block_id.lower())

    @property
    def is_copper_bulb_lit(self) -> bool:
        return self.is_copper_bulb and self.get_property("lit", "false").lower() == "true"

    @property
    def is_button(self) -> bool:
        return bool(self.block_id and "button" in self.block_id.lower())

    @property
    def is_lever(self) -> bool:
        return bool(self.block_id and "lever" in self.block_id.lower())

    @property
    def is_redstone_torch(self) -> bool:
        return bool(self.block_id and "redstone_torch" in self.block_id.lower())

    @property
    def is_powered(self) -> _CallableBool:
        val = self.get_property("powered", "false").lower() == "true"
        return _CallableBool(1 if val else 0) 

    @property
    def is_redstone_wire(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return "redstone_wire" in bid or bid == "minecraft:redstone"

    @property
    def is_container(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return any(k in bid for k in ["chest", "shulker_box", "barrel", "dropper", "dispenser", "crafter", "furnace", "hopper", "brewing_stand"])

    @property
    def is_piston(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        return ("piston" in bid or bid == "minecraft:piston" or bid == "minecraft:sticky_piston") and "piston_head" not in bid

    @property
    def is_sticky_piston(self) -> bool:
        if not self.block_id:
            return False
        return "sticky_piston" in self.block_id.lower()

    @property
    def is_extended(self) -> _CallableBool:
        val = self.get_property("extended", "false").lower() == "true"
        return _CallableBool(1 if val else 0)

    @property
    def is_slime_block(self) -> bool:
        return bool(self.block_id and "slime_block" in self.block_id.lower())

    @property
    def honey_block(self) -> bool:
        return self.is_honey_block

    @property
    def is_honey_block(self) -> bool:
        return bool(self.block_id and "honey_block" in self.block_id.lower())

    @property
    def is_glazed_terracotta(self) -> bool:
        return bool(self.block_id and "glazed_terracotta" in self.block_id.lower())

    @property
    def is_immovable(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        if any(k in bid for k in [
            "bedrock", "obsidian", "crying_obsidian", "nether_portal", "end_portal",
            "reinforced_deepslate", "piston_head"
        ]):
            return True
        if any(k in bid for k in [
            "chest", "barrel", "shulker_box", "furnace", "smoker", "blast_furnace",
            "hopper", "dispenser", "dropper", "brewing_stand", "crafter", "beacon",
            "enchanting_table", "spawner", "sculk_sensor", "sculk_catalyst", "sculk_shrieker"
        ]):
            return True
        return False

    @property
    def is_shulker_box(self) -> bool:
        return bool(self.block_id and "shulker_box" in self.block_id.lower())

    @property
    def is_dispenser(self) -> bool:
        return bool(self.block_id and "dispenser" in self.block_id.lower())

    @property
    def is_shulker_component(self) -> bool:
        return (self.is_shulker_box or self.is_dispenser or self.is_dropper or
                self.is_hopper or self.is_comparator or self.is_piston)

    @property
    def is_redstone_power_source(self) -> bool:
        if not self.block_id:
            return False
        bid = self.block_id.lower()
        if "redstone_block" in bid:
            return True
        if "redstone_torch" in bid and self.get_property("lit", "true").lower() != "false":
            return True
        if "redstone_wire" in bid and (self.get_property("power", "0") != "0" or self.get_property("powered", "false").lower() == "true"):
            return True
        if any(k in bid for k in ["lever", "button", "pressure_plate"]) and self.get_property("powered", "false").lower() == "true":
            return True
        if any(k in bid for k in ["repeater", "comparator", "observer"]) and self.get_property("powered", "false").lower() == "true":
            return True
        return self.get_property("powered", "false").lower() == "true"



@dataclass
class LocalMachineCluster:
    origin: BlockPos
    blocks: Dict[BlockPos, LocalBlock] = field(default_factory=dict)

    def add(self, x: int, y: int, z: int, block_id: str, properties: Optional[Dict[str, str]] = None) -> "LocalMachineCluster":
        pos = BlockPos(x, y, z)
        self.blocks[pos] = LocalBlock(pos, block_id, properties or {})
        return self

    def get_connected_kinetics(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_create_kinetics]

    def get_connected_hoppers(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_hopper]

    def get_connected_ae2(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_ae2]

    def get_connected_pistons(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_piston]

    def get_connected_comparators(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_comparator]



    def get_connected_rails(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_rail]

    def get_connected_copper_bulbs(self) -> List[LocalBlock]:
        return [b for b in self.blocks.values() if b.is_copper_bulb]

    def get_block(self, pos: BlockPos) -> Optional[LocalBlock]:
        return self.blocks.get(pos)

    @property
    def origin_block(self) -> Optional[LocalBlock]:
        return self.blocks.get(self.origin)

    @property
    def size(self) -> int:
        return len(self.blocks)

    @property
    def is_empty(self) -> bool:
        return len(self.blocks) == 0

    def to_summary(self) -> str:
        return f"Cluster centered at {self.origin} with {self.size} blocks (Kinetics: {len(self.get_connected_kinetics())}, Hoppers: {len(self.get_connected_hoppers())}, AE2: {len(self.get_connected_ae2())}, Pistons: {len(self.get_connected_pistons())}, Comparators: {len(self.get_connected_comparators())})"


@dataclass
class KineticReport:
    is_healthy: bool
    is_jammed: bool
    total_components: int
    conflicts: List[str]
    primary_diagnosis: str
    actionable_remediation: str


class KineticNetworkAnalyzer:
    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster]) -> KineticReport:
        if not cluster or not cluster.blocks:
            return KineticReport(True, False, 0, [], "未检测到机械动力组件", "")

        kinetics = cluster.get_connected_kinetics()
        if not kinetics:
            return KineticReport(True, False, 0, [], "未检测到机械动力组件", "")

        k_map = {b.pos: b for b in kinetics}
        state_map: Dict[BlockPos, Tuple[float, int]] = {}
        conflicts: List[str] = []

        for start in kinetics:
            if start.pos in state_map:
                continue
            queue = [start.pos]
            state_map[start.pos] = (1.0, 1)

            while queue:
                curr_pos = queue.pop(0)
                curr_block = k_map[curr_pos]
                curr_speed, curr_sign = state_map[curr_pos]

                for nb_pos in curr_pos.get_direct_neighbors():
                    nb = k_map.get(nb_pos)
                    if not nb:
                        continue
                    connected, mult, sign_flip = KineticNetworkAnalyzer._transmission(curr_block, nb)
                    if not connected:
                        continue

                    exp_speed = curr_speed * mult
                    exp_sign = curr_sign * sign_flip

                    if nb_pos not in state_map:
                        state_map[nb_pos] = (exp_speed, exp_sign)
                        queue.append(nb_pos)
                    else:
                        exist_speed, exist_sign = state_map[nb_pos]
                        sign_conflict = exist_sign != exp_sign
                        speed_conflict = abs(exist_speed - exp_speed) > 1e-4
                        if sign_conflict or speed_conflict:
                            conf = f"动力冲突: {curr_block.block_id} {curr_pos} 与 {nb.block_id} {nb_pos} 啮合矛盾 (方向冲突={sign_conflict}, 转速比矛盾: 现有={exist_speed:.2f}x, 传入={exp_speed:.2f}x)"
                            if conf not in conflicts:
                                conflicts.append(conf)

        if conflicts:
            return KineticReport(
                is_healthy=False,
                is_jammed=True,
                total_components=len(kinetics),
                conflicts=conflicts,
                primary_diagnosis=f"⚡ [动力网卡死 JAMMED] 检测到 {len(conflicts)} 处机械传动冲突导致整线锁死！",
                actionable_remediation="排查建议：相邻齿轮之间形成了奇数环路或反向啮合回环。请拆除冲突处的任一从动齿轮，或接入换向齿轮箱 (Gearbox) 进行相位配平！"
            )

        return KineticReport(
            is_healthy=True,
            is_jammed=False,
            total_components=len(kinetics),
            conflicts=[],
            primary_diagnosis=f"✔ 动力网络包含 {len(kinetics)} 个机械动力组件，全部转速比与啮合方向完全匹配自洽。",
            actionable_remediation="动力网络拓扑健康，传动顺畅无冲突。"
        )

    @staticmethod
    def _transmission(a: LocalBlock, b: LocalBlock) -> Tuple[bool, float, int]:
        axis_a, axis_b = a.axis(), b.axis()
        dx = b.pos.x - a.pos.x
        dy = b.pos.y - a.pos.y
        dz = b.pos.z - a.pos.z

        # Collinear axial
        is_collinear = (
            (axis_a == "x" and axis_b == "x" and dy == 0 and dz == 0 and abs(dx) == 1) or
            (axis_a == "y" and axis_b == "y" and dx == 0 and dz == 0 and abs(dy) == 1) or
            (axis_a == "z" and axis_b == "z" and dx == 0 and dy == 0 and abs(dz) == 1)
        )
        if is_collinear:
            return True, 1.0, 1

        # Spur Gear mesh
        parallel = axis_a == axis_b
        perpendicular = (
            (axis_a == "y" and dy == 0 and (abs(dx) + abs(dz) == 1)) or
            (axis_a == "x" and dx == 0 and (abs(dy) + abs(dz) == 1)) or
            (axis_a == "z" and dz == 0 and (abs(dx) + abs(dz) == 1))
        )
        if parallel and perpendicular:
            a_s, b_s = a.is_cogwheel, b.is_cogwheel
            a_l, b_l = a.is_large_cogwheel, b.is_large_cogwheel
            if (a_s and b_s) or (a_l and b_l):
                return True, 1.0, -1
            if a_s and b_l:
                return True, 0.5, -1
            if a_l and b_s:
                return True, 2.0, -1

        return False, 1.0, 1


@dataclass
class HopperReport:
    is_healthy: bool
    has_deadlock: bool
    has_backpressure: bool
    has_bleed_risk: bool
    total_hoppers: int
    deadlocks: List[str]
    stalled_hoppers: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str


class HopperNetworkAnalyzer:
    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster]) -> HopperReport:
        if not cluster or not cluster.blocks:
            return HopperReport(True, False, False, False, 0, [], [], [], "未检测到漏斗组件", "")

        hoppers = cluster.get_connected_hoppers()
        if not hoppers:
            return HopperReport(True, False, False, False, 0, [], [], [], "未检测到漏斗组件", "")

        h_map = {h.pos: h for h in hoppers}
        forward_edges: Dict[BlockPos, BlockPos] = {}
        stalled: List[str] = []
        warnings: List[str] = []

        for h in hoppers:
            target_pos = h.pos.offset(facing=h.facing())
            forward_edges[h.pos] = target_pos

            if h.get_property("full") == "true" or h.get_property("enabled") == "false":
                stalled.append(f"漏斗 {h.pos} 停滞")

            target_block = cluster.blocks.get(target_pos)
            if target_block and target_block.get_property("full") == "true":
                stalled.append(f"漏斗 {h.pos} 下游容器已满")

        # Cycle detection
        deadlocks: List[str] = []
        visited: Set[BlockPos] = set()
        rec_stack: Set[BlockPos] = set()

        def dfs(curr: BlockPos, path: List[BlockPos]):
            visited.add(curr)
            rec_stack.add(curr)
            path.append(curr)

            nxt = forward_edges.get(curr)
            if nxt and nxt in h_map:
                if nxt not in visited:
                    dfs(nxt, path)
                elif nxt in rec_stack:
                    idx = path.index(nxt)
                    deadlocks.append(" -> ".join(str(p) for p in path[idx:] + [nxt]))

            rec_stack.remove(curr)
            path.pop()

        for pos in h_map:
            if pos not in visited:
                dfs(pos, [])

        # Sorter bleed
        comparators = [b for b in cluster.blocks.values() if "comparator" in b.block_id.lower()]
        has_bleed_risk = False
        opp_facing = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "down", "down": "up"}
        for comp in comparators:
            src_pos = comp.pos.offset(facing=opp_facing.get(comp.facing(), "north"))
            src_block = cluster.blocks.get(src_pos)
            if src_block and src_block.is_hopper:
                count = int(src_block.get_property("item_count", "0") or "0")
                if count >= 46:
                    has_bleed_risk = True
                    warnings.append(f"分类器串线警报: 漏斗 {src_pos} 容纳 {count} 物品导致信号 ≥3 级击穿！")

        has_deadlock = len(deadlocks) > 0
        has_backpressure = len(stalled) > 0
        is_healthy = not has_deadlock and not has_backpressure and not has_bleed_risk

        if has_deadlock:
            return HopperReport(False, True, has_backpressure, has_bleed_risk, len(hoppers), deadlocks, stalled, warnings,
                                f"⚡ [漏斗死锁 DEADLOCK] 检测到 {len(deadlocks)} 处闭环回路！", "解决建议：断开死循环回路。")
        if has_bleed_risk:
            return HopperReport(False, False, has_backpressure, True, len(hoppers), deadlocks, stalled, warnings,
                                "⚡ [分类器串线击穿风险] 过滤漏斗物品积压超标！", "解决建议：恢复标准 41+1+1+1+1 布局。")
        if has_backpressure:
            return HopperReport(False, False, True, False, len(hoppers), deadlocks, stalled, warnings,
                                f"⚠ [背压停滞 BACKPRESSURE] 检测到 {len(stalled)} 处堵塞！", "排查建议：检查下游容器。")

        return HopperReport(True, False, False, False, len(hoppers), [], [], [],
                            f"✔ 漏斗网络包含 {len(hoppers)} 个漏斗，流向拓扑健康顺畅。", "无需干预。")


@dataclass
class CrafterReport:
    is_healthy: bool
    has_deadlock_risk: bool
    has_masking_deficit: bool
    required_slots: int
    disabled_slots: int
    active_filled_slots: int
    issues: List[str]
    primary_diagnosis: str
    actionable_advice: str


class CrafterPipelineAnalyzer:
    @staticmethod
    def analyze(crafter_block: Optional[LocalBlock], cluster: Optional[LocalMachineCluster] = None, target_recipe: Optional[str] = None) -> CrafterReport:
        if not crafter_block or not crafter_block.is_crafter:
            return CrafterReport(True, False, False, 0, 0, 0, [], "未检测到 1.21 自动合成器", "")

        disabled = int(crafter_block.get_property("disabled_slots", "0") or "0")
        filled = int(crafter_block.get_property("filled_slots", "0") or "0")

        exp_slots = 9
        if target_recipe:
            rec = target_recipe.lower()
            if "chestplate" in rec: exp_slots = 8
            elif "leggings" in rec: exp_slots = 7
            elif "helmet" in rec or "pickaxe" in rec: exp_slots = 5
            elif "sword" in rec: exp_slots = 3

        exp_disabled = 9 - exp_slots
        masking_deficit = disabled < exp_disabled
        issues = []
        if masking_deficit:
            issues.append(f"槽位遮罩不足: 应禁用 {exp_disabled} 格，当前仅禁用 {disabled} 格！")

        feeders = []
        if cluster:
            for nb_pos in crafter_block.pos.get_direct_neighbors():
                nb = cluster.blocks.get(nb_pos)
                if nb and nb.is_hopper and crafter_block.pos == nb_pos.offset(facing=nb.facing()):
                    feeders.append(nb)

        deadlock_risk = exp_slots < 9 and target_recipe and "sword" in target_recipe.lower() and len(feeders) == 1
        if deadlock_risk:
            issues.append("单漏斗混投多原料死锁高危！")

        if masking_deficit or deadlock_risk:
            return CrafterReport(False, deadlock_risk, masking_deficit, exp_slots, disabled, filled, issues,
                                 "⚡ [自动合成器流水线缺陷] 槽位未遮罩或供料失衡！", "建议：手动红色禁用多余槽位并脉冲投料。")

        return CrafterReport(True, False, False, exp_slots, disabled, filled, [], f"✔ 自动合成器配置健康 [{target_recipe}]", "无需干预。")


from collections import deque

@dataclass
class Ae2Report:
    is_healthy: bool
    has_multiblock_error: bool
    has_channel_overload: bool
    has_p2p_loop: bool
    total_controllers: int
    total_cables: int
    total_dense_cables: int
    total_devices: int
    online_devices: int
    missing_channel_devices: int
    illegal_interior_controllers: List[BlockPos]
    overloaded_cables: List[BlockPos]
    offline_devices: List[BlockPos]
    issues: List[str]
    primary_diagnosis: str
    actionable_remediation: str

    def format_report(self) -> str:
        lines = [
            "§b【AE2 数字化网络：频道拓扑与控制器诊断】§r",
            f"§7- 控制器: §f{self.total_controllers}块§7 | 普通线缆(8ch): §f{self.total_cables}§7 | 致密线缆(32ch): §f{self.total_dense_cables}§7 | 终端设备: §e{self.total_devices}台§r"
        ]
        if self.is_healthy:
            lines.append(f"§a✔ 网络工况健康：全部 {self.online_devices} 台设备在线 (100% 频道覆盖)！§r")
        else:
            lines.append("§c❌ 拓扑异常警告：检测到网络阻断与配置缺陷！§r")
            if self.has_multiblock_error: lines.append("§c  * 控制器多方块结构非法！整网陷入瘫痪！§r")
            if self.has_channel_overload: lines.append(f"§6  * 频道过载耗尽：已有 {self.missing_channel_devices} 台终端设备因抢不到频道而掉线 (Missing Channel)！§r")
            if self.has_p2p_loop: lines.append("§d  * 检测到 P2P 隧道自引用回环死锁！§r")
        if self.issues:
            lines.append("§e具体异常清单：§r")
            for iss in self.issues: lines.append(f"  §7- §f{iss}§r")
        if self.actionable_remediation:
            lines.append("§a建议整改方案：§r")
            lines.append(f"  §7* §f{self.actionable_remediation}§r")
        return "\n".join(lines)


class Ae2NetworkAnalyzer:
    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster]) -> Ae2Report:
        if not cluster or cluster.is_empty:
            return Ae2Report(True, False, False, False, 0, 0, 0, 0, 0, 0, [], [], [], [], "未检测到 AE2 数字化网络组件", "")

        ae2_blocks = cluster.get_connected_ae2()
        if not ae2_blocks:
            return Ae2Report(True, False, False, False, 0, 0, 0, 0, 0, 0, [], [], [], [], "未检测到 AE2 数字化网络组件", "")

        block_map = {b.pos: b for b in ae2_blocks}
        controllers = [b for b in ae2_blocks if b.is_ae2_controller]
        dense_cables = [b for b in ae2_blocks if b.is_ae2_dense_cable]
        regular_cables = [b for b in ae2_blocks if b.is_ae2_cable]
        p2p_tunnels = [b for b in ae2_blocks if b.is_ae2_p2p_tunnel]
        devices = [b for b in ae2_blocks if b.is_ae2_device]

        issues = []
        illegal_interior = []
        overloaded_cables = []
        offline_devices = []
        multiblock_error = False
        channel_overload = False
        p2p_loop = False

        if controllers:
            ctrl_set = {c.pos for c in controllers}
            min_x = min(p.x for p in ctrl_set); max_x = max(p.x for p in ctrl_set)
            min_y = min(p.y for p in ctrl_set); max_y = max(p.y for p in ctrl_set)
            min_z = min(p.z for p in ctrl_set); max_z = max(p.z for p in ctrl_set)
            span_x = max_x - min_x + 1
            span_y = max_y - min_y + 1
            span_z = max_z - min_z + 1
            if span_x > 7 or span_y > 7 or span_z > 7:
                multiblock_error = True
                issues.append(f"控制器尺寸超限：包围盒为 {span_x}x{span_y}x{span_z} 方块（规则严禁超过 7x7x7）")

            for c in controllers:
                if sum(1 for n in c.pos.get_direct_neighbors() if n in ctrl_set) == 6:
                    multiblock_error = True
                    illegal_interior.append(c.pos)
                    issues.append(f"控制器实心内部违规：坐标 {c.pos} 处于 2x2x2 封闭立方体核心内部（无任何外表面暴露）")

            visited = set()
            queue = deque([controllers[0].pos])
            visited.add(controllers[0].pos)
            while queue:
                curr = queue.popleft()
                for n in curr.get_direct_neighbors():
                    if n in ctrl_set and n not in visited:
                        visited.add(n)
                        queue.append(n)
            if len(visited) < len(controllers):
                multiblock_error = True
                issues.append(f"控制器多结构冲突：网络中存在 {len(controllers) - len(visited) + 1} 个未连通的独立控制器构架")

        total_dev = len(devices)
        if not controllers:
            if total_dev > 8:
                channel_overload = True
                deficit = total_dev - 8
                issues.append(f"无控制器 (Ad-hoc) 网络频道超限：挂载了 {total_dev} 台设备（上限 8 频道），末端 {deficit} 台设备已掉线")
                for i in range(8, total_dev):
                    offline_devices.append(devices[i].pos)
        elif not multiblock_error:
            depth_map = {}
            parent_map = {}
            queue = deque()
            for c in controllers:
                depth_map[c.pos] = 0
                queue.append(c.pos)

            visit_order = []
            while queue:
                curr = queue.popleft()
                visit_order.append(curr)
                d = depth_map[curr]
                for n in curr.get_direct_neighbors():
                    if n in block_map and n not in depth_map:
                        depth_map[n] = d + 1
                        parent_map[n] = curr
                        queue.append(n)

            channel_demand = {dev.pos: 1 for dev in devices}
            for node in reversed(visit_order):
                demand = channel_demand.get(node, 0)
                parent = parent_map.get(node)
                if parent:
                    channel_demand[parent] = channel_demand.get(parent, 0) + demand

                block = block_map.get(node)
                if block:
                    cap = 32 if block.is_ae2_dense_cable else (8 if block.is_ae2_cable else 1024)
                    if (block.is_ae2_dense_cable or block.is_ae2_cable) and demand > cap:
                        channel_overload = True
                        overloaded_cables.append(node)
                        issues.append(f"线缆频道过载：{node} 承载了 {demand} 个频道（容量上限 {cap} 频道），超出 {demand - cap} 个频道！")

            for dev in devices:
                curr = dev.pos
                starved = False
                while curr:
                    blk = block_map.get(curr)
                    if blk:
                        cap = 32 if blk.is_ae2_dense_cable else (8 if blk.is_ae2_cable else 1024)
                        if channel_demand.get(curr, 0) > cap:
                            starved = True
                            break
                    curr = parent_map.get(curr)
                if starved and dev.pos not in offline_devices:
                    offline_devices.append(dev.pos)

        if len(p2p_tunnels) >= 2:
            for p2p in p2p_tunnels:
                freq = p2p.get_property("frequency", "").lower()
                if freq in ["carrier", "loop"]:
                    p2p_loop = True
                    issues.append(f"P2P 隧道自引用死锁：隧道 {p2p.pos} 频率绑定产生回环，载体与输出陷入递归循环！")

        missing_count = len(offline_devices)
        online_count = max(0, total_dev - missing_count)
        is_healthy = not multiblock_error and not channel_overload and not p2p_loop

        if is_healthy:
            diag = f"✔ AE2 网络拓扑健康（{total_dev} 台设备全部在线，0 频道溢出）"
            rem = "当前网络布线合理。若未来新增机器，请注意保持各支路 8/32 频道裕度，或使用致密线缆/P2P 扩展。"
        elif multiblock_error:
            diag = "❌ 控制器多方块结构严重违规，网络离线停摆！"
            rem = f"立即拆除内部实心坐标 {illegal_interior[0]} 处的控制器方块，使其保持中空或外表面暴露！" if illegal_interior else "检查控制器尺寸使其严格限制在 7x7x7 内，并确保所有控制器方块紧密相连为一个整体结构。"
        elif channel_overload:
            diag = f"⚠ 频道超载导致 {missing_count} 台设备掉线 (Missing Channel)！"
            rem = "将过载处的普通线缆（8 频道）升级为致密线缆（32 频道），或使用 P2P 隧道建立点对点压缩传输。"
        else:
            diag = "⚠ P2P 隧道配置错误导致逻辑回环！"
            rem = "重置 P2P 频率，确保载体子网与数据终端子网保持物理电气隔离。"

        return Ae2Report(
            is_healthy, multiblock_error, channel_overload, p2p_loop,
            len(controllers), len(regular_cables), len(dense_cables),
            total_dev, online_count, missing_count,
            illegal_interior, overloaded_cables, offline_devices,
            issues, diag, rem
        )



@dataclass(frozen=True)
class PistonReport:
    is_healthy: bool
    is_directly_powered: bool
    is_qc_powered: bool
    is_bud_locked: bool
    is_bud_pending: bool
    is_push_limit_exceeded: bool
    has_immovable_obstacle: bool
    piston_pos: BlockPos
    piston_facing: str
    push_chain_count: int
    push_chain: List[BlockPos]
    direct_power_sources: List[BlockPos]
    qc_power_sources: List[BlockPos]
    immovable_blocks: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    @classmethod
    def empty(cls) -> "PistonReport":
        return PistonReport(
            is_healthy=True,
            is_directly_powered=False,
            is_qc_powered=False,
            is_bud_locked=False,
            is_bud_pending=False,
            is_push_limit_exceeded=False,
            has_immovable_obstacle=False,
            piston_pos=BlockPos(0, 0, 0),
            piston_facing="unknown",
            push_chain_count=0,
            push_chain=[],
            direct_power_sources=[],
            qc_power_sources=[],
            immovable_blocks=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到活塞机械组件",
            actionable_advice=""
        )

    def format_report(self) -> str:
        sb = []
        sb.append("§e【红石活塞与准连接 (QC) 拓扑诊断报告】§r")
        sb.append(f"▸ 目标活塞坐标：{self.piston_pos} (朝向: {self.piston_facing.upper()})")
        dp_str = "§a直接供电§r" if self.is_directly_powered else "§7无直接供电§r"
        qc_str = "§b激活 (QC)§r" if self.is_qc_powered else "§7无§r"
        sb.append(f"▸ 供电状态：{dp_str} | 准连接(QC): {qc_str}")

        if self.is_bud_locked:
            sb.append("  ⚡ §c[BUD 锁定卡死] 供电已断开，但缺少方块更新导致活塞保持伸出！§r")
        elif self.is_bud_pending:
            sb.append("  ⚡ §6[BUD 待命潜伏] 上方 QC 已充能，等待邻域方块更新触发弹出！§r")

        pl_str = "§c[超重 >12]§r" if self.is_push_limit_exceeded else "§a[正常]§r"
        sb.append(f"▸ 推块链条负载：{self.push_chain_count} / 12 方块 {pl_str}")

        if self.direct_power_sources:
            srcs = " ".join(str(p) for p in self.direct_power_sources)
            sb.append(f"  - 直接供电源: {srcs}")
        if self.qc_power_sources:
            srcs = " ".join(str(p) for p in self.qc_power_sources)
            sb.append(f"  - 准连接 (QC) 隔电源: {srcs}")
        if self.immovable_blocks:
            srcs = " ".join(str(p) for p in self.immovable_blocks)
            sb.append(f"  ✖ §c不可移动阻断方块: {srcs}§r")

        if self.issues:
            sb.append("§c【发现问题】§r")
            for iss in self.issues:
                sb.append(f"  ✖ {iss}")
        if self.warnings:
            sb.append("§6【注意事项】§r")
            for w in self.warnings:
                sb.append(f"  ⚠ {w}")

        sb.append(f"▸ 诊断结论：{self.primary_diagnosis}")
        sb.append(f"▸ 优化建议：{self.actionable_advice}")
        return "\n".join(sb)


class PistonRedstoneAnalyzer:
    @classmethod
    def analyze(cls, cluster: Optional[LocalMachineCluster], target_pos: Optional[BlockPos] = None) -> PistonReport:
        if not cluster or cluster.is_empty:
            return PistonReport.empty()

        piston = None
        if target_pos:
            piston = cluster.get_block(target_pos)
        if not piston or not piston.is_piston:
            org = cluster.origin_block
            if org and org.is_piston:
                piston = org
        if not piston or not piston.is_piston:
            pistons = cluster.get_connected_pistons()
            if pistons:
                piston = pistons[0]

        if not piston or not piston.is_piston:
            return PistonReport.empty()

        p_pos = piston.pos
        facing = piston.facing()
        extended = piston.is_extended

        direct_power: List[BlockPos] = []
        qc_power: List[BlockPos] = []
        immovables: List[BlockPos] = []
        issues: List[str] = []
        warnings: List[str] = []

        # 1. Direct Powering Check (6 direct neighbors)
        for n_pos in p_pos.get_direct_neighbors():
            n_block = cluster.get_block(n_pos)
            if n_block and n_block.is_redstone_power_source:
                direct_power.append(n_pos)

        # 2. Quasi-Connectivity (QC) Check
        above_pos = p_pos.offset("up")
        direct_set = set(p_pos.get_direct_neighbors())

        above_block = cluster.get_block(above_pos)
        if above_block and above_block.is_redstone_power_source:
            if above_pos not in direct_set:
                qc_power.append(above_pos)

        qc_candidates = [
            above_pos.offset("up"),
            above_pos.offset("north"),
            above_pos.offset("south"),
            above_pos.offset("west"),
            above_pos.offset("east"),
        ]
        for qp in qc_candidates:
            if qp not in direct_set:
                q_block = cluster.get_block(qp)
                if q_block and q_block.is_redstone_power_source:
                    qc_power.append(qp)

        is_directly_powered = len(direct_power) > 0
        is_qc_powered = len(qc_power) > 0

        # 3. BUD State Machine
        is_bud_locked = extended and not is_directly_powered and not is_qc_powered
        is_bud_pending = not extended and not is_directly_powered and is_qc_powered

        if is_bud_locked:
            issues.append(f"活塞 {p_pos} 处于 BUD 锁定状态：红石源已切断，因未收到方块更新依然保持伸出！")
        if is_bud_pending:
            warnings.append(f"活塞 {p_pos} 上方存在准连接 (QC) 充能但未更新：一旦邻近方块发生改变将立即弹出！")

        # 4. Push Chain & Adhesion BFS
        push_chain: List[BlockPos] = []
        is_push_limit_exceeded = False
        has_immovable_obstacle = False

        step_pos = p_pos.offset(facing)
        visited_in_chain: Set[BlockPos] = set()
        from collections import deque
        queue = deque()

        first_block = cluster.get_block(step_pos)
        if first_block and not first_block.is_air:
            queue.append(step_pos)
            visited_in_chain.add(step_pos)

        while queue:
            current = queue.popleft()
            cur_block = cluster.get_block(current)
            if not cur_block or cur_block.is_air:
                continue

            if cur_block.is_immovable:
                has_immovable_obstacle = True
                immovables.append(current)
                issues.append(f"遭遇不可移动方块 {current} ({cur_block.block_id})，阻断活塞推动！")
                continue

            push_chain.append(current)

            next_in_line = current.offset(facing)
            if next_in_line not in visited_in_chain:
                next_block = cluster.get_block(next_in_line)
                if next_block and not next_block.is_air:
                    visited_in_chain.add(next_in_line)
                    queue.append(next_in_line)

            is_slime = cur_block.is_slime_block
            is_honey = cur_block.is_honey_block

            if is_slime or is_honey:
                for neighbor in current.get_direct_neighbors():
                    if neighbor == p_pos or neighbor in visited_in_chain:
                        continue
                    n_block = cluster.get_block(neighbor)
                    if not n_block or n_block.is_air:
                        continue

                    if is_slime and n_block.is_honey_block:
                        continue
                    if is_honey and n_block.is_slime_block:
                        continue
                    if n_block.is_glazed_terracotta:
                        continue

                    visited_in_chain.add(neighbor)
                    queue.append(neighbor)

        push_chain_count = len(push_chain)
        if push_chain_count > 12:
            is_push_limit_exceeded = True
            excess = push_chain[12]
            issues.append(f"推块链总数达到 {push_chain_count} 块，突破 12 方块上限！第 13 块方块位于 {excess}")

        is_healthy = len(issues) == 0 and not is_bud_locked

        if is_bud_locked:
            diag = "⚡ [BUD 锁定卡死] 活塞断电后未接收到邻域方块更新，保持伸出卡滞。"
            advice = "解决建议：在活塞正交相邻方块处放置或破坏任意方块产生方块更新，或给予一次红石线脉冲强制其复位缩回。"
        elif has_immovable_obstacle:
            diag = "⚡ [不可移动方块阻断] 推块路径上包含黑曜石、基岩或 Java 版不可推容器 (TileEntity)。"
            advice = "解决建议：移除阻碍的不可移动方块，或使用漏斗矿车/投掷器等代替实心阻挡。"
        elif is_push_limit_exceeded:
            diag = f"⚡ [推块上限超载] 推块链条包含 {push_chain_count} 块方块，超出 12 方块推力上限。"
            advice = "解决建议：使用釉面陶瓦隔断粘液块/蜜蜂块的横向粘连，或减少推击链条上的方块数量。"
        elif is_bud_pending:
            diag = "⚡ [BUD 待命状态] 活塞处于准连接 (QC) 充能状态，等待方块更新触发。"
            advice = "状态正常：若需要即时弹出，请在活塞旁引入红石脉冲或更新源；若用于方块更新检测器 (BUD)，已就绪。"
        elif is_directly_powered or is_qc_powered:
            diag = "✓ 活塞供电正常，推块链符合动力学规范。"
            advice = "保持当前布线即可。"
        else:
            diag = "✓ 活塞未充能，推块链处于安全休眠状态。"
            advice = "正常状态。通过红石粉或中继器输入信号即可激活。"

        return PistonReport(
            is_healthy=is_healthy,
            is_directly_powered=is_directly_powered,
            is_qc_powered=is_qc_powered,
            is_bud_locked=is_bud_locked,
            is_bud_pending=is_bud_pending,
            is_push_limit_exceeded=is_push_limit_exceeded,
            has_immovable_obstacle=has_immovable_obstacle,
            piston_pos=p_pos,
            piston_facing=facing,
            push_chain_count=push_chain_count,
            push_chain=push_chain,
            direct_power_sources=direct_power,
            qc_power_sources=qc_power,
            immovable_blocks=immovables,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=advice
        )


@dataclass
class ContainerSlotInfo:
    slot: int
    item_id: str
    count: int
    max_stack: int = 64


@dataclass
class ComparatorReport:
    is_healthy: bool
    is_subtract_mode: bool
    output_signal: int
    rear_signal: int
    side_signal: int
    is_sorter_slice: bool
    redstone_wire_length: int
    has_crosstalk_risk: bool
    has_unstackable_pollution: bool
    is_overflow_protected: bool
    comparator_pos: BlockPos
    container_pos: BlockPos
    container_type: str
    filled_item_count: int
    container_slot_capacity: int
    redstone_wire_chain: List[BlockPos]
    crosstalk_leak_targets: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    @classmethod
    def empty(cls) -> "ComparatorReport":
        return cls(
            is_healthy=True,
            is_subtract_mode=False,
            output_signal=0,
            rear_signal=0,
            side_signal=0,
            is_sorter_slice=False,
            redstone_wire_length=0,
            has_crosstalk_risk=False,
            has_unstackable_pollution=False,
            is_overflow_protected=True,
            comparator_pos=BlockPos(0, 0, 0),
            container_pos=BlockPos(0, 0, 0),
            container_type="none",
            filled_item_count=0,
            container_slot_capacity=0,
            redstone_wire_chain=[],
            crosstalk_leak_targets=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到红石比较器或容器组件",
            actionable_advice=""
        )

    def format_report(self) -> str:
        lines = [
            "§e【红石比较器与容器分类拓扑诊断报告】§r",
            f"▸ 目标比较器坐标：{self.comparator_pos} (模式: {'§c减法模式 (Subtract)§r' if self.is_subtract_mode else '§a比较模式 (Compare)§r'})",
            f"▸ 信号强度：输出 §6{self.output_signal}§r | 输入(后端): {self.rear_signal} | 侧边: {self.side_signal}"
        ]
        if self.container_type != "none":
            lines.append(f"▸ 绑测容器：{self.container_pos} ({self.container_type.upper()}) | 填充负载: {self.filled_item_count} 物品 (槽位: {self.container_slot_capacity})")

        if self.is_sorter_slice:
            lines.append(f"▸ 物品分类切片：红石线长 {self.redstone_wire_length} 格 | 架构: {'§a[安全防串扰 (3格线/41+1)]§r' if self.is_overflow_protected else '§c[高危串扰隐患 (短线/超载)]§r'}")

        if self.has_crosstalk_risk:
            lines.append("  ⚡ §c[高危串扰警报] 漏斗满溢或红石线过短，信号将横向泄漏至相邻切片导致漏光！§r")
            if self.crosstalk_leak_targets:
                lines.append(f"  ✖ 泄漏波及切片目标: {' '.join(str(p) for p in self.crosstalk_leak_targets)}")

        if self.has_unstackable_pollution:
            lines.append("  ✖ §c[槽位污染] 检测到不可堆叠/16堆叠物品误入滤波槽，致使信号异常激增！§r")

        if self.issues:
            lines.append("§c【发现问题】§r")
            for iss in self.issues:
                lines.append(f"  ✖ {iss}")

        if self.warnings:
            lines.append("§6【风险预警】§r")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")

        lines.append(f"▸ 诊断结论：{self.primary_diagnosis}")
        if self.actionable_advice:
            lines.append(f"▸ 优化建议：{self.actionable_advice}")
        return "\n".join(lines)


class ComparatorRedstoneAnalyzer:

    @staticmethod
    def calculate_container_signal(slot_count: int, items: List[ContainerSlotInfo]) -> int:
        if slot_count <= 0 or not items:
            return 0
        sum_filled_ratio = 0.0
        has_any_item = False
        for item in items:
            if item.count > 0:
                has_any_item = True
                max_stk = item.max_stack if item.max_stack > 0 else 64
                sum_filled_ratio += item.count / max_stk
        if not has_any_item:
            return 0
        raw = 1.0 + (sum_filled_ratio / float(slot_count)) * 14.0
        import math
        return min(15, max(1, math.floor(raw)))

    @staticmethod
    def calculate_simple_container_signal(slot_count: int, total_items: int, max_stack: int = 64) -> int:
        if slot_count <= 0 or total_items <= 0:
            return 0
        stk = max_stack if max_stack > 0 else 64
        items = []
        rem = total_items
        for i in range(slot_count):
            if rem <= 0:
                break
            take = min(stk, rem)
            items.append(ContainerSlotInfo(i, "item", take, stk))
            rem -= take
        return ComparatorRedstoneAnalyzer.calculate_container_signal(slot_count, items)

    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster], target_pos: Optional[BlockPos] = None) -> ComparatorReport:
        if not cluster or not cluster.blocks:
            return ComparatorReport.empty()

        comp = cluster.get_block(target_pos) if target_pos else None
        if not comp or not comp.is_comparator:
            for b in cluster.blocks.values():
                if b.is_comparator:
                    comp = b
                    target_pos = b.pos
                    break

        if not comp or not comp.is_comparator:
            return ComparatorReport.empty()

        facing = comp.get_property("facing", "north").lower()
        is_subtract = comp.get_property("mode", "compare").lower() == "subtract"

        def opposite_offset(pos: BlockPos, f: str) -> BlockPos:
            if f == "north": return pos.offset("south")
            if f == "south": return pos.offset("north")
            if f == "west": return pos.offset("east")
            if f == "east": return pos.offset("west")
            return pos.offset("south")

        def facing_offset(pos: BlockPos, f: str) -> BlockPos:
            if f == "north": return pos.offset("north")
            if f == "south": return pos.offset("south")
            if f == "west": return pos.offset("west")
            if f == "east": return pos.offset("east")
            return pos.offset("north")

        def side_offsets(pos: BlockPos, f: str) -> List[BlockPos]:
            if f in ("north", "south"):
                return [pos.offset("west"), pos.offset("east")]
            else:
                return [pos.offset("north"), pos.offset("south")]

        rear_pos = opposite_offset(target_pos, facing)
        rear_block = cluster.get_block(rear_pos)

        container_pos = rear_pos
        container_type = "none"
        slot_count = 0
        filled_item_count = 0
        has_unstackable = False
        rear_signal = 0

        def parse_container_type(bid: Optional[str]) -> str:
            if not bid: return "unknown"
            b = bid.lower()
            for k in ["hopper", "chest", "barrel", "shulker_box", "dispenser", "dropper", "crafter", "furnace", "brewing_stand"]:
                if k in b: return k
            return "container"

        def get_slot_capacity(ctype: str) -> int:
            if ctype in ("hopper", "brewing_stand"): return 5
            if ctype in ("chest", "barrel", "shulker_box"): return 27
            if ctype in ("dispenser", "dropper", "crafter"): return 9
            if ctype == "furnace": return 3
            return 27

        if rear_block and rear_block.is_container:
            container_type = parse_container_type(rear_block.block_id)
            slot_count = get_slot_capacity(container_type)
            items_prop = rear_block.get_property("items_count", "") or rear_block.get_property("items", "")
            has_unstackable = rear_block.get_property("has_unstackable", "false").lower() == "true"
            if items_prop:
                try:
                    filled_item_count = int(items_prop)
                except ValueError:
                    filled_item_count = 0
            else:
                filled_item_count = 45 if rear_block.is_powered else 0

            if has_unstackable:
                items = [ContainerSlotInfo(0, "potion", 1, 1)]
                rem = max(0, filled_item_count - 1)
                for s in range(1, slot_count):
                    take = min(64, rem)
                    items.append(ContainerSlotInfo(s, "filler", take, 64))
                    rem -= take
                rear_signal = ComparatorRedstoneAnalyzer.calculate_container_signal(slot_count, items)
            else:
                rear_signal = ComparatorRedstoneAnalyzer.calculate_simple_container_signal(slot_count, filled_item_count, 64)
        elif rear_block:
            try:
                rear_signal = int(rear_block.get_property("power", "0"))
            except ValueError:
                rear_signal = 15 if rear_block.is_powered else 0

        side_signal = 0
        for s_pos in side_offsets(target_pos, facing):
            s_block = cluster.get_block(s_pos)
            if s_block:
                try:
                    p = int(s_block.get_property("power", "0"))
                except ValueError:
                    p = 15 if s_block.is_powered else 0
                if p > side_signal:
                    side_signal = p

        if is_subtract:
            output_signal = max(0, rear_signal - side_signal)
        else:
            output_signal = rear_signal if rear_signal >= side_signal else 0

        front_pos = facing_offset(target_pos, facing)
        wire_chain = []
        cur = front_pos
        for _ in range(5):
            w = cluster.get_block(cur)
            if w and w.is_redstone_wire:
                wire_chain.append(cur)
                cur = facing_offset(cur, facing)
            else:
                break
        wire_length = len(wire_chain)

        is_sorter_slice = (rear_block is not None and rear_block.is_hopper) and (wire_length >= 2)
        has_crosstalk_risk = False
        is_overflow_protected = True
        crosstalk_leak_targets = []

        if is_sorter_slice:
            if wire_length == 2:
                is_overflow_protected = False
                if filled_item_count >= 46 or output_signal >= 3:
                    has_crosstalk_risk = True
                    for w_pos in wire_chain:
                        for side in side_offsets(w_pos, facing):
                            adj = cluster.get_block(side)
                            if adj and adj.is_redstone_wire:
                                crosstalk_leak_targets.append(side)
            elif wire_length >= 3:
                is_overflow_protected = True
                if output_signal >= 4:
                    has_crosstalk_risk = True

        issues = []
        warnings = []
        is_healthy = True

        if has_unstackable:
            is_healthy = False
            issues.append(f"滤波漏斗内混入不可堆叠物品，导致比较器信号暴增至 {output_signal}！")

        if has_crosstalk_risk:
            is_healthy = False
            issues.append(f"检测到红石串扰风险！当前信号强度 {output_signal} 在 {wire_length} 格红石线末端诱发横向泄漏，将毁损相邻分类切片！")
        elif not is_overflow_protected and is_sorter_slice:
            warnings.append(f"当前分类切片仅采用 {wire_length} 格红石线走线；若下方箱子满溢导致漏斗堆积超 45 件，将引发串扰！")

        if not is_healthy:
            if has_unstackable:
                diag = "不可堆叠物品槽位污染，破坏物品分类器信号标定"
                advice = "立即取出漏斗中的不可堆叠物品，换用重命名后的 64 堆叠方块作为滤波占位符。"
            else:
                diag = "分类机红石线过短或满溢超载，面临相邻切片串扰烧毁风险"
                advice = "建议将红石粉线路扩充至 3 格走线，并严格采用 41+1+1+1+1 物品布局，确保满溢时信号上限截断在 3 格以内。"
        elif is_sorter_slice:
            diag = "物品分类切片架构健全，具备防满溢串扰保护" if is_overflow_protected else "物品分类切片正常运行（注意防范后续满仓溢出）"
            advice = "当前 3 格红石走线与槽位配置安全，可支持紧凑密集切片并行排列。" if is_overflow_protected else "建议预留满仓停机熔断机制，或升级为标准 3 格红石线分类切片。"
        else:
            diag = f"红石比较器运行正常 (输出信号: {output_signal})"
            advice = "当前处于减法模式，可通过侧面信号动态衰减实现脉冲延长或高频时钟。" if is_subtract else "当前处于比较模式，输出等于或大于后端信号时如实透传。"

        return ComparatorReport(
            is_healthy=is_healthy,
            is_subtract_mode=is_subtract,
            output_signal=output_signal,
            rear_signal=rear_signal,
            side_signal=side_signal,
            is_sorter_slice=is_sorter_slice,
            redstone_wire_length=wire_length,
            has_crosstalk_risk=has_crosstalk_risk,
            has_unstackable_pollution=has_unstackable,
            is_overflow_protected=is_overflow_protected,
            comparator_pos=target_pos,
            container_pos=container_pos,
            container_type=container_type,
            filled_item_count=filled_item_count,
            container_slot_capacity=slot_count,
            redstone_wire_chain=wire_chain,
            crosstalk_leak_targets=crosstalk_leak_targets,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=advice
        )


@dataclass
class RedstoneTransmissionReport:
    is_healthy: bool
    has_torch_burnout: bool
    has_weak_power_blockade: bool
    has_wire_redirection_disconnection: bool
    has_observer_loop: bool
    target_pos: BlockPos
    target_block_type: str
    power_type: str  # STRONG, WEAK, TRANSPARENT_INSULATOR, NONE
    signal_strength: int
    burnout_torches: List[BlockPos]
    weak_power_blockades: List[BlockPos]
    redirected_wires: List[BlockPos]
    observer_loops: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    def format_report(self) -> str:
        sb = []
        sb.append("§e【红石传输拓扑与充能因果诊断报告】§r")
        sb.append(f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})")
        pt_zh = {
            "STRONG": "§a强充能 (Strongly Powered)§r",
            "WEAK": "§6弱充能 (Weakly Powered)§r",
            "TRANSPARENT_INSULATOR": "§c透明绝缘介质 (Non-conductive)§r",
            "NONE": "§7未充能 (Unpowered)§r"
        }.get(self.power_type, self.power_type)
        sb.append(f"▸ 充能状态：{pt_zh} | 信号强度: §6{self.signal_strength}§r")

        if self.has_torch_burnout:
            sb.append("  ⚡ §c[火把烧毁高危] 检测到红石火把极速自激振荡回路 (总延迟 < 4 ticks)！§r")
            for b in self.burnout_torches:
                sb.append(f"     ✖ 烧毁火把节点: {b} (3秒内切换>=8次触发熄灭冷却)")

        if self.has_weak_power_blockade:
            sb.append("  ⚡ §6[弱充能阻断告警] 实体方块仅为弱充能 (Weakly Powered)，无法熄灭火把或激活未指向的红石线！§r")
            for w in self.weak_power_blockades:
                sb.append(f"     ✖ 弱充能阻断点: {w} (需中继器升格为强充能)")

        if self.has_wire_redirection_disconnection:
            sb.append("  ⚡ §e[导线偏转断路] 红石粉因邻近组件吸引发生转向，脱离目标方块造成断电！§r")
            for r in self.redirected_wires:
                sb.append(f"     ↷ 偏转断路线路: {r}")

        if self.has_observer_loop:
            sb.append("  ⚡ §b[侦测器自激死循环] 检测到 1-clock (2 gameticks) 高频脉冲死循环振荡！§r")
            for o in self.observer_loops:
                sb.append(f"     ⟳ 侦测器振荡源: {o}")

        if self.is_healthy:
            sb.append("  ✓ §a[传输健康] 电路充能完整，无烧毁、弱充能阻断或偏转断路隐患。§r")

        sb.append(f"▸ 核心诊断：{self.primary_diagnosis}")
        if self.actionable_advice:
            sb.append(f"▸ 修复建议：{self.actionable_advice}")
        return "\n".join(sb)


class RedstoneTransmissionAnalyzer:
    @staticmethod
    def is_transparent(block: Optional[LocalBlock]) -> bool:
        if not block or block.is_air:
            return True
        bid = block.block_id.lower()
        transparent_keys = [
            "glass", "slab", "stairs", "glowstone", "leaves", "ice",
            "hopper", "chest", "fence", "wall", "piston", "door",
            "trapdoor", "wire", "torch", "repeater", "comparator"
        ]
        return any(k in bid for k in transparent_keys)

    @staticmethod
    def is_solid_conductive(block: Optional[LocalBlock]) -> bool:
        if not block or block.is_air or RedstoneTransmissionAnalyzer.is_transparent(block):
            return False
        bid = block.block_id.lower()
        non_conductive = ["redstone", "torch", "lever", "button", "pressure_plate"]
        return not any(k in bid for k in non_conductive)

    @staticmethod
    def is_wire_pointing_to(cluster: LocalMachineCluster, wire_pos: BlockPos, target_pos: BlockPos) -> bool:
        wire = cluster.get_block(wire_pos)
        if not wire or not wire.is_redstone_wire:
            return False

        dx = target_pos.x - wire_pos.x
        dy = target_pos.y - wire_pos.y
        dz = target_pos.z - wire_pos.z

        if dy != 0 or abs(dx) + abs(dz) != 1:
            return False

        direction = "east" if dx == 1 else "west" if dx == -1 else "south" if dz == 1 else "north"
        conn = wire.get_property(direction, "none")
        if conn != "none":
            return True

        if any(wire.get_property(d, "none") != "none" for d in ["north", "south", "east", "west"] if d != direction):
            return wire.get_property(direction, "none") != "none"

        return True

    @staticmethod
    def calculate_power_state(cluster: LocalMachineCluster, pos: BlockPos) -> tuple[str, int, List[BlockPos]]:
        block = cluster.get_block(pos)
        if not block or block.is_air:
            return "NONE", 0, []

        if RedstoneTransmissionAnalyzer.is_transparent(block):
            return "TRANSPARENT_INSULATOR", 0, []

        max_strong = 0
        max_weak = 0
        sources = []

        for n_pos in pos.neighbors():
            nb = cluster.get_block(n_pos)
            if not nb:
                continue

            # 1. Repeater pointing to pos
            if nb.is_repeater and nb.is_powered():
                if n_pos.offset(facing=nb.facing()) == pos:
                    max_strong = max(max_strong, 15)
                    sources.append(n_pos)

            # 2. Comparator pointing to pos
            if nb.is_comparator and nb.is_powered():
                if n_pos.offset(facing=nb.facing()) == pos:
                    p = int(nb.get_property("power", "15") or "15")
                    max_strong = max(max_strong, p)
                    sources.append(n_pos)

            # 3. Lever / Button
            if any(k in nb.block_id.lower() for k in ["lever", "button", "pressure_plate"]) and nb.is_powered():
                max_strong = max(max_strong, 15)
                sources.append(n_pos)

            # 4. Redstone block
            if "redstone_block" in nb.block_id.lower():
                max_strong = max(max_strong, 15)
                sources.append(n_pos)

            # 5. Redstone wire
            if nb.is_redstone_wire:
                wp = int(nb.get_property("power", "15" if nb.is_powered() else "0") or "0")
                if wp > 0:
                    if n_pos == pos.offset("up") or RedstoneTransmissionAnalyzer.is_wire_pointing_to(cluster, n_pos, pos):
                        max_weak = max(max_weak, wp)
                        sources.append(n_pos)

        if max_strong > 0:
            return "STRONG", max_strong, sources
        elif max_weak > 0:
            return "WEAK", max_weak, sources
        else:
            return "NONE", 0, sources

    @staticmethod
    def get_torch_base_pos(torch: LocalBlock) -> BlockPos:
        bid = torch.block_id.lower()
        facing = torch.facing()
        if "wall_torch" in bid:
            opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
            return torch.pos.offset(facing=opp.get(facing, "down"))
        return torch.pos.offset("down")

    @staticmethod
    def calculate_loop_delay(cluster: LocalMachineCluster, torch_pos: BlockPos, base_pos: BlockPos) -> int:
        from collections import deque
        queue = deque()
        delay_map = {}

        above = torch_pos.offset("up")
        queue.append(above)
        delay_map[above] = 1

        for n in torch_pos.neighbors():
            if n == torch_pos.offset("down"):
                continue
            nb = cluster.get_block(n)
            if nb and nb.is_redstone_wire:
                queue.append(n)
                delay_map[n] = 1

        visited = set()
        opp_facing = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}

        while queue:
            curr = queue.popleft()
            if curr == base_pos:
                return delay_map[curr]
            if curr in visited:
                continue
            visited.add(curr)

            curr_delay = delay_map[curr]
            for next_pos in curr.neighbors():
                if next_pos in visited or next_pos == torch_pos:
                    continue
                next_block = cluster.get_block(next_pos)
                if not next_block:
                    continue

                if next_pos == base_pos:
                    return curr_delay

                if next_block.is_redstone_wire:
                    if next_pos not in delay_map:
                        delay_map[next_pos] = curr_delay
                    queue.append(next_pos)
                elif next_block.is_repeater:
                    rf = next_block.facing()
                    if next_pos.offset(facing=opp_facing.get(rf, "north")) == curr:
                        r_delay = int(next_block.get_property("delay", "1") or "1")
                        if next_pos not in delay_map:
                            delay_map[next_pos] = curr_delay + r_delay
                        queue.append(next_pos.offset(facing=rf))
                elif RedstoneTransmissionAnalyzer.is_solid_conductive(next_block) and next_pos != base_pos:
                    if next_pos not in delay_map:
                        delay_map[next_pos] = curr_delay
                    queue.append(next_pos)

        return -1

    @classmethod
    def analyze(cls, cluster: Optional[LocalMachineCluster], target_pos: Optional[BlockPos] = None) -> RedstoneTransmissionReport:
        if not cluster or not cluster.blocks:
            return RedstoneTransmissionReport(
                is_healthy=True, has_torch_burnout=False, has_weak_power_blockade=False,
                has_wire_redirection_disconnection=False, has_observer_loop=False,
                target_pos=BlockPos(0, 0, 0), target_block_type="none", power_type="NONE",
                signal_strength=0, burnout_torches=[], weak_power_blockades=[],
                redirected_wires=[], observer_loops=[], issues=[], warnings=[],
                primary_diagnosis="未检测到红石传输或电路异常", actionable_advice=""
            )

        if not target_pos:
            target_pos = cluster.origin

        target_block = cluster.get_block(target_pos)
        target_type = target_block.block_id if target_block else "minecraft:air"

        power_type, signal_strength, _ = cls.calculate_power_state(cluster, target_pos)

        burnout_torches = []
        weak_power_blockades = []
        redirected_wires = []
        observer_loops = []
        issues = []
        warnings = []

        # 1. Detect torch burnout
        for block in cluster.blocks.values():
            if "redstone_torch" in block.block_id.lower():
                torch_pos = block.pos
                base_pos = cls.get_torch_base_pos(block)
                loop_delay = cls.calculate_loop_delay(cluster, torch_pos, base_pos)
                if 0 <= loop_delay < 4:
                    burnout_torches.append(torch_pos)
                    issues.append(f"红石火把 {torch_pos} 存在极速自激反馈回路（回路中继延迟: {loop_delay} ticks < 4 ticks），必将烧毁熄灭")

        # 2. Detect weak power blockades
        for neighbor in target_pos.neighbors():
            nb = cluster.get_block(neighbor)
            if nb and "redstone_torch" in nb.block_id.lower():
                base = cls.get_torch_base_pos(nb)
                if base == target_pos and power_type == "WEAK":
                    weak_power_blockades.append(target_pos)
                    issues.append(f"方块 {target_pos} 附着红石火把 {neighbor}，但该方块仅处于弱充能状态，红石火把无法熄灭！")

        for neighbor in target_pos.neighbors():
            nb = cluster.get_block(neighbor)
            if nb and nb.is_redstone_wire and power_type == "WEAK":
                if not cls.is_wire_pointing_to(cluster, neighbor, target_pos):
                    weak_power_blockades.append(target_pos)
                    issues.append(f"弱充能方块 {target_pos} 无法向相邻未对准的红石线 {neighbor} 传导信号")
                    break

        # 3. Detect wire redirection disconnection
        if target_block and not target_block.is_air:
            for neighbor in target_pos.neighbors():
                wire = cluster.get_block(neighbor)
                if wire and wire.is_redstone_wire:
                    wp = int(wire.get_property("power", "15" if wire.is_powered() else "0") or "0")
                    if wp > 0:
                        if not cls.is_wire_pointing_to(cluster, neighbor, target_pos) and neighbor != target_pos.offset("up"):
                            redirected_wires.append(neighbor)
                            warnings.append(f"红石线 {neighbor} 处于激活状态，但发生偏转脱离目标方块 {target_pos}，导致供电中断")

        # 4. Detect observer loops
        for block in cluster.blocks.values():
            if "observer" in block.block_id.lower():
                facing = block.facing()
                detected_pos = block.pos.offset(facing=facing)
                t_obs = cluster.get_block(detected_pos)
                if t_obs and "observer" in t_obs.block_id.lower():
                    if t_obs.pos.offset(facing=t_obs.facing()) == block.pos:
                        if block.pos not in observer_loops:
                            observer_loops.append(block.pos)
                            observer_loops.append(t_obs.pos)
                            warnings.append(f"侦测器 {block.pos} 与 {t_obs.pos} 面对面相对，构成 1-clock (2 gameticks) 自激震荡时钟")

        has_torch_burnout = len(burnout_torches) > 0
        has_weak_power = len(weak_power_blockades) > 0
        has_wire_redir = len(redirected_wires) > 0
        has_observer_loop = len(observer_loops) > 0
        is_healthy = not has_torch_burnout and not has_weak_power and not has_wire_redir and not has_observer_loop

        if has_torch_burnout:
            primary_diag = "检测到红石火把自激振荡反馈回路，回路延迟 < 4 ticks，火把将高频烧毁熄灭"
            advice = "在反馈回路中接入红石中继器（Repeater），将总延迟调至 4 redstone ticks（8 gameticks）以上消除烧毁"
        elif has_weak_power:
            primary_diag = "实体方块处于弱充能状态，无法灭活附着的红石火把或激活未指向的红石导线"
            advice = "改用红石中继器直接指向该方块，升格为强充能（Strongly Powered），以可靠熄灭火把"
        elif has_wire_redir:
            primary_diag = "红石粉受到邻近组件吸引产生偏转，不再对齐目标方块造成断路"
            advice = "在目标方块前放置中继器锁定单向注入，或在红石线侧面加装隔电方块防止偏转"
        elif has_observer_loop:
            primary_diag = "侦测器面对面或与活塞构成 1-clock (2 gameticks) 极限自激振荡"
            advice = "断开侦测器对冲，改用比较器时钟或拉开间距避免高频卡死"
        else:
            primary_diag = "红石传输链路与充能拓扑正常，无烧毁或阻断隐患"
            advice = "保持当前规范布线"

        return RedstoneTransmissionReport(
            is_healthy=is_healthy,
            has_torch_burnout=has_torch_burnout,
            has_weak_power_blockade=has_weak_power,
            has_wire_redirection_disconnection=has_wire_redir,
            has_observer_loop=has_observer_loop,
            target_pos=target_pos,
            target_block_type=target_type,
            power_type=power_type,
            signal_strength=signal_strength,
            burnout_torches=burnout_torches,
            weak_power_blockades=weak_power_blockades,
            redirected_wires=redirected_wires,
            observer_loops=observer_loops,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=primary_diag,
            actionable_advice=advice
        )


@dataclass
class RedstoneLogicReport:
    is_healthy: bool
    has_race_conflict: bool
    has_pulse_width_mismatch: bool
    has_bulb_lock: bool
    has_glitch_risk: bool
    target_pos: BlockPos
    target_block_type: str
    logic_type: str  # COPPER_BULB_T_FLIP_FLOP, RS_NOR_LATCH, STICKY_PISTON_T_FLIP_FLOP, MONOSTABLE_CIRCUIT, LOGIC_GATE, NONE
    gate_kind: str  # AND, OR, XOR, NOT, NONE
    output_state: bool
    signal_strength: int
    conflict_nodes: List[BlockPos]
    active_outputs: List[BlockPos]
    logic_components: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    def format_report(self) -> str:
        sb = []
        sb.append("§e【红石门电路、时序锁存器与铜球触发器因果诊断报告】§r")
        sb.append(f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})")
        lt_zh = {
            "COPPER_BULB_T_FLIP_FLOP": "§b1.21 铜球原生 T 触发器 (Copper Bulb T-Flip-Flop)§r",
            "RS_NOR_LATCH": "§aRS-NOR 保持锁存器 (Bi-stable Latch)§r",
            "STICKY_PISTON_T_FLIP_FLOP": "§3粘性活塞 1 刻吐方块 T 触发器 (Piston 1-Tick Spit)§r",
            "MONOSTABLE_CIRCUIT": "§6单稳态脉冲限制器 (Monostable Pulse Limiter)§r",
            "LOGIC_GATE": f"§d复合门电路 ({self.gate_kind} 门)§r",
            "NONE": "§7无特定门电路§r"
        }.get(self.logic_type, self.logic_type)
        out_zh = "§a[激活/高电平/ON]§r" if self.output_state else "§7[休眠/低电平/OFF]§r"
        sb.append(f"▸ 逻辑类型：{lt_zh} | 输出状态: {out_zh} (信号强度: §6{self.signal_strength}§r)")

        if self.has_race_conflict:
            sb.append("  ⚡ §c[锁存器竞争冲突] RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 冲突输入端: {c} (双端熄灭并在撤除信号时触发亚稳态自激)")

        if self.has_pulse_width_mismatch:
            sb.append("  ⚡ §e[脉宽不匹配失效] 粘性活塞 T 触发器输入脉冲 > 2 gameticks (检测到按钮或长持续供电)！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 超宽输入电源: {c} (活塞伸缩带回方块，无法脱离方块翻转)")

        if self.has_bulb_lock:
            sb.append("  ⚡ §6[铜球未复位锁定] 1.21 铜球处于持续充能状态 (powered=true)，无法响应后续脉冲！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 持续通电锁定点: {c} (需先断开信号恢复 powered=false)")

        if self.has_glitch_risk:
            sb.append("  ⚡ §e[门电路毛刺风险] 复合门多路输入存在延时差 (>=2 ticks)，切换瞬间可能激发出瞬态假脉冲！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ↷ 延时失配输入端: {c}")

        if self.is_healthy:
            sb.append("  ✓ §a[逻辑健康] 时序逻辑与门电路逻辑状态清晰，无竞争冒险、脉宽失配或锁死隐患。§r")

        sb.append(f"▸ 核心诊断：{self.primary_diagnosis}")
        if self.actionable_advice:
            sb.append(f"▸ 修复建议：{self.actionable_advice}")
        return "\n".join(sb)


class RedstoneLogicAnalyzer:
    @staticmethod
    def empty() -> RedstoneLogicReport:
        return RedstoneLogicReport(
            is_healthy=True,
            has_race_conflict=False,
            has_pulse_width_mismatch=False,
            has_bulb_lock=False,
            has_glitch_risk=False,
            target_pos=BlockPos(0, 0, 0),
            target_block_type="none",
            logic_type="NONE",
            gate_kind="NONE",
            output_state=False,
            signal_strength=0,
            conflict_nodes=[],
            active_outputs=[],
            logic_components=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到红石门电路、锁存器或触发器组件",
            actionable_advice=""
        )

    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster], target_pos: BlockPos) -> RedstoneLogicReport:
        if not cluster or cluster.is_empty:
            return RedstoneLogicAnalyzer.empty()

        target = cluster.get_block(target_pos)
        focus_pos = target_pos if (target and not target.is_air) else cluster.origin
        focus_block = cluster.get_block(focus_pos)

        # 1. Copper Bulb
        if focus_block and focus_block.is_copper_bulb:
            return RedstoneLogicAnalyzer._analyze_copper_bulb(cluster, focus_block)
        for b in cluster.get_connected_copper_bulbs():
            return RedstoneLogicAnalyzer._analyze_copper_bulb(cluster, b)

        # 2. RS-NOR Latch
        latch = RedstoneLogicAnalyzer._scan_rs_nor_latch(cluster, focus_pos)
        if latch:
            return latch

        # 3. Sticky Piston T-Flip-Flop
        if focus_block and focus_block.is_sticky_piston:
            return RedstoneLogicAnalyzer._analyze_piston_t_flip_flop(cluster, focus_block)
        for b in cluster.get_connected_pistons():
            if b.is_sticky_piston:
                return RedstoneLogicAnalyzer._analyze_piston_t_flip_flop(cluster, b)

        # 4. Monostable
        mono = RedstoneLogicAnalyzer._scan_monostable(cluster, focus_pos)
        if mono:
            return mono

        # 5. Logic Gate
        gate = RedstoneLogicAnalyzer._scan_logic_gate(cluster, focus_pos)
        if gate:
            return gate

        return RedstoneLogicAnalyzer.empty()

    @staticmethod
    def _analyze_copper_bulb(cluster: LocalMachineCluster, bulb: LocalBlock) -> RedstoneLogicReport:
        pos = bulb.pos
        is_lit = bulb.is_copper_bulb_lit
        is_powered = bulb.is_powered()

        conflict_nodes = []
        active_outputs = [pos] if is_lit else []
        components = [pos]
        issues = []
        warnings = []

        has_bulb_lock = False
        has_loop_oscillation = False

        if is_powered:
            has_bulb_lock = True
            conflict_nodes.append(pos)
            issues.append("铜球当前处于持续充能状态 (powered=true)，若无断电过程无法响应后续红石脉冲切换 lit 状态！")

        for n_pos in pos.neighbors():
            nb = cluster.get_block(n_pos)
            if nb and nb.is_comparator:
                components.append(n_pos)
                cFacing = nb.facing()
                # Comparator reading from bulb
                if n_pos.offset(facing=cFacing) == pos or n_pos.offset(facing=RedstoneLogicAnalyzer._reverse_facing(cFacing)) == pos:
                    comp_out = n_pos.offset(facing=cFacing)
                    if comp_out == pos or pos in comp_out.neighbors():
                        has_loop_oscillation = True
                        conflict_nodes.append(n_pos)
                        issues.append("检测到铜球经由比较器直连自反馈回路，将引发 1-gt 极限高频啸叫振荡！")

        is_healthy = not has_bulb_lock and not has_loop_oscillation
        if has_loop_oscillation:
            diag = "铜球与比较器构成无延时自反馈闭环，将诱发 1-gametick 极限高频啸叫自激！"
            advice = "在比较器输出端接入红石中继器或断开直连反馈，避免服务器卡顿。"
        elif has_bulb_lock:
            diag = "1.21 铜球处于持续充能锁定状态 (powered=true)，后续红石脉冲将失效。"
            advice = "断开持续供电信号（如将拉杆切为按钮，或确保前置信号能及时断电归零）。"
        else:
            diag = f"1.21 原生铜球 T 触发器状态正常 (lit={is_lit}, powered={is_powered})，具 1-gt 奇数刻极速延迟"
            advice = "可后接红石比较器无损读取 15 级高信噪满信号，或用于奇数刻超紧凑时钟。"

        return RedstoneLogicReport(
            is_healthy=is_healthy,
            has_race_conflict=False,
            has_pulse_width_mismatch=False,
            has_bulb_lock=has_bulb_lock or has_loop_oscillation,
            has_glitch_risk=False,
            target_pos=pos,
            target_block_type=bulb.block_id,
            logic_type="COPPER_BULB_T_FLIP_FLOP",
            gate_kind="NONE",
            output_state=is_lit,
            signal_strength=15 if is_lit else 0,
            conflict_nodes=conflict_nodes,
            active_outputs=active_outputs,
            logic_components=components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=advice
        )

    @staticmethod
    def _scan_rs_nor_latch(cluster: LocalMachineCluster, focus_pos: BlockPos) -> Optional[RedstoneLogicReport]:
        torches = [b for b in cluster.blocks.values() if b.is_redstone_torch]
        if len(torches) < 2:
            target = cluster.get_block(focus_pos)
            if target and (target.get_property("latch", "false").lower() == "true" or target.get_property("circuit", "").lower() == "rs_nor"):
                return RedstoneLogicAnalyzer._eval_explicit_latch(cluster, target)
            return None

        for i in range(len(torches)):
            for j in range(i + 1, len(torches)):
                tA = torches[i]
                tB = torches[j]
                dist = abs(tA.pos.x - tB.pos.x) + abs(tA.pos.y - tB.pos.y) + abs(tA.pos.z - tB.pos.z)
                if dist <= 5:
                    return RedstoneLogicAnalyzer._eval_rs_nor_pair(cluster, tA, tB)

        target = cluster.get_block(focus_pos)
        if target and (target.get_property("latch", "false").lower() == "true" or target.get_property("circuit", "").lower() == "rs_nor"):
            return RedstoneLogicAnalyzer._eval_explicit_latch(cluster, target)
        return None

    @staticmethod
    def _eval_rs_nor_pair(cluster: LocalMachineCluster, tA: LocalBlock, tB: LocalBlock) -> RedstoneLogicReport:
        posA = tA.pos
        posB = tB.pos
        litA = tA.get_property("lit", "true").lower() != "false"
        litB = tB.get_property("lit", "false").lower() != "false"

        s_active = tA.get_property("set", "false").lower() == "true"
        r_active = tB.get_property("reset", "false").lower() == "true"

        for n in posA.neighbors():
            nb = cluster.get_block(n)
            if nb and (nb.is_button or nb.is_lever) and nb.is_powered():
                s_active = True
        for n in posB.neighbors():
            nb = cluster.get_block(n)
            if nb and (nb.is_button or nb.is_lever) and nb.is_powered():
                r_active = True

        has_race = s_active and r_active
        conflict_nodes = [posA, posB] if has_race else []
        issues = ["RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！两路输出均被强行熄灭，撤除时引发亚稳态竞争自激！"] if has_race else []

        active_outputs = []
        if litA: active_outputs.append(posA)
        if litB: active_outputs.append(posB)

        q_state = litB or (not litA and not r_active)

        diag = "RS-NOR 保持锁存器检测到非法竞争状态 (S=1 & R=1)，两路火把熄灭，存在竞争冒险高危" if has_race else f"RS-NOR 保持锁存器工作正常 [Q={1 if q_state else 0}, Q_BAR={0 if q_state else 1}] (S={s_active}, R={r_active})"
        advice = "在 Set 与 Reset 输入端增加前置互锁逻辑或双向仲裁电路，禁止双侧同时触发。" if has_race else "保持 Set 与 Reset 互斥脉冲输入，避免同时通电。"

        return RedstoneLogicReport(
            is_healthy=not has_race,
            has_race_conflict=has_race,
            has_pulse_width_mismatch=False,
            has_bulb_lock=False,
            has_glitch_risk=False,
            target_pos=posB,
            target_block_type="minecraft:redstone_torch",
            logic_type="RS_NOR_LATCH",
            gate_kind="NONE",
            output_state=q_state,
            signal_strength=15 if q_state else 0,
            conflict_nodes=conflict_nodes,
            active_outputs=active_outputs,
            logic_components=[posA, posB],
            issues=issues,
            warnings=[],
            primary_diagnosis=diag,
            actionable_advice=advice
        )

    @staticmethod
    def _eval_explicit_latch(cluster: LocalMachineCluster, target: LocalBlock) -> RedstoneLogicReport:
        s_active = target.get_property("set", "false").lower() == "true"
        r_active = target.get_property("reset", "false").lower() == "true"
        has_race = s_active and r_active

        q = s_active or (not r_active and target.get_property("q", "true").lower() != "false")
        conflict_nodes = [target.pos] if has_race else []
        issues = ["RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！"] if has_race else []

        return RedstoneLogicReport(
            is_healthy=not has_race,
            has_race_conflict=has_race,
            has_pulse_width_mismatch=False,
            has_bulb_lock=False,
            has_glitch_risk=False,
            target_pos=target.pos,
            target_block_type=target.block_id,
            logic_type="RS_NOR_LATCH",
            gate_kind="NONE",
            output_state=q,
            signal_strength=15 if q else 0,
            conflict_nodes=conflict_nodes,
            active_outputs=[target.pos] if (q and not has_race) else [],
            logic_components=[target.pos],
            issues=issues,
            warnings=[],
            primary_diagnosis="RS-NOR 保持锁存器检测到非法输入冲突 (S=1 & R=1)" if has_race else "RS-NOR 保持锁存器工作正常",
            actionable_advice="增加前置互锁电路禁止双端同时通电" if has_race else "保持当前输入分离"
        )

    @staticmethod
    def _analyze_piston_t_flip_flop(cluster: LocalMachineCluster, piston: LocalBlock) -> RedstoneLogicReport:
        pos = piston.pos
        facing = piston.facing()
        spit_pos = pos.offset(facing=facing)

        has_mono = piston.get_property("has_monostable", "false").lower() == "true"
        pulse_width = int(piston.get_property("pulse_width", "0"))
        has_button = False
        source_pos = None

        for n in pos.neighbors():
            nb = cluster.get_block(n)
            if not nb: continue
            if nb.is_button:
                has_button = True
                source_pos = n
                if pulse_width == 0:
                    pulse_width = 30 if "wood" in nb.block_id.lower() else 20
            elif nb.is_lever and nb.is_powered():
                has_button = True
                source_pos = n
                if pulse_width == 0: pulse_width = 100
            elif nb.is_repeater:
                d = int(nb.get_property("delay", "1"))
                if d >= 2 and pulse_width == 0:
                    pulse_width = d * 2

        has_mismatch = not has_mono and (pulse_width > 2 or has_button)
        conflict_nodes = []
        issues = []
        if has_mismatch:
            conflict_nodes.append(pos)
            if source_pos: conflict_nodes.append(source_pos)
            issues.append(f"粘性活塞 T 触发器输入脉冲宽度为 {pulse_width} gameticks (> 2 gt)！活塞伸缩后将吸回方块，无法脱离方块翻转！")

        is_ext = piston.is_extended or piston.get_property("spit_out", "false").lower() == "true"
        active_outputs = [spit_pos] if is_ext else []

        diag = f"粘性活塞 T 触发器输入脉宽过长 ({pulse_width} gt > 2 gt)，活塞拉回方块无法吐出" if has_mismatch else "粘性活塞 1 刻吐方块 T 触发器工作正常 (脉冲 <= 2 gt 瞬间脱离)"
        advice = "在输入端前置接入单稳态电路（如普通活塞切线单稳态或双路反相延时器），将脉宽精确裁剪至 <= 2 gameticks (1 redstone tick)。" if has_mismatch else "保持超短脉冲输入以维持可靠双稳态切换。"

        return RedstoneLogicReport(
            is_healthy=not has_mismatch,
            has_race_conflict=False,
            has_pulse_width_mismatch=has_mismatch,
            has_bulb_lock=False,
            has_glitch_risk=False,
            target_pos=pos,
            target_block_type=piston.block_id,
            logic_type="STICKY_PISTON_T_FLIP_FLOP",
            gate_kind="NONE",
            output_state=is_ext,
            signal_strength=15 if is_ext else 0,
            conflict_nodes=conflict_nodes,
            active_outputs=active_outputs,
            logic_components=[pos],
            issues=issues,
            warnings=[],
            primary_diagnosis=diag,
            actionable_advice=advice
        )

    @staticmethod
    def _scan_monostable(cluster: LocalMachineCluster, focus_pos: BlockPos) -> Optional[RedstoneLogicReport]:
        target = cluster.get_block(focus_pos)
        if target and (target.get_property("monostable", "false").lower() == "true" or target.get_property("circuit", "").lower() == "monostable"):
            powered = target.is_powered()
            return RedstoneLogicReport(
                is_healthy=True,
                has_race_conflict=False,
                has_pulse_width_mismatch=False,
                has_bulb_lock=False,
                has_glitch_risk=False,
                target_pos=target.pos,
                target_block_type=target.block_id,
                logic_type="MONOSTABLE_CIRCUIT",
                gate_kind="NONE",
                output_state=powered,
                signal_strength=15 if powered else 0,
                conflict_nodes=[],
                active_outputs=[target.pos] if powered else [],
                logic_components=[target.pos],
                issues=[],
                warnings=[],
                primary_diagnosis="单稳态脉冲限制器工作正常，输出 1 redstone tick (2 gt) 极短脉冲",
                actionable_advice="可用于粘性活塞吐方块、计数器或发射器点射"
            )
        return None

    @staticmethod
    def _scan_logic_gate(cluster: LocalMachineCluster, focus_pos: BlockPos) -> Optional[RedstoneLogicReport]:
        target = cluster.get_block(focus_pos)
        if not target: return None

        circ = target.get_property("circuit", "").lower()
        gate = target.get_property("gate", "").lower()

        kind = "NONE"
        if "and" in circ or "and" in gate: kind = "AND"
        elif "xor" in circ or "xor" in gate: kind = "XOR"
        elif "or" in circ or "or" in gate: kind = "OR"

        if kind == "NONE": return None

        in_a = target.get_property("input_a", "false").lower() == "true"
        in_b = target.get_property("input_b", "false").lower() == "true"
        delay_a = int(target.get_property("delay_a", "0"))
        delay_b = int(target.get_property("delay_b", "0"))

        has_glitch = abs(delay_a - delay_b) >= 2

        out = False
        if kind == "AND": out = in_a and in_b
        elif kind == "OR": out = in_a or in_b
        elif kind == "XOR": out = in_a != in_b

        diag = f"复合门电路 ({kind} 门) 输入延迟不对齐 (差值 {abs(delay_a - delay_b)} ticks)，存在毛刺冒险" if has_glitch else f"复合门电路 ({kind} 门) 逻辑运算正常 [A={in_a}, B={in_b} -> OUT={out}]"
        advice = "在延迟较短的输入通路上串联中继器平衡时间，避免瞬态毛刺误触下级机械。" if has_glitch else "逻辑信号对称，保持当前布线。"

        return RedstoneLogicReport(
            is_healthy=not has_glitch,
            has_race_conflict=False,
            has_pulse_width_mismatch=False,
            has_bulb_lock=False,
            has_glitch_risk=has_glitch,
            target_pos=target.pos,
            target_block_type=target.block_id,
            logic_type="LOGIC_GATE",
            gate_kind=kind,
            output_state=out,
            signal_strength=15 if out else 0,
            conflict_nodes=[target.pos] if has_glitch else [],
            active_outputs=[target.pos] if out else [],
            logic_components=[target.pos],
            issues=[],
            warnings=[f"门电路双路输入延时差为 {abs(delay_a - delay_b)} ticks (>= 2 ticks)！"] if has_glitch else [],
            primary_diagnosis=diag,
            actionable_advice=advice
        )

    @staticmethod
    def _reverse_facing(facing: str) -> str:
        f = facing.lower()
        return {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down"}.get(f, "up")


@dataclass
class RailReport:
    is_healthy: bool
    has_slope_stall_risk: bool
    has_missing_backstop: bool
    has_activator_lockout: bool
    has_unloader_glitch_risk: bool
    has_underpowered_launch: bool
    target_pos: BlockPos
    target_block_type: str
    rail_type: str  # UNLOADER_STATION, LOADER_STATION, SLOPED_ASCENT, CRUISING_LINE, ACTIVATOR_SECTION, NONE
    rail_count: int
    powered_rail_count: int
    conflict_nodes: List[BlockPos]
    ghost_block_placements: List[BlockPos]
    rail_components: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    def format_report(self) -> str:
        sb = []
        sb.append("§e【矿车铁轨网络、坡道动量与智能装卸站因果诊断报告】§r")
        sb.append(f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})")
        sb.append(f"▸ 轨道类型：{self._format_rail_type()} | 铁轨总数: {self.rail_count} (充能铁轨: §6{self.powered_rail_count}§r)")
        if self.has_missing_backstop:
            sb.append("  ⚡ §c[终端缺失坚固挡板] 卸货站充能铁轨后方未检测到坚固实体方块！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 悬空/无依托站台: {c} (静止矿车无法凭空起步，通电后原地卡死)")
            for g in self.ghost_block_placements:
                sb.append(f"     ➕ 建议补全实体方块位置: {g}")
        if self.has_slope_stall_risk:
            sb.append("  ⚡ §e[坡道动量不足/倒溜高危] 斜坡铁轨检测到连续 ≥2 格普通铁轨！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 爬坡动力赤字段: {c} (重力衰减导致动量耗尽，矿车将倒溜卡死)")
        if self.has_activator_lockout:
            sb.append("  ⚡ §c[激活铁轨停用锁死] 检测到通电激活铁轨 (Activator Rail) 接入货运线路！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 锁定禁用节点: {c} (漏斗矿车压过将被锁定停用，停止吸取掉落物)")
        if self.has_unloader_glitch_risk:
            sb.append("  ⚡ §6[卸货站提前发车隐患] 比较器直连反相火把，缺失双比较器脉冲延长器 (Pulse Extender)！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ↷ 无滤波检测端: {c} (8-tick 物品抽取间歇可能导致信号瞬断提前弹走矿车)")
        if self.has_underpowered_launch:
            sb.append("  ⚡ §e[起步冲力不足] 站台起步段仅铺设 1 根充能铁轨，出站速度不足 2.4 m/s (极速仅 30%)！§r")
        if self.is_healthy:
            sb.append("  ✓ §a[铁轨健康] 铁轨间距合理，站台挡板完备，卸货滤波与动力坡道配置健康无倒溜隐患。§r")
        sb.append(f"▸ 核心诊断：{self.primary_diagnosis}")
        if self.actionable_advice:
            sb.append(f"▸ 修复建议：{self.actionable_advice}")
        return "\n".join(sb)

    def _format_rail_type(self) -> str:
        types = {
            "UNLOADER_STATION": "§b智能漏斗矿车卸货站 (Smart Unloader Station)§r",
            "LOADER_STATION": "§a智能矿车装货站 (Smart Loader Station)§r",
            "SLOPED_ASCENT": "§e斜坡爬坡动力段 (Sloped Rail Ascent)§r",
            "CRUISING_LINE": "§3平地极速巡航干线 (Cruising Rail Line)§r",
            "ACTIVATOR_SECTION": "§d激活铁轨功能段 (Activator Functional Rail)§r",
            "NONE": "§7常规铁轨轨道§r",
        }
        return types.get(self.rail_type, "§7常规铁轨轨道§r")


class RailNetworkAnalyzer:
    @staticmethod
    def empty() -> RailReport:
        return RailReport(
            is_healthy=True,
            has_slope_stall_risk=False,
            has_missing_backstop=False,
            has_activator_lockout=False,
            has_unloader_glitch_risk=False,
            has_underpowered_launch=False,
            target_pos=BlockPos(0, 0, 0),
            target_block_type="none",
            rail_type="NONE",
            rail_count=0,
            powered_rail_count=0,
            conflict_nodes=[],
            ghost_block_placements=[],
            rail_components=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到铁轨、矿车站台或物流轨道网络组件",
            actionable_advice=""
        )

    @staticmethod
    def analyze(cluster: Optional[LocalMachineCluster], target_pos: BlockPos) -> RailReport:
        if not cluster or cluster.is_empty:
            return RailNetworkAnalyzer.empty()

        rails = cluster.get_connected_rails()
        if not rails:
            target = cluster.get_block(target_pos)
            if target and target.is_hopper:
                above = cluster.get_block(target_pos.offset("up"))
                if above and above.is_rail:
                    rails = [above]

        if not rails:
            return RailNetworkAnalyzer.empty()

        target_block = cluster.get_block(target_pos)
        focus_pos = target_pos if (target_block and not target_block.is_air) else cluster.origin

        # 1. Unloader station (rail over hopper)
        for r in rails:
            down_pos = r.pos.offset("down")
            below = cluster.get_block(down_pos)
            if below and below.is_hopper:
                return RailNetworkAnalyzer._analyze_unloader_station(cluster, r, below, rails)

        # 2. Activator rail
        for r in rails:
            if r.is_activator_rail:
                return RailNetworkAnalyzer._analyze_activator_rail(cluster, r, rails)

        # 3. Sloped ascent
        has_slope = False
        for r in rails:
            if r.is_ascending_rail:
                has_slope = True
                break
            for r2 in rails:
                if r.pos != r2.pos and abs(r.pos.y - r2.pos.y) == 1:
                    dist = abs(r.pos.x - r2.pos.x) + abs(r.pos.z - r2.pos.z)
                    if dist == 1:
                        has_slope = True
                        break
            if has_slope:
                break

        if has_slope:
            return RailNetworkAnalyzer._analyze_sloped_ascent(cluster, focus_pos, rails)

        # 4. Cruising line
        return RailNetworkAnalyzer._analyze_cruising_line(cluster, focus_pos, rails)

    @staticmethod
    def _analyze_unloader_station(cluster: LocalMachineCluster, unloader_rail: LocalBlock, hopper: LocalBlock, all_rails: List[LocalBlock]) -> RailReport:
        rail_pos = unloader_rail.pos
        hopper_pos = hopper.pos

        conflict_nodes = []
        ghost_blocks = []
        rail_components = [r.pos for r in all_rails] + [hopper_pos]
        issues = []
        warnings = []

        directions = ["north", "south", "east", "west"]
        track_direction = None
        for d in directions:
            nb = cluster.get_block(rail_pos.offset(d))
            if nb and nb.is_rail:
                track_direction = d
                break

        rev = {"north": "south", "south": "north", "east": "west", "west": "east"}
        backstop_pos = rail_pos.offset(rev.get(track_direction, "south"))

        backstop_block = cluster.get_block(backstop_pos)
        has_missing_backstop = not backstop_block or not backstop_block.is_solid_conductive_block
        if has_missing_backstop:
            conflict_nodes.append(rail_pos)
            ghost_blocks.append(backstop_pos)
            issues.append("卸货站终端充能铁轨后方未检测到坚固实体方块！静止矿车无法凭空起动，通电后将卡死在站台！")

        # Check comparator & pulse extender
        comparator_block = None
        for d in directions:
            c = cluster.get_block(hopper_pos.offset(d))
            if c and c.is_comparator:
                comparator_block = c
                rail_components.append(c.pos)
                break

        has_unloader_glitch = False
        if comparator_block:
            has_pulse_extender = False
            comp_out = comparator_block.pos.offset(comparator_block.facing())
            out_block = cluster.get_block(comp_out)
            if out_block:
                rail_components.append(comp_out)
                if out_block.is_repeater and int(out_block.get_property("delay", "1")) >= 3:
                    has_pulse_extender = True
                elif out_block.is_comparator:
                    has_pulse_extender = True

            if not has_pulse_extender:
                has_unloader_glitch = True
                conflict_nodes.append(comparator_block.pos)
                warnings.append("卸货站比较器直连反相控制端，未接入双比较器脉冲延长器 (Pulse Extender)；漏斗抽取物品交接的 8-tick 间歇可能诱发信号瞬断提前发车！")

        powered_count = sum(1 for r in all_rails if r.is_powered_rail)
        has_underpowered = (powered_count == 1 and len(all_rails) > 1)
        if has_underpowered:
            warnings.append("起步加速段仅铺设 1 根充能铁轨，出站速度不足 2.4 m/s (仅为极速 30%)，长距离巡航极易中途停滞。")

        is_healthy = not has_missing_backstop and not has_unloader_glitch and not has_underpowered
        diag = "卸货站终端缺失实体挡板，静止矿车无法形成反弹动力起步卡死。" if has_missing_backstop else (
            "卸货站比较器缺失脉冲延长器延时滤波，存在抽料瞬隙提前发车隐患。" if has_unloader_glitch else (
                "起步段充能铁轨不足，矿车出站初速度较低。" if has_underpowered else "智能卸货站结构完备，实体挡板存在且动力控制稳定。"
            )
        )
        adv = "在终端充能铁轨后方紧贴放置一个实体方块（如石头、深板岩）作为反弹挡板。" if has_missing_backstop else (
            "在比较器与反相火把之间串入双比较器脉冲延长器（8~12 ticks 滤波缓冲），杜绝提前发车。" if has_unloader_glitch else (
                "在出站起步前 3~4 格连续铺设充能铁轨，使矿车在最短距离内提速至 8.0 m/s 极速。" if has_underpowered else "保持当前配置，确保下方箱子容量充足。"
            )
        )

        return RailReport(
            is_healthy=is_healthy,
            has_slope_stall_risk=False,
            has_missing_backstop=has_missing_backstop,
            has_activator_lockout=False,
            has_unloader_glitch_risk=has_unloader_glitch,
            has_underpowered_launch=has_underpowered,
            target_pos=rail_pos,
            target_block_type=unloader_rail.block_id,
            rail_type="UNLOADER_STATION",
            rail_count=len(all_rails),
            powered_rail_count=powered_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=ghost_blocks,
            rail_components=rail_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )

    @staticmethod
    def _analyze_sloped_ascent(cluster: LocalMachineCluster, target_pos: BlockPos, all_rails: List[LocalBlock]) -> RailReport:
        conflict_nodes = []
        rail_components = [r.pos for r in all_rails]
        issues = []
        warnings = []

        sorted_rails = sorted(all_rails, key=lambda b: (b.pos.y, b.pos.x, b.pos.z))
        powered_count = 0
        max_consecutive = 0
        cur_consecutive = 0
        consecutive_pos = []
        longest_chain = []

        for r in sorted_rails:
            if r.is_powered_rail:
                powered_count += 1
                if cur_consecutive > max_consecutive:
                    max_consecutive = cur_consecutive
                    longest_chain = list(consecutive_pos)
                cur_consecutive = 0
                consecutive_pos.clear()
            else:
                cur_consecutive += 1
                consecutive_pos.append(r.pos)

        if cur_consecutive > max_consecutive:
            max_consecutive = cur_consecutive
            longest_chain = list(consecutive_pos)

        has_slope_stall = max_consecutive >= 2
        if has_slope_stall:
            conflict_nodes.extend(longest_chain)
            issues.append(f"斜坡爬坡段连续出现 {max_consecutive} 格普通铁轨 (≥2)！矿车克服重力爬坡时动量急剧衰减，必定在半坡发生重力倒溜卡死 (Rollback Stall)！")

        is_healthy = not has_slope_stall
        diag = "斜坡铁轨充能间隔过大 (连续普通铁轨≥2)，上行矿车动量耗尽发生重力倒溜。" if has_slope_stall else "斜坡动力充沛，充能铁轨间隔符合安全爬坡规范 (≤1格普通铁轨)。"
        adv = "斜坡上充能铁轨间距严禁超过 2 格，请至少按“1 充能 + 1 普通”交替铺设；重载建议 1:1 全铺充能铁轨。" if has_slope_stall else "保持当前坡道动力配置。"

        return RailReport(
            is_healthy=is_healthy,
            has_slope_stall_risk=has_slope_stall,
            has_missing_backstop=False,
            has_activator_lockout=False,
            has_unloader_glitch_risk=False,
            has_underpowered_launch=False,
            target_pos=target_pos,
            target_block_type=sorted_rails[0].block_id,
            rail_type="SLOPED_ASCENT",
            rail_count=len(all_rails),
            powered_rail_count=powered_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=[],
            rail_components=rail_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )

    @staticmethod
    def _analyze_activator_rail(cluster: LocalMachineCluster, activator_rail: LocalBlock, all_rails: List[LocalBlock]) -> RailReport:
        act_pos = activator_rail.pos
        conflict_nodes = []
        rail_components = [r.pos for r in all_rails]
        issues = []
        warnings = []

        is_powered = activator_rail.is_powered() or activator_rail.is_redstone_power_source
        if not is_powered:
            for nb_pos in act_pos.neighbors:
                nb = cluster.get_block(nb_pos)
                if nb and nb.is_redstone_power_source:
                    is_powered = True
                    break

        has_activator_lockout = is_powered
        if has_activator_lockout:
            conflict_nodes.append(act_pos)
            issues.append("检测到通电激活铁轨 (Activator Rail) 接入轨道！漏斗矿车压过通电激活铁轨会被强行锁定停用 (disabled)，停止吸取所有掉落物！")

        powered_count = sum(1 for r in all_rails if r.is_powered_rail)
        is_healthy = not has_activator_lockout
        diag = "通电激活铁轨导致漏斗矿车被强行锁定，货运收集功能瘫痪。" if has_activator_lockout else "激活铁轨处于未通电休眠状态。"
        adv = "若为物资收集线，请将激活铁轨更换为充能铁轨 (Powered Rail)；激活铁轨仅用于弹射生物或引爆 TNT 矿车。" if has_activator_lockout else "若需弹射乘骑生物或引爆 TNT 矿车，请接入红石信号激活。"

        return RailReport(
            is_healthy=is_healthy,
            has_slope_stall_risk=False,
            has_missing_backstop=False,
            has_activator_lockout=has_activator_lockout,
            has_unloader_glitch_risk=False,
            has_underpowered_launch=False,
            target_pos=act_pos,
            target_block_type=activator_rail.block_id,
            rail_type="ACTIVATOR_SECTION",
            rail_count=len(all_rails),
            powered_rail_count=powered_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=[],
            rail_components=rail_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )

    @staticmethod
    def _analyze_cruising_line(cluster: LocalMachineCluster, target_pos: BlockPos, all_rails: List[LocalBlock]) -> RailReport:
        conflict_nodes = []
        rail_components = [r.pos for r in all_rails]
        issues = []
        warnings = []

        powered_count = sum(1 for r in all_rails if r.is_powered_rail)
        normal_count = sum(1 for r in all_rails if r.is_normal_rail)
        has_underpowered = normal_count > 38 and powered_count == 0
        if has_underpowered:
            warnings.append(f"平地巡航段连续普通铁轨达 {normal_count} 格 (>38 格)！矿车动量严重衰减，无法维持 8.0 m/s 极速巡航。")

        is_healthy = not has_underpowered
        diag = "平地巡航普通铁轨超过 38 格阈值，矿车速度明显跌落。" if has_underpowered else "平地巡航铁轨配置健康，动量巡航正常。"
        adv = "平地建议每 34~38 格铺设 1 根充能铁轨以维持矿车最高限速 (8.0 m/s)。" if has_underpowered else "保持当前轨道配置。"

        return RailReport(
            is_healthy=is_healthy,
            has_slope_stall_risk=False,
            has_missing_backstop=False,
            has_activator_lockout=False,
            has_unloader_glitch_risk=False,
            has_underpowered_launch=has_underpowered,
            target_pos=target_pos,
            target_block_type=all_rails[0].block_id,
            rail_type="CRUISING_LINE",
            rail_count=len(all_rails),
            powered_rail_count=powered_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=[],
            rail_components=rail_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )

@dataclass
class WaterReport:
    is_healthy: bool
    has_broken_bubble_column: bool
    has_top_spill_risk: bool
    has_flow_stall_risk: bool
    has_misaligned_stream: bool
    has_despawn_vortex_risk: bool
    target_pos: BlockPos
    target_block_type: str
    logistics_type: str
    water_block_count: int
    ice_block_count: int
    conflict_nodes: List[BlockPos] = field(default_factory=list)
    ghost_block_placements: List[BlockPos] = field(default_factory=list)
    water_components: List[BlockPos] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    primary_diagnosis: str = ""
    actionable_advice: str = ""

    def format_report(self) -> str:
        sb = []
        sb.append("§b【水流传输网络、气泡柱动力学与物品对齐因果诊断报告】§r")
        sb.append(f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})")
        sb.append(f"▸ 物流类型：{self.logistics_type} | 水体单元数: {self.water_block_count} (冰道方块: §b{self.ice_block_count}§r)")

        if self.has_broken_bubble_column:
            sb.append("  ⚡ §c[气泡柱中断卡死] 灵魂沙垂直水柱中检测到流动水！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 流动水断点: {c} (非全源水导致浮力消失，掉落物卡死)")
            for g in self.ghost_block_placements:
                sb.append(f"     ➕ 建议在此种植海带转化为水源: {g}")

        if self.has_top_spill_risk:
            sb.append("  ⚡ §e[顶端外溢散落高危] 气泡柱顶端缺乏坚固顶盖或侧向承接导流水渠！§r")
            for g in self.ghost_block_placements:
                sb.append(f"     ➕ 建议在顶端上方补全防喷顶盖/半砖: {g}")

        if self.has_flow_stall_risk:
            sb.append("  ⚡ §c[水流动量衰竭停摆] 水道已达到或超过 8 格流动极限！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 推力枯竭点: {c} (水平速度降为0，物品停滞)")

        if self.has_misaligned_stream:
            sb.append("  ⚡ §d[物品流未对齐高危] 并排双漏斗上方水渠缺乏蜂蜜块/箱子边缘内凹对齐！§r")
            for g in self.ghost_block_placements:
                sb.append(f"     ➕ 建议水渠边缘放置蜂蜜块 (0.125格缝隙对齐): {g}")

        if self.has_despawn_vortex_risk:
            sb.append("  ⚡ §c[对冲涡流与5分钟清除高危] 检测到对向流动水死角！§r")
            for c in self.conflict_nodes:
                sb.append(f"     ✖ 滞流死角: {c} (合速度为0，物品积聚5分钟后必定Despawn)")

        if self.is_healthy:
            sb.append("  ✔ §a[物流动力健康] 水流连续性、气泡柱全源与物品导向拓扑正常。§r")

        sb.append(f"▸ §6核心诊断§r：{self.primary_diagnosis}")
        if self.actionable_advice:
            sb.append(f"▸ §a修复建议§r：{self.actionable_advice}")
        return "\\n".join(sb)


class WaterLogisticsAnalyzer:
    @staticmethod
    def analyze(cluster: LocalMachineCluster, focus: BlockPos) -> WaterReport:
        if not cluster or cluster.is_empty:
            return WaterReport(
                is_healthy=True,
                has_broken_bubble_column=False,
                has_top_spill_risk=False,
                has_flow_stall_risk=False,
                has_misaligned_stream=False,
                has_despawn_vortex_risk=False,
                target_pos=BlockPos(0, 0, 0),
                target_block_type="none",
                logistics_type="NONE",
                water_block_count=0,
                ice_block_count=0,
                primary_diagnosis="未检测到水流、气泡柱、冰道物流或物品对齐组件"
            )

        target = cluster.get_block(focus) or cluster.origin_block
        if not target or (not target.is_water and not target.is_soul_sand and not target.is_ice and not target.is_honey_block and not target.is_dropper):
            target = next((b for b in cluster.blocks.values() if b.is_water or b.is_soul_sand or b.is_ice or b.is_honey_block or b.is_dropper), None)

        if not target:
            return WaterReport(
                is_healthy=True,
                has_broken_bubble_column=False,
                has_top_spill_risk=False,
                has_flow_stall_risk=False,
                has_misaligned_stream=False,
                has_despawn_vortex_risk=False,
                target_pos=BlockPos(0, 0, 0),
                target_block_type="none",
                logistics_type="NONE",
                water_block_count=0,
                ice_block_count=0,
                primary_diagnosis="未检测到水流、气泡柱、冰道物流或物品对齐组件"
            )

        target_pos = target.pos
        target_block_type = target.block_id

        conflict_nodes = []
        ghost_block_placements = []
        water_components = []
        issues = []
        warnings = []

        water_count = sum(1 for b in cluster.blocks.values() if b.is_water)
        ice_count = sum(1 for b in cluster.blocks.values() if b.is_ice)
        water_components = [b.pos for b in cluster.blocks.values() if b.is_water]

        has_broken_bubble = False
        has_top_spill = False
        has_flow_stall = False
        has_misaligned = False
        has_despawn_vortex = False

        logistics_type = "NONE"

        # Check 1: Soul Sand Bubble Column
        soul_sand_block = next((b for b in cluster.blocks.values() if b.is_soul_sand), None)
        if soul_sand_block:
            logistics_type = "SOUL_SAND_BUBBLE_ELEVATOR"
            base = soul_sand_block.pos
            cur_y = base.y + 1
            highest_water = None

            while True:
                col_pos = BlockPos(base.x, cur_y, base.z)
                col_block = cluster.get_block(col_pos)
                if not col_block or not col_block.is_water:
                    break
                highest_water = col_pos
                if col_block.is_flowing_water:
                    has_broken_bubble = True
                    conflict_nodes.append(col_pos)
                    ghost_block_placements.append(col_pos)
                    issues.append(f"气泡柱中断卡死：坐标 {col_pos} 为流动水而非全源水源！气泡浮力在此处彻底消失，掉落物无法上升。")
                cur_y += 1

            if highest_water:
                top_cap_pos = highest_water.offset("up")
                top_cap_block = cluster.get_block(top_cap_pos)
                if not top_cap_block or top_cap_block.is_air:
                    has_top_spill = True
                    ghost_block_placements.append(top_cap_pos)
                    warnings.append(f"气泡柱顶端外溢高危：顶端 {top_cap_pos} 缺乏坚固挡板顶盖，垂直高速冲击力将导致掉落物飞出水渠散落丢失。")

        # Check 2: Ice canal 8-block flow stall
        if ice_count > 0:
            if logistics_type == "NONE":
                logistics_type = "ICE_WATER_CANAL"
            water_by_y = {}
            for b in cluster.blocks.values():
                if b.is_water:
                    water_by_y.setdefault(b.pos.y, []).append(b)

            for y, layer in water_by_y.items():
                min_x = min(b.pos.x for b in layer)
                max_x = max(b.pos.x for b in layer)
                min_z = min(b.pos.z for b in layer)
                max_z = max(b.pos.z for b in layer)
                span_x = max_x - min_x + 1
                span_z = max_z - min_z + 1

                has_sign = any(b.is_sign for b in cluster.blocks.values())
                if span_x >= 8 and not has_sign:
                    has_flow_stall = True
                    stall_pos = BlockPos(max_x, y, min_z)
                    conflict_nodes.append(stall_pos)
                    issues.append(f"水流动力耗尽停摆：X轴水流长度达 {span_x} 格，超出 8 格流动极限 (坐标 {stall_pos})，水流推力归零卡死。")
                if span_z >= 8 and not has_sign:
                    has_flow_stall = True
                    stall_pos = BlockPos(min_x, y, max_z)
                    conflict_nodes.append(stall_pos)
                    issues.append(f"水流动力耗尽停摆：Z轴水流长度达 {span_z} 格，超出 8 格流动极限 (坐标 {stall_pos})，水流推力归零卡死。")

        # Check 3: Dual-hopper Item Alignment (Honey Block / Chest edge)
        hoppers = [b for b in cluster.blocks.values() if b.is_hopper]
        if len(hoppers) >= 2:
            is_parallel_hoppers = any(
                h1.pos.y == h2.pos.y and h1.pos.manhattan_distance(h2.pos) == 1
                for i, h1 in enumerate(hoppers) for h2 in hoppers[i+1:]
            )
            if is_parallel_hoppers:
                if logistics_type == "NONE":
                    logistics_type = "ALIGNED_HOPPER_STREAM"
                has_honey = any(b.is_honey_block for b in cluster.blocks.values())
                has_chest = any(b.is_chest for b in cluster.blocks.values())
                if not has_honey and not has_chest:
                    has_misaligned = True
                    for h in hoppers:
                        conflict_nodes.append(h.pos)
                    rec_pos = hoppers[0].pos.offset("up").offset("north")
                    ghost_block_placements.append(rec_pos)
                    warnings.append("物品流未对齐高危：并排双漏斗上方水渠未检测到蜂蜜块或箱子等 0.125 格边缘内凹对齐构件！掉落物无法跨双漏斗吸取盒，吞吐量折半且易溢出丢物。")

        # Check 4: Opposing Eddy Currents & Despawn Vortex
        sources = [b for b in cluster.blocks.values() if b.is_water and b.is_water_source]
        if len(sources) >= 2:
            for i, s1 in enumerate(sources):
                for s2 in sources[i+1:]:
                    if s1.pos.y == s2.pos.y and 1 < s1.pos.manhattan_distance(s2.pos) <= 4:
                        mid = BlockPos((s1.pos.x + s2.pos.x)//2, s1.pos.y, (s1.pos.z + s2.pos.z)//2)
                        mid_block = cluster.get_block(mid)
                        if mid_block and mid_block.is_water:
                            has_despawn_vortex = True
                            conflict_nodes.append(mid)
                            issues.append(f"对冲涡流滞流死角：水源 {s1.pos} 与 {s2.pos} 对向冲击，中间点 {mid} 合速度为零形成滞流漩涡！掉落物滞留 5 分钟后必定被清除 (Despawn)。")

        if logistics_type == "NONE" and (water_count > 0 or ice_count > 0):
            logistics_type = "ICE_WATER_CANAL"

        is_healthy = not has_broken_bubble and not has_top_spill and not has_flow_stall and not has_misaligned and not has_despawn_vortex

        if has_broken_bubble:
            diag = "气泡柱水体中断：存在流动水破坏了全源水连续性，浮力推力消失"
            adv = "在流动水方块处种植海带并催熟至顶层，或在其位置放置冰块打碎转化为水源。"
        elif has_flow_stall:
            diag = "水流超出 8 格流动极限，末端推力衰竭导致物品停摆卡死"
            adv = "在第 8 格放置告示牌阻断水流，留出 1~2 格干燥冰面（依靠惯性滑行），紧接放置新水源开启下一段流水。"
        elif has_despawn_vortex:
            diag = "双向水源对冲形成零速度滞流漩涡，物品面临 5 分钟 Despawn 清除"
            adv = "拆除对冲水源或用告示牌/实体方块建立单向导流挡板，消除对流死角。"
        elif has_misaligned:
            diag = "双漏斗上方水流未对齐，掉落物无法同时覆盖两个漏斗的吸取体积"
            adv = "在水渠侧壁放置蜂蜜块或箱子，利用 14/16 (0.875格) 碰撞箱让物品在 0.125 格边缘内凹处对齐双漏斗中缝。"
        elif has_top_spill:
            diag = "气泡柱顶端缺乏防喷顶盖，高速冲出的掉落物存在外溢散落风险"
            adv = "在气泡柱顶水方块上方 1 格安装平滑石半砖或活板门作为导流顶盖，并布置 90° 横向导流。"
        else:
            diag = "水流与气泡柱物流网络动力学完整健康"
            adv = "水路拓扑规范，全源水连续性与物品推进正常。"

        return WaterReport(
            is_healthy=is_healthy,
            has_broken_bubble_column=has_broken_bubble,
            has_top_spill_risk=has_top_spill,
            has_flow_stall_risk=has_flow_stall,
            has_misaligned_stream=has_misaligned,
            has_despawn_vortex_risk=has_despawn_vortex,
            target_pos=target_pos,
            target_block_type=target_block_type,
            logistics_type=logistics_type,
            water_block_count=water_count,
            ice_block_count=ice_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=ghost_block_placements,
            water_components=water_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )


@dataclass
class FlyingReport:
    is_healthy: bool
    has_push_limit_exceeded: bool
    has_bridging_jam: bool
    has_accidental_adhesion: bool
    has_missing_stopper: bool
    has_observer_polarity_deficit: bool
    target_pos: BlockPos
    target_block_type: str
    engine_type: str
    total_moving_blocks: int
    slime_count: int
    honey_count: int
    conflict_nodes: List[BlockPos]
    ghost_block_placements: List[BlockPos]
    engine_components: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    @classmethod
    def empty(cls) -> "FlyingReport":
        return cls(
            is_healthy=True,
            has_push_limit_exceeded=False,
            has_bridging_jam=False,
            has_accidental_adhesion=False,
            has_missing_stopper=False,
            has_observer_polarity_deficit=False,
            target_pos=BlockPos(0, 0, 0),
            target_block_type="none",
            engine_type="NONE",
            total_moving_blocks=0,
            slime_count=0,
            honey_count=0,
            conflict_nodes=[],
            ghost_block_placements=[],
            engine_components=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到活塞飞行器、机械蠕虫或停靠站组件",
            actionable_advice=""
        )

    def format_report(self) -> str:
        sb = []
        sb.append("§6【双向活塞飞行器与机械蠕虫动力学因果诊断报告】§r")
        sb.append(f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})")
        type_str = {
            "TWO_WAY_REVERSIBLE_ENGINE": "§b双向可逆活塞飞行引擎 (Two-Way Engine)§r",
            "ONE_WAY_ENGINE": "§a单向自主巡航飞行引擎 (One-Way Engine)§r",
            "MULTI_SEGMENT_HARVESTER": "§d多段复合收割/盾构机械 (Multi-Stage Harvester/Bore)§r",
            "DOCKING_STATION": "§e端点停靠与换向基站 (Docking Station)§r",
            "NONE": "§7未识别§r"
        }.get(self.engine_type, "§7未识别§r")
        sb.append(f"▸ 机械引擎构型：{type_str} | 移动负载: {self.total_moving_blocks} 格 (粘液: §a{self.slime_count}§r, 蜂蜜: §6{self.honey_count}§r)")

        if self.has_push_limit_exceeded:
            sb.append("  ⚡ §c[活塞推动超限卡死] 动力构件负载超过 12 格物理推动上限！§r")
            for c_pos in self.conflict_nodes:
                sb.append(f"     ✖ 超载构件/阻挡点: {c_pos}")

        if self.has_bridging_jam:
            sb.append("  ⚡ §c[粘液/蜂蜜短路粘连] 异动引擎构件发生同类粘性方块相互吸附！§r")
            for c_pos in self.conflict_nodes:
                sb.append(f"     ✖ 粘连接触点: {c_pos} (两段无法解耦推进)")
            for g_pos in self.ghost_block_placements:
                sb.append(f"     ➕ 建议在此替换为对立粘性方块或带釉陶瓦: {g_pos}")

        if self.has_accidental_adhesion:
            sb.append("  ⚡ §d[外部地形意外吸附] 粘性方块抓取了周围未隔离的常规地形方块！§r")
            for c_pos in self.conflict_nodes:
                sb.append(f"     ✖ 意外吸附位置: {c_pos}")
            for g_pos in self.ghost_block_placements:
                sb.append(f"     ➕ 建议在此铺设带釉陶瓦导轨: {g_pos}")

        if self.has_missing_stopper:
            sb.append("  ⚡ §e[停靠站缺失黑曜石限位] 飞行器到达端点将冲毁换向基站机构！§r")
            for g_pos in self.ghost_block_placements:
                sb.append(f"     ➕ 建议在停靠撞击端补全黑曜石阻挡块: {g_pos}")

        if self.has_observer_polarity_deficit:
            sb.append("  ⚡ §c[侦测器朝向极性失配] 侦测器输出未正对动力活塞或时序反向！§r")
            for c_pos in self.conflict_nodes:
                sb.append(f"     ✖ 朝向失配侦测器: {c_pos} (单拍运行后失去自激脉冲)")

        if self.is_healthy:
            sb.append("  ✔ §a[飞行引擎动力健康] 12 格负载预算合规，时序闭环与粘液/蜂蜜隔断正常。§r")

        sb.append(f"▸ §6核心诊断§r：{self.primary_diagnosis}")
        if self.actionable_advice:
            sb.append(f"▸ §a修复建议§r：{self.actionable_advice}")
        return "\n".join(sb)


class FlyingMachineAnalyzer:
    @staticmethod
    def opposite_facing(facing: str) -> str:
        return {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
            "up": "down",
            "down": "up"
        }.get(facing.lower(), "down")

    @classmethod
    def calculate_push_cluster(cls, cluster: LocalMachineCluster, piston: LocalBlock, start_pos: BlockPos) -> Set[BlockPos]:
        visited: Set[BlockPos] = set()
        queue: collections.deque = collections.deque()

        start_block = cluster.get_block(start_pos)
        if not start_block or start_block.is_air:
            return visited

        queue.append(start_pos)
        visited.add(start_pos)

        while queue and len(visited) <= 20:
            cur = queue.popleft()
            cur_block = cluster.get_block(cur)
            if not cur_block or cur_block.is_air:
                continue

            if cur_block.is_slime_block:
                for nb_pos in cur.get_direct_neighbors():
                    if nb_pos in visited or nb_pos == piston.pos:
                        continue
                    nb = cluster.get_block(nb_pos)
                    if nb and not nb.is_air and not nb.is_immovable and not nb.is_honey_block and not nb.is_glazed_terracotta:
                        visited.add(nb_pos)
                        queue.append(nb_pos)
            elif cur_block.is_honey_block:
                for nb_pos in cur.get_direct_neighbors():
                    if nb_pos in visited or nb_pos == piston.pos:
                        continue
                    nb = cluster.get_block(nb_pos)
                    if nb and not nb.is_air and not nb.is_immovable and not nb.is_slime_block and not nb.is_glazed_terracotta:
                        visited.add(nb_pos)
                        queue.append(nb_pos)
        return visited

    @classmethod
    def analyze(cls, cluster: LocalMachineCluster, focus: Optional[BlockPos] = None) -> FlyingReport:
        if not cluster or cluster.is_empty:
            return FlyingReport.empty()

        target = cluster.get_block(focus) if focus else None
        if not target:
            target = cluster.origin_block

        if not target or not target.is_flying_component:
            for b in cluster.blocks.values():
                if b.is_flying_component:
                    target = b
                    break

        if not target:
            return FlyingReport.empty()

        target_pos = target.pos
        target_block_type = target.block_id

        conflict_nodes: List[BlockPos] = []
        ghost_block_placements: List[BlockPos] = []
        engine_components: List[BlockPos] = []
        issues: List[str] = []
        warnings: List[str] = []

        pistons = [b for b in cluster.blocks.values() if b.is_piston]
        observers = [b for b in cluster.blocks.values() if b.is_observer]
        slime_blocks = [b for b in cluster.blocks.values() if b.is_slime_block]
        honey_blocks = [b for b in cluster.blocks.values() if b.is_honey_block]

        for b in cluster.blocks.values():
            if b.is_flying_component:
                engine_components.append(b.pos)

        slime_count = len(slime_blocks)
        honey_count = len(honey_blocks)

        engine_type = "ONE_WAY_ENGINE"
        if len(pistons) >= 2:
            facings = {p.facing() for p in pistons}
            has_opposing = (("east" in facings and "west" in facings) or
                            ("north" in facings and "south" in facings) or
                            ("up" in facings and "down" in facings))
            if has_opposing:
                engine_type = "TWO_WAY_REVERSIBLE_ENGINE"
            elif len(pistons) >= 3:
                engine_type = "MULTI_SEGMENT_HARVESTER"
        elif slime_count == 0 and honey_count == 0 and any(b.is_trapdoor or b.is_note_block or b.is_obsidian for b in cluster.blocks.values()):
            engine_type = "DOCKING_STATION"

        has_push_limit_exceeded = False
        has_bridging_jam = False
        has_accidental_adhesion = False
        has_missing_stopper = False
        has_observer_polarity_deficit = False

        max_push_load = 0
        for piston in pistons:
            face_pos = piston.pos.offset(piston.facing())
            push_cluster = cls.calculate_push_cluster(cluster, piston, face_pos)
            if len(push_cluster) > max_push_load:
                max_push_load = len(push_cluster)
            if len(push_cluster) > 12:
                has_push_limit_exceeded = True
                conflict_nodes.append(piston.pos)
                for p in push_cluster:
                    if p not in conflict_nodes:
                        conflict_nodes.append(p)
                issues.append(f"活塞推动超限卡死：活塞 {piston.pos} (朝向 {piston.facing()}) 推动负载达 {len(push_cluster)} 格，超过 12 格物理推动上限！")

        if len(pistons) >= 2:
            p1, p2 = pistons[0], pistons[1]
            if p1.facing() != p2.facing():
                for s1 in slime_blocks:
                    for s2 in slime_blocks:
                        if s1.pos != s2.pos and s1.pos.manhattan_distance(s2.pos) == 1:
                            s1_near_p1 = s1.pos.manhattan_distance(p1.pos) <= s1.pos.manhattan_distance(p2.pos)
                            s2_near_p2 = s2.pos.manhattan_distance(p2.pos) < s2.pos.manhattan_distance(p1.pos)
                            if s1_near_p1 and s2_near_p2:
                                has_bridging_jam = True
                                conflict_nodes.extend([s1.pos, s2.pos])
                                ghost_block_placements.append(s2.pos)
                                issues.append(f"粘连短路死锁：两翼动力构件在 {s1.pos} 与 {s2.pos} 处发生同类粘液块短路粘连！双驱无法解耦，建议将其中一段替换为蜂蜜块。")
                for h1 in honey_blocks:
                    for h2 in honey_blocks:
                        if h1.pos != h2.pos and h1.pos.manhattan_distance(h2.pos) == 1:
                            h1_near_p1 = h1.pos.manhattan_distance(p1.pos) <= h1.pos.manhattan_distance(p2.pos)
                            h2_near_p2 = h2.pos.manhattan_distance(p2.pos) < h2.pos.manhattan_distance(p1.pos)
                            if h1_near_p1 and h2_near_p2:
                                has_bridging_jam = True
                                conflict_nodes.extend([h1.pos, h2.pos])
                                ghost_block_placements.append(h2.pos)
                                issues.append(f"粘连短路死锁：两翼动力构件在 {h1.pos} 与 {h2.pos} 处发生同类蜂蜜块短路粘连！双驱无法解耦，建议将其中一段替换为粘液块。")

        for sticky in cluster.blocks.values():
            if sticky.is_slime_block or sticky.is_honey_block:
                for nb_pos in sticky.pos.get_direct_neighbors():
                    nb = cluster.get_block(nb_pos)
                    if nb and not nb.is_air and not nb.is_flying_component and not nb.is_glazed_terracotta and not nb.is_immovable:
                        has_accidental_adhesion = True
                        conflict_nodes.append(nb_pos)
                        ghost_block_placements.append(nb_pos)
                        warnings.append(f"外界地形意外吸附：粘性方块 {sticky.pos} 意外吸附了外界非绝缘方块 {nb_pos} ({nb.block_id})！建议改用带釉陶瓦隔离。")

        has_docking_trigger = any(b.is_trapdoor or b.is_note_block for b in cluster.blocks.values())
        has_obsidian_stopper = any(b.is_obsidian for b in cluster.blocks.values())
        if has_docking_trigger and not has_obsidian_stopper:
            has_missing_stopper = True
            trigger = next((b for b in cluster.blocks.values() if b.is_trapdoor or b.is_note_block), None)
            if trigger:
                stopper_pos = trigger.pos.offset("up")
                ghost_block_placements.append(stopper_pos)
                conflict_nodes.append(trigger.pos)
            warnings.append("停靠站缺失黑曜石限位阻挡：检测到换向触发机构 (音符盒/活板门)，但未检测到黑曜石阻挡块！飞行器冲入将推毁换向基站。")

        for obs in observers:
            obs_facing = obs.facing()
            output_dir = cls.opposite_facing(obs_facing)
            out_pos = obs.pos.offset(output_dir)
            out_block = cluster.get_block(out_pos)
            output_valid = out_block and (out_block.is_piston or out_block.is_slime_block or out_block.is_honey_block or out_block.is_solid_conductive_block)
            if not output_valid:
                has_observer_polarity_deficit = True
                conflict_nodes.append(obs.pos)
                issues.append(f"侦测器朝向极性失配：侦测器 {obs.pos} 朝向 {obs_facing} (脉冲输出端指向 {output_dir} / {out_pos})，未有效对准动力活塞或传导构件！")

        is_healthy = not has_push_limit_exceeded and not has_bridging_jam and not has_accidental_adhesion and not has_missing_stopper and not has_observer_polarity_deficit

        if has_push_limit_exceeded:
            diag = "飞行器动力构件超载：推动方块总数超过 12 格上限，活塞卡死无法伸展"
            adv = "拆减附带方块或分割推拉动力构件，确保每个活塞推动的粘附子集群 ≤ 12 个方块。"
        elif has_bridging_jam:
            diag = "两翼动力构件发生粘连短路：同种粘性方块相互吸附导致两段无法解耦推进"
            adv = "在相邻动力段交错使用粘液块与蜂蜜块（互不相粘特性），或用带釉陶瓦阻断粘连。"
        elif has_observer_polarity_deficit:
            diag = "侦测器朝向极性颠倒或时序断流：脉冲输出端未正确驱动动力活塞"
            adv = "调整侦测器朝向，确保感应面朝向移动侦测位，红石输出红点精准对准动力活塞或驱动粘性方块。"
        elif has_accidental_adhesion:
            diag = "粘性方块吸附外界未绝缘地形方块，引发整机阻力超载停摆"
            adv = "在飞行轨道两侧隧道或基座铺设带釉陶瓦 (Glazed Terracotta)，利用其不粘特性隔离外界地形。"
        elif has_missing_stopper:
            diag = "端点换向停靠站缺乏黑曜石等不可移动方块进行刚性阻挡拦截"
            adv = "在停靠撞击端加装黑曜石/哭泣黑曜石阻挡块，确保飞行器到位刹车并触发换向更新。"
        else:
            diag = "双向活塞飞行器与机械蠕虫动力学完整健康"
            adv = "动力活塞推拉时钟同步，12格推动预算与粘液/蜂蜜隔断合规，可稳定自激巡航。"

        return FlyingReport(
            is_healthy=is_healthy,
            has_push_limit_exceeded=has_push_limit_exceeded,
            has_bridging_jam=has_bridging_jam,
            has_accidental_adhesion=has_accidental_adhesion,
            has_missing_stopper=has_missing_stopper,
            has_observer_polarity_deficit=has_observer_polarity_deficit,
            target_pos=target_pos,
            target_block_type=target_block_type,
            engine_type=engine_type,
            total_moving_blocks=max_push_load,
            slime_count=slime_count,
            honey_count=honey_count,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=ghost_block_placements,
            engine_components=engine_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )



class ShulkerSystemType(Enum):
    SHULKER_LOADER = "SHULKER_LOADER"
    SHULKER_UNLOADER = "SHULKER_UNLOADER"
    MANUAL_UNLOADER = "MANUAL_UNLOADER"
    NONE = "NONE"


@dataclass
class ShulkerReport:
    is_healthy: bool
    has_dropper_instead_of_dispenser: bool
    has_unlocked_hopper_siphon: bool
    has_box_open_clearance_blocked: bool
    has_uncollected_drop_hazard: bool
    has_persistent_piston_lock: bool
    target_pos: BlockPos
    target_block_type: str
    system_type: ShulkerSystemType
    signal_strength: int
    conflict_nodes: List[BlockPos]
    ghost_block_placements: List[BlockPos]
    system_components: List[BlockPos]
    issues: List[str]
    warnings: List[str]
    primary_diagnosis: str
    actionable_advice: str

    @classmethod
    def empty(cls) -> "ShulkerReport":
        return cls(
            is_healthy=True,
            has_dropper_instead_of_dispenser=False,
            has_unlocked_hopper_siphon=False,
            has_box_open_clearance_blocked=False,
            has_uncollected_drop_hazard=False,
            has_persistent_piston_lock=False,
            target_pos=BlockPos(0, 0, 0),
            target_block_type="none",
            system_type=ShulkerSystemType.NONE,
            signal_strength=0,
            conflict_nodes=[],
            ghost_block_placements=[],
            system_components=[],
            issues=[],
            warnings=[],
            primary_diagnosis="未检测到潜影盒装盒机、拆盒机或物流自动化组件",
            actionable_advice=""
        )

    def format_report(self) -> str:
        lines = [
            "§6【潜影盒装卸物流与自动化因果诊断报告】§r",
            f"▸ 目标组件坐标：{self.target_pos} ({self.target_block_type.upper()})",
            f"▸ 物流系统构型：{self.system_type.value} | 比较器信号: §e{self.signal_strength}/15§r"
        ]
        if self.has_dropper_instead_of_dispenser:
            lines.append("  ⚡ §c[投掷器误用致命卡死] 放置潜影盒必须使用发射器 (Dispenser)，误用投掷器只会将盒子作为掉落物吐出！§r")
            for c in self.conflict_nodes:
                lines.append(f"     ✖ 误用投掷器: {c}")
            for g in self.ghost_block_placements:
                lines.append(f"     ➕ 建议在此替换为发射器: {g}")
        if self.has_unlocked_hopper_siphon:
            lines.append("  ⚡ §c[下方漏斗偷吸空盒] 装盒机下方收集漏斗未施加红石锁定，新放置的空盒被立刻吸走导致无限吐盒！§r")
            for c in self.conflict_nodes:
                lines.append(f"     ✖ 未锁定漏斗: {c}")
        if self.has_box_open_clearance_blocked:
            lines.append("  ⚡ §e[开盖空间物理受阻] 潜影盒开盖朝向正前方 1 格被实心方块封堵，无法正常开启！§r")
            for c in self.conflict_nodes:
                lines.append(f"     ⚠ 阻挡方块: {c}")
        if self.has_uncollected_drop_hazard:
            lines.append("  ⚡ §e[掉落物无收集通道] 活塞推破潜影盒的落点周围无漏斗或水流承接，满载潜影盒将在 5 分钟后清除！§r")
            for c in self.conflict_nodes:
                lines.append(f"     ⚠ 缺乏收集落点: {c}")
        if self.has_persistent_piston_lock:
            lines.append("  ⚡ §c[活塞持续伸出死锁] 拆盒机推盒活塞处于持续伸出状态，阻挡发射器放置下一个潜影盒！§r")
            for c in self.conflict_nodes:
                lines.append(f"     ✖ 持续通电活塞: {c}")
        if self.is_healthy:
            lines.append("  ✔ §a潜影盒自动化流水线物理拓扑、发射时序与收集通道健康无死锁。§r")
        lines.append(f"▸ 因果诊断：{self.primary_diagnosis}")
        if self.actionable_advice:
            lines.append(f"▸ 优化建议：{self.actionable_advice}")
        return "\n".join(lines)


class ShulkerLogisticsAnalyzer:
    @classmethod
    def analyze(cls, cluster: LocalMachineCluster, focus: Optional[BlockPos] = None) -> ShulkerReport:
        if focus is None:
            focus = cluster.origin if cluster else BlockPos(0, 0, 0)
        return cls.analyze_shulker(cluster, focus)

    @classmethod
    def analyze_shulker(cls, cluster: LocalMachineCluster, focus: BlockPos) -> ShulkerReport:
        if not cluster or not cluster.blocks:
            return ShulkerReport.empty()

        target = cluster.get_block(focus)
        if not target:
            any_shulker = next((b for b in cluster.blocks.values() if b.is_shulker_component), None)
            if any_shulker:
                target = any_shulker
                focus = target.pos
            else:
                return ShulkerReport.empty()

        shulkers = [b for b in cluster.blocks.values() if b.is_shulker_box]
        dispensers = [b for b in cluster.blocks.values() if b.is_dispenser]
        droppers = [b for b in cluster.blocks.values() if b.is_dropper]
        pistons = [b for b in cluster.blocks.values() if b.is_piston]
        hoppers = [b for b in cluster.blocks.values() if b.is_hopper]
        comparators = [b for b in cluster.blocks.values() if b.is_comparator]

        if not shulkers and not dispensers and not droppers:
            return ShulkerReport.empty()

        system_components = [b.pos for b in shulkers + dispensers + droppers + pistons + hoppers + comparators]

        has_top_feeding = False
        has_bottom_extracting = False
        for s in shulkers:
            ab = cluster.get_block(s.pos.offset("up"))
            bl = cluster.get_block(s.pos.offset("down"))
            if ab and ab.is_hopper:
                has_top_feeding = True
            if bl and bl.is_hopper:
                has_bottom_extracting = True

        if has_top_feeding or (dispensers and pistons and not has_bottom_extracting):
            system_type = ShulkerSystemType.SHULKER_LOADER
        elif has_bottom_extracting and (pistons or dispensers):
            system_type = ShulkerSystemType.SHULKER_UNLOADER
        elif shulkers:
            system_type = ShulkerSystemType.MANUAL_UNLOADER
        elif dispensers or droppers:
            system_type = ShulkerSystemType.SHULKER_LOADER
        else:
            system_type = ShulkerSystemType.NONE

        conflict_nodes = []
        ghost_block_placements = []
        issues = []
        warnings = []

        has_dropper_instead_of_dispenser = False
        has_unlocked_hopper_siphon = False
        has_box_open_clearance_blocked = False
        has_uncollected_drop_hazard = False
        has_persistent_piston_lock = False

        # 1. Dropper vs Dispenser
        for d in droppers:
            target_placement = d.pos.offset(d.facing())
            if target_placement in cluster.blocks or system_type == ShulkerSystemType.SHULKER_LOADER:
                has_dropper_instead_of_dispenser = True
                conflict_nodes.append(d.pos)
                ghost_block_placements.append(d.pos)
                issues.append(f"在 {d.pos} 处误用了投掷器代替发射器，导致潜影盒作为掉落物喷出")

        # 2. Unlocked Hopper Siphon in Loader
        if system_type == ShulkerSystemType.SHULKER_LOADER:
            for s in shulkers:
                bl = cluster.get_block(s.pos.offset("down"))
                if bl and bl.is_hopper:
                    is_locked = bl.is_powered or bl.get_property("enabled", "true").lower() == "false"
                    if not is_locked:
                        has_unlocked_hopper_siphon = True
                        conflict_nodes.append(bl.pos)
                        ghost_block_placements.append(bl.pos.offset("east"))
                        issues.append(f"装盒机下方收集漏斗 {bl.pos} 未受红石锁定，新盒发射将被直接偷吸")

        # 3. Open Clearance Blocked
        for s in shulkers:
            s_facing = s.facing() or "up"
            open_pos = s.pos.offset(s_facing)
            open_b = cluster.get_block(open_pos)
            if open_b and open_b.is_solid_conductive_block:
                has_box_open_clearance_blocked = True
                conflict_nodes.append(open_pos)
                warnings.append(f"潜影盒 {s.pos} 正前方开盖空间 {open_pos} 被实心方块封堵，无法开启")

        # 4. Uncollected Drop Hazard
        for p in pistons:
            p_facing = p.facing()
            break_target = p.pos.offset(p_facing)
            tb = cluster.get_block(break_target)
            if tb and (tb.is_shulker_box or tb.is_air):
                has_collector = False
                for nb in break_target.get_direct_neighbors():
                    nb_b = cluster.get_block(nb)
                    if nb_b and (nb_b.is_hopper or nb_b.is_water):
                        has_collector = True
                        break
                bl_tb = cluster.get_block(break_target.offset("down"))
                if bl_tb and (bl_tb.is_hopper or bl_tb.is_water):
                    has_collector = True
                if not has_collector:
                    has_uncollected_drop_hazard = True
                    conflict_nodes.append(break_target)
                    ghost_block_placements.append(break_target.offset("down"))
                    warnings.append(f"活塞推破目标位 {break_target} 下方缺乏漏斗或水流收集通道，潜影盒面临清除风险")

        # 5. Persistent Piston Lock in Unloader
        if system_type == ShulkerSystemType.SHULKER_UNLOADER:
            for p in pistons:
                if p.is_extended or p.is_powered:
                    has_persistent_piston_lock = True
                    conflict_nodes.append(p.pos)
                    issues.append(f"拆盒机推盒活塞 {p.pos} 处于持续伸出状态，阻挡发射器放置下一个潜影盒")

        signal_strength = 0
        for comp in comparators:
            try:
                sig = int(comp.get_property("power", "0"))
                if sig > signal_strength:
                    signal_strength = sig
            except ValueError:
                pass

        is_healthy = not has_dropper_instead_of_dispenser and not has_unlocked_hopper_siphon and \
                     not has_box_open_clearance_blocked and not has_uncollected_drop_hazard and not has_persistent_piston_lock

        if has_dropper_instead_of_dispenser:
            diag = "装盒机误用了投掷器代替发射器，潜影盒被当作掉落物吐出无法放置。"
            adv = "将投掷器 (Dropper) 替换为发射器 (Dispenser)，圆孔朝向潜影盒放置位。"
        elif has_unlocked_hopper_siphon:
            diag = "装盒机下方收集漏斗未施加红石锁存，导致空盒落位即被偷吸。"
            adv = "在活塞推破与发射新盒期间，通过红石火把或比较器脉冲锁死下方漏斗，落位后再解锁。"
        elif has_persistent_piston_lock:
            diag = "拆盒机活塞持续伸出阻挡新盒放置，缺少单稳态短脉冲截断。"
            adv = "在比较器信号归零检测端接入 1~2 刻单稳态脉冲电路 (Monostable Circuit) 产生瞬态推破脉冲。"
        elif has_box_open_clearance_blocked:
            diag = "潜影盒开盖空间被实心方块遮挡，玩家或机械无法打开。"
            adv = "将开盖正前方的方块替换为玻璃、半砖、楼梯或空气。"
        elif has_uncollected_drop_hazard:
            diag = "活塞推破落点周围缺乏漏斗或水流收集通道，潜影盒面临清除风险。"
            adv = "在潜影盒落点下方铺设漏斗、漏斗矿车或导流水渠承接。"
        else:
            diag = "潜影盒装卸物流系统物理拓扑、发射时序与开盖通道健康。"
            adv = "保持发射器备用盒供应，定期检查比较器信号线防外部串扰。"

        return ShulkerReport(
            is_healthy=is_healthy,
            has_dropper_instead_of_dispenser=has_dropper_instead_of_dispenser,
            has_unlocked_hopper_siphon=has_unlocked_hopper_siphon,
            has_box_open_clearance_blocked=has_box_open_clearance_blocked,
            has_uncollected_drop_hazard=has_uncollected_drop_hazard,
            has_persistent_piston_lock=has_persistent_piston_lock,
            target_pos=focus,
            target_block_type=target.block_id,
            system_type=system_type,
            signal_strength=signal_strength,
            conflict_nodes=conflict_nodes,
            ghost_block_placements=ghost_block_placements,
            system_components=system_components,
            issues=issues,
            warnings=warnings,
            primary_diagnosis=diag,
            actionable_advice=adv
        )
