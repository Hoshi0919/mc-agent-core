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

    @property
    def size(self) -> int:
        return len(self.blocks)

    @property
    def is_empty(self) -> bool:
        return len(self.blocks) == 0

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
