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
    def is_air(self) -> bool:
        if not self.block_id:
            return True
        bid = self.block_id.lower()
        return bid in ("air", "minecraft:air", "cave_air", "minecraft:cave_air", "void_air", "minecraft:void_air")

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

    def is_powered(self) -> bool:
        return self.get_property("powered", "false").lower() == "true" 

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
    def is_extended(self) -> bool:
        return self.get_property("extended", "false").lower() == "true"

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
