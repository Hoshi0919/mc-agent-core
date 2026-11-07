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
