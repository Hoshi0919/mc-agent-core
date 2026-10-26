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

    @property
    def size(self) -> int:
        return len(self.blocks)

    def to_summary(self) -> str:
        return f"Cluster centered at {self.origin} with {self.size} blocks (Kinetics: {len(self.get_connected_kinetics())}, Hoppers: {len(self.get_connected_hoppers())})"


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
