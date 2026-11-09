from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import json
import re
import time

from .cluster import BlockPos, LocalMachineCluster, KineticReport, HopperReport
from .multiblock import MultiblockBlueprint


class SpatialColor:
    def __init__(self, red: int, green: int, blue: int, alpha: int = 180):
        self.red = max(0, min(255, red))
        self.green = max(0, min(255, green))
        self.blue = max(0, min(255, blue))
        self.alpha = max(0, min(255, alpha))

    def with_alpha(self, new_alpha: int) -> 'SpatialColor':
        return SpatialColor(self.red, self.green, self.blue, new_alpha)

    def to_hex(self) -> str:
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}{self.alpha:02X}"

    def to_dict(self) -> Dict[str, int]:
        return {"r": self.red, "g": self.green, "b": self.blue, "a": self.alpha}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        return f"SpatialColor(r={self.red}, g={self.green}, b={self.blue}, a={self.alpha})"


SpatialColor.RED = SpatialColor(255, 60, 60, 180)
SpatialColor.GREEN = SpatialColor(60, 255, 60, 180)
SpatialColor.BLUE = SpatialColor(60, 150, 255, 180)
SpatialColor.YELLOW = SpatialColor(255, 215, 0, 180)
SpatialColor.ORANGE = SpatialColor(255, 140, 0, 180)
SpatialColor.CYAN = SpatialColor(0, 255, 255, 180)
SpatialColor.PURPLE = SpatialColor(186, 85, 211, 180)
SpatialColor.WHITE = SpatialColor(255, 255, 255, 200)


class PrimitiveType(Enum):
    BOX_OUTLINE = "BOX_OUTLINE"
    GHOST_BLOCK = "GHOST_BLOCK"
    FLOW_ARROW = "FLOW_ARROW"
    SPHERE_BOUNDARY = "SPHERE_BOUNDARY"
    BILLBOARD = "BILLBOARD"


@dataclass
class SpatialPrimitive:
    type: PrimitiveType
    color: SpatialColor
    duration_ticks: int = 200
    label: Optional[str] = None
    pos: Optional[BlockPos] = None
    min_pos: Optional[BlockPos] = None
    max_pos: Optional[BlockPos] = None
    block_id: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    from_pos: Optional[BlockPos] = None
    to_pos: Optional[BlockPos] = None
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    radius: float = 0.0

    @classmethod
    def box_outline(cls, pos: BlockPos, color: SpatialColor, label: Optional[str] = None, duration_ticks: int = 200, max_pos: Optional[BlockPos] = None):
        return cls(
            type=PrimitiveType.BOX_OUTLINE,
            color=color,
            duration_ticks=duration_ticks,
            label=label,
            pos=pos,
            min_pos=pos,
            max_pos=max_pos if max_pos else pos
        )

    @classmethod
    def ghost_block(cls, pos: BlockPos, block_id: str, properties: Optional[Dict[str, str]] = None, color: Optional[SpatialColor] = None, duration_ticks: int = 600):
        return cls(
            type=PrimitiveType.GHOST_BLOCK,
            color=color or SpatialColor.BLUE,
            duration_ticks=duration_ticks,
            pos=pos,
            min_pos=pos,
            max_pos=pos,
            block_id=block_id,
            properties=properties or {}
        )

    @classmethod
    def flow_arrow(cls, from_pos: BlockPos, to_pos: BlockPos, color: SpatialColor, label: Optional[str] = None, duration_ticks: int = 300):
        return cls(
            type=PrimitiveType.FLOW_ARROW,
            color=color,
            duration_ticks=duration_ticks,
            label=label,
            from_pos=from_pos,
            to_pos=to_pos,
            pos=from_pos
        )

    @classmethod
    def sphere_boundary(cls, cx: float, cy: float, cz: float, radius: float, color: SpatialColor, label: Optional[str] = None, duration_ticks: int = 400):
        return cls(
            type=PrimitiveType.SPHERE_BOUNDARY,
            color=color,
            duration_ticks=duration_ticks,
            label=label,
            center_x=cx,
            center_y=cy,
            center_z=cz,
            radius=radius
        )

    @classmethod
    def billboard(cls, pos: BlockPos, text: str, color: SpatialColor, duration_ticks: int = 300):
        return cls(
            type=PrimitiveType.BILLBOARD,
            color=color,
            duration_ticks=duration_ticks,
            label=text,
            pos=pos
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "type": self.type.value,
            "color": self.color.to_dict(),
            "duration": self.duration_ticks
        }
        if self.label:
            d["label"] = self.label
        if self.pos:
            d["pos"] = {"x": self.pos.x, "y": self.pos.y, "z": self.pos.z}
        if self.min_pos and self.max_pos:
            d["min"] = {"x": self.min_pos.x, "y": self.min_pos.y, "z": self.min_pos.z}
            d["max"] = {"x": self.max_pos.x, "y": self.max_pos.y, "z": self.max_pos.z}
        if self.block_id:
            d["blockId"] = self.block_id
        if self.properties:
            d["properties"] = self.properties
        if self.from_pos and self.to_pos:
            d["from"] = {"x": self.from_pos.x, "y": self.from_pos.y, "z": self.from_pos.z}
            d["to"] = {"x": self.to_pos.x, "y": self.to_pos.y, "z": self.to_pos.z}
        if self.type == PrimitiveType.SPHERE_BOUNDARY:
            d["sphere"] = {
                "cx": self.center_x, "cy": self.center_y, "cz": self.center_z,
                "radius": self.radius
            }
        return d


@dataclass
class SpatialDirectivePacket:
    channel: str = "hoshi:spatial_overlay"
    id: str = "overlay"
    category: str = "GENERAL"
    primitives: List[SpatialPrimitive] = field(default_factory=list)
    hud_title: Optional[str] = None
    hud_description: Optional[str] = None
    clear_previous: bool = True
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def is_empty(self) -> bool:
        if self.category == "NONE" and not self.clear_previous:
            return True
        return len(self.primitives) == 0 and not self.hud_title and not self.clear_previous

    def size(self) -> int:
        return len(self.primitives)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "channel": self.channel,
            "id": self.id,
            "category": self.category,
            "clearPrevious": self.clear_previous,
            "timestamp": self.timestamp,
            "primitives": [p.to_dict() for p in self.primitives]
        }
        if self.hud_title:
            d["hudTitle"] = self.hud_title
        if self.hud_description:
            d["hudDescription"] = self.hud_description
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def clear(cls, category: str = "ALL") -> 'SpatialDirectivePacket':
        return cls(id=f"clear-{category}", category=category, primitives=[], clear_previous=True)

    @classmethod
    def empty(cls) -> 'SpatialDirectivePacket':
        return cls(id="empty", category="NONE", primitives=[], clear_previous=False)


class SpatialDirectiveGenerator:
    BLOCK_POS_PATTERN = re.compile(r"\[(-?\d+),\s*(-?\d+),\s*(-?\d+)\]")

    @classmethod
    def generate_kinetic_overlay(cls, cluster: Optional[LocalMachineCluster], report: Optional[KineticReport]) -> SpatialDirectivePacket:
        if not report or report.total_components == 0:
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 300

        if report.is_jammed:
            conflict_positions = set()
            for c_str in report.conflicts:
                matches = cls.BLOCK_POS_PATTERN.findall(c_str)
                coords = [BlockPos(int(x), int(y), int(z)) for x, y, z in matches]
                if len(coords) >= 2:
                    p1, p2 = coords[0], coords[1]
                    conflict_positions.add(p1)
                    conflict_positions.add(p2)
                    primitives.append(SpatialPrimitive.flow_arrow(p1, p2, SpatialColor.RED, "JAMMED RATIO", duration))
                elif len(coords) == 1:
                    conflict_positions.add(coords[0])

            for p in conflict_positions:
                primitives.append(SpatialPrimitive.box_outline(p, SpatialColor.RED, "JAMMED", duration))

            if conflict_positions:
                first = next(iter(conflict_positions))
                primitives.append(SpatialPrimitive.billboard(first.offset("up"), "⚠ 传动冲突卡死点", SpatialColor.RED, duration))

            return SpatialDirectivePacket(
                id=f"kinetic-jam-{int(time.time()*1000)}",
                category="KINETIC_JAM",
                primitives=primitives,
                hud_title=report.primary_diagnosis,
                hud_description=report.actionable_remediation
            )
        else:
            if cluster:
                for b in cluster.get_connected_kinetics():
                    primitives.append(SpatialPrimitive.box_outline(b.pos, SpatialColor.GREEN.with_alpha(120), "OK", 100))

            return SpatialDirectivePacket(
                id=f"kinetic-healthy-{int(time.time()*1000)}",
                category="KINETIC_HEALTHY",
                primitives=primitives,
                hud_title=report.primary_diagnosis,
                hud_description=report.actionable_remediation
            )

    @classmethod
    def generate_hopper_overlay(cls, cluster: Optional[LocalMachineCluster], report: Optional[HopperReport]) -> SpatialDirectivePacket:
        if not report or report.total_hoppers == 0:
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 300

        if cluster:
            for h in cluster.get_connected_hoppers():
                target = h.pos.offset(h.facing())
                primitives.append(SpatialPrimitive.flow_arrow(h.pos, target, SpatialColor.CYAN.with_alpha(140), "FLOW", duration))

        if report.has_deadlock:
            for d_str in report.deadlocks:
                matches = cls.BLOCK_POS_PATTERN.findall(d_str)
                cycle = [BlockPos(int(x), int(y), int(z)) for x, y, z in matches]
                for i in range(len(cycle)):
                    cur = cycle[i]
                    nxt = cycle[(i + 1) % len(cycle)]
                    primitives.append(SpatialPrimitive.box_outline(cur, SpatialColor.YELLOW, "DEADLOCK", duration))
                    primitives.append(SpatialPrimitive.flow_arrow(cur, nxt, SpatialColor.ORANGE, "CYCLE", duration))

        if report.has_backpressure:
            for s_str in report.stalled_hoppers:
                m = cls.BLOCK_POS_PATTERN.search(s_str)
                if m:
                    p = BlockPos(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    primitives.append(SpatialPrimitive.box_outline(p, SpatialColor.RED, "BACKPRESSURE", duration))

        if report.has_bleed_risk:
            for w_str in report.warnings:
                m = cls.BLOCK_POS_PATTERN.search(w_str)
                if m:
                    p = BlockPos(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    primitives.append(SpatialPrimitive.box_outline(p, SpatialColor.PURPLE, "BLEED RISK >45", duration))

        return SpatialDirectivePacket(
            id=f"hopper-diag-{int(time.time()*1000)}",
            category="HOPPER_DIAGNOSTICS",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )

    @classmethod
    def generate_multiblock_ghost_overlay(cls, blueprint: MultiblockBlueprint, center_pos: BlockPos) -> SpatialDirectivePacket:
        if not blueprint or not center_pos:
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 600

        half_x = blueprint.width_x // 2
        half_y = blueprint.height_y // 2
        half_z = blueprint.depth_z // 2

        if blueprint.id.lower() == "conduit":
            layers = blueprint.layer_schematics
            for ly in range(min(5, len(layers))):
                rows = layers[ly]
                world_y = center_pos.y - half_y + ly
                for row_idx, line in enumerate(rows):
                    world_z = center_pos.z - half_z + row_idx
                    for col_idx, char in enumerate(line):
                        world_x = center_pos.x - half_x + col_idx
                        p = BlockPos(world_x, world_y, world_z)
                        if char == '#':
                            primitives.append(SpatialPrimitive.ghost_block(p, "minecraft:prismarine", color=SpatialColor.BLUE.with_alpha(160), duration_ticks=duration))
                        elif char == 'C':
                            primitives.append(SpatialPrimitive.ghost_block(p, "minecraft:conduit", color=SpatialColor.CYAN.with_alpha(220), duration_ticks=duration))
        elif blueprint.id.lower().startswith("beacon"):
            layers_count = blueprint.height_y - 1
            for l in range(layers_count):
                radius = layers_count - l
                cur_y = center_pos.y + l
                for dx in range(-radius, radius + 1):
                    for dz in range(-radius, radius + 1):
                        p = BlockPos(center_pos.x + dx, cur_y, center_pos.z + dz)
                        primitives.append(SpatialPrimitive.ghost_block(p, "minecraft:iron_block", color=SpatialColor.YELLOW.with_alpha(140), duration_ticks=duration))
            primitives.append(SpatialPrimitive.ghost_block(BlockPos(center_pos.x, center_pos.y + layers_count, center_pos.z), "minecraft:beacon", color=SpatialColor.CYAN.with_alpha(220), duration_ticks=duration))
        else:
            min_pos = BlockPos(center_pos.x - half_x, center_pos.y, center_pos.z - half_z)
            max_pos = BlockPos(center_pos.x + half_x, center_pos.y + blueprint.height_y, center_pos.z + half_z)
            primitives.append(SpatialPrimitive.box_outline(min_pos, SpatialColor.BLUE, label=blueprint.name, duration_ticks=duration, max_pos=max_pos))

        primitives.append(SpatialPrimitive.billboard(
            BlockPos(center_pos.x, center_pos.y + blueprint.height_y + 1, center_pos.z),
            f"蓝图投影: {blueprint.name}",
            SpatialColor.YELLOW,
            duration
        ))

        return SpatialDirectivePacket(
            id=f"multiblock-{blueprint.id}-{int(time.time()*1000)}",
            category="MULTIBLOCK_GHOST",
            primitives=primitives,
            hud_title=f"多方块蓝图全息投影: {blueprint.name}",
            hud_description=blueprint.core_activation_condition
        )

    @classmethod
    def generate_mob_farm_overlay(cls, player_x: float, player_y: float, player_z: float) -> SpatialDirectivePacket:
        primitives: List[SpatialPrimitive] = [
            SpatialPrimitive.sphere_boundary(player_x, player_y, player_z, 24.0, SpatialColor.RED.with_alpha(150), "0-24m: 绝对禁刷盲区 (No-Spawn Zone)", 400),
            SpatialPrimitive.sphere_boundary(player_x, player_y, player_z, 32.0, SpatialColor.GREEN.with_alpha(180), "24-32m: 黄金高频活动圈 (Active Golden Sphere)", 400),
            SpatialPrimitive.sphere_boundary(player_x, player_y, player_z, 128.0, SpatialColor.CYAN.with_alpha(120), "128m: 瞬间蒸发视界 (Instant Despawn Horizon)", 400),
            SpatialPrimitive.billboard(BlockPos(int(player_x), int(player_y) + 2, int(player_z)), "生电刷怪动力学生成圈 (24m/32m/128m)", SpatialColor.GREEN, 400)
        ]
        return SpatialDirectivePacket(
            id=f"mobfarm-spheres-{int(time.time()*1000)}",
            category="MOB_FARM_SPHERES",
            primitives=primitives,
            hud_title="生电清除球与生成动力学视界",
            hud_description="红色=24m禁刷，绿色=32m黄金活动区，青色=128m瞬间清除界"
        )


    @classmethod
    def generate_ae2_overlay(cls, cluster: Optional[Any], report: Optional[Any]) -> SpatialDirectivePacket:
        if not report or (report.total_controllers == 0 and report.total_cables == 0 and report.total_devices == 0):
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 300

        for pos in report.illegal_interior_controllers:
            primitives.append(SpatialPrimitive.box_outline(pos, SpatialColor.RED, "ILLEGAL INTERIOR", duration))
            primitives.append(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 控制器实心内部违规方块", SpatialColor.RED, duration))

        for pos in report.overloaded_cables:
            primitives.append(SpatialPrimitive.box_outline(pos, SpatialColor.ORANGE, "CABLE OVERLOAD", duration))
            primitives.append(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 频道过载线缆", SpatialColor.ORANGE, duration))

        for pos in report.offline_devices:
            primitives.append(SpatialPrimitive.box_outline(pos, SpatialColor.YELLOW, "MISSING CHANNEL", duration))
            primitives.append(SpatialPrimitive.ghost_block(pos, "ae2:missing_channel", {"state": "offline"}, SpatialColor.YELLOW, duration))
            primitives.append(SpatialPrimitive.billboard(pos.offset("up"), "⚠ 频道耗尽离线", SpatialColor.YELLOW, duration))

        if report.is_healthy and report.total_devices > 0:
            if cluster and getattr(cluster, "origin", None):
                org = cluster.origin
                primitives.append(SpatialPrimitive.box_outline(org, SpatialColor.CYAN, "AE2 OK", duration))
                primitives.append(SpatialPrimitive.billboard(org.offset("up"), f"✔ AE2 在线: {report.online_devices}台", SpatialColor.CYAN, duration))

        return SpatialDirectivePacket(
            id=f"ae2-network-{int(time.time()*1000)}",
            category="AE2_NETWORK",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_remediation
        )


    @classmethod
    def generate_piston_overlay(cls, cluster: Optional[Any], report: Optional[Any]) -> SpatialDirectivePacket:
        if not report or getattr(report, "piston_facing", "unknown") == "unknown":
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 300
        p_pos = report.piston_pos

        # 1. Highlight Piston itself
        if report.is_bud_locked:
            primitives.append(SpatialPrimitive.box_outline(p_pos, SpatialColor.YELLOW, "BUD LOCK", duration))
            primitives.append(SpatialPrimitive.billboard(p_pos.offset("up"), "⚠ BUD 锁定：需方块更新复位", SpatialColor.YELLOW, duration))
        elif report.is_bud_pending:
            primitives.append(SpatialPrimitive.box_outline(p_pos, SpatialColor.CYAN, "BUD ARMED", duration))
            primitives.append(SpatialPrimitive.billboard(p_pos.offset("up"), "ℹ BUD 待命：等待更新触发", SpatialColor.CYAN, duration))
        elif not report.is_healthy:
            primitives.append(SpatialPrimitive.box_outline(p_pos, SpatialColor.RED, "PISTON STALLED", duration))
        else:
            primitives.append(SpatialPrimitive.box_outline(p_pos, SpatialColor.GREEN, "PISTON OK", duration))

        # 2. Quasi-Connectivity (QC) sources
        for qp in report.qc_power_sources:
            primitives.append(SpatialPrimitive.box_outline(qp, SpatialColor.CYAN, "QC POWER SOURCE", duration))
            primitives.append(SpatialPrimitive.flow_arrow(qp, p_pos, SpatialColor.CYAN, "QUASI-CONNECTIVITY (QC)", duration))
            primitives.append(SpatialPrimitive.billboard(qp.offset("up"), "⚡ 隔空准连接电源", SpatialColor.CYAN, duration))

        # 3. Immovable obstacles
        for ip in report.immovable_blocks:
            primitives.append(SpatialPrimitive.box_outline(ip, SpatialColor.PURPLE, "IMMOVABLE BLOCK", duration))
            primitives.append(SpatialPrimitive.billboard(ip.offset("up"), "✖ 不可推动障碍", SpatialColor.PURPLE, duration))

        # 4. Push chain and push limit overloads
        if report.is_push_limit_exceeded:
            for i, b_pos in enumerate(report.push_chain):
                if i >= 12:
                    primitives.append(SpatialPrimitive.box_outline(b_pos, SpatialColor.RED, "PUSH LIMIT (MAX 12)", duration))
                    primitives.append(SpatialPrimitive.billboard(b_pos.offset("up"), f"✖ 超载方块 (#{i + 1})", SpatialColor.RED, duration))
                else:
                    primitives.append(SpatialPrimitive.box_outline(b_pos, SpatialColor.ORANGE, f"BLOCK #{i + 1}", duration))

        return SpatialDirectivePacket(
            id=f"piston-dynamics-{int(time.time()*1000)}",
            category="PISTON_DYNAMICS",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )

    @classmethod
    def generate_comparator_overlay(cls, cluster: Optional[Any], report: Optional[Any]) -> SpatialDirectivePacket:
        if not report or (getattr(report, "container_type", "none") == "none" and report.output_signal == 0 and report.redstone_wire_length == 0 and not report.is_subtract_mode):
            return SpatialDirectivePacket.empty()

        primitives: List[SpatialPrimitive] = []
        duration = 300
        c_pos = report.comparator_pos

        # 1. Comparator outline
        if report.has_crosstalk_risk or report.has_unstackable_pollution:
            primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.RED, "COMPARATOR HAZARD", duration))
            primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), f"⚡ 比较器告警 (信号: {report.output_signal})", SpatialColor.RED, duration))
        elif report.is_subtract_mode:
            primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.PURPLE, "SUBTRACT MODE", duration))
            primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), f"➖ 减法模式 (输出: {report.output_signal})", SpatialColor.PURPLE, duration))
        else:
            primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.YELLOW, "COMPARATOR", duration))
            primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), f"⚡ 比较模式 (信号: {report.output_signal})", SpatialColor.YELLOW, duration))

        # 2. Bound container
        if getattr(report, "container_type", "none") != "none":
            cont_pos = report.container_pos
            if report.has_unstackable_pollution:
                primitives.append(SpatialPrimitive.box_outline(cont_pos, SpatialColor.PURPLE, "POLLUTED CONTAINER", duration))
                primitives.append(SpatialPrimitive.billboard(cont_pos.offset("up"), "✖ 槽位污染：不可堆叠物品", SpatialColor.PURPLE, duration))
            else:
                primitives.append(SpatialPrimitive.box_outline(cont_pos, SpatialColor.CYAN, "CONTAINER", duration))
                primitives.append(SpatialPrimitive.billboard(cont_pos.offset("up"), f"📦 容器负载: {report.filled_item_count} 物品", SpatialColor.CYAN, duration))

        # 3. Redstone wire chain
        if report.redstone_wire_chain:
            for i, w_pos in enumerate(report.redstone_wire_chain):
                if report.has_crosstalk_risk:
                    primitives.append(SpatialPrimitive.box_outline(w_pos, SpatialColor.RED, "CROSSTALK WIRE", duration))
                elif report.is_overflow_protected:
                    primitives.append(SpatialPrimitive.box_outline(w_pos, SpatialColor.GREEN, f"WIRE #{i + 1}", duration))
                else:
                    primitives.append(SpatialPrimitive.box_outline(w_pos, SpatialColor.ORANGE, f"WIRE #{i + 1}", duration))

        # 4. Crosstalk leakage targets
        for leak_target in report.crosstalk_leak_targets:
            primitives.append(SpatialPrimitive.box_outline(leak_target, SpatialColor.RED, "CROSSTALK LEAK TARGET", duration))
            primitives.append(SpatialPrimitive.flow_arrow(c_pos, leak_target, SpatialColor.RED, "CROSSTALK LEAK", duration))
            primitives.append(SpatialPrimitive.billboard(leak_target.offset("up"), "⚠ 串扰信号泄漏毁损", SpatialColor.RED, duration))

        return SpatialDirectivePacket(
            id=f"comparator-dynamics-{int(time.time()*1000)}",
            category="COMPARATOR_DYNAMICS",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )


    @classmethod
    def generate_transmission_overlay(cls, cluster: Optional[Any], report: Optional[Any]) -> SpatialDirectivePacket:
        if not report:
            return SpatialDirectivePacket.empty()

        primitives = []
        duration = 300
        t_pos = report.target_pos

        if report.has_torch_burnout:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.RED, "TORCH BURNOUT HAZARD", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), f"⚡ 烧毁高危 (信号: {report.signal_strength})", SpatialColor.RED, duration))
        elif report.has_weak_power_blockade:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.ORANGE, "WEAK POWER BLOCKADE", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "✖ 弱充能阻断点", SpatialColor.ORANGE, duration))
        elif report.has_wire_redirection_disconnection:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.YELLOW, "WIRE REDIRECTED", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "↷ 偏转断路线路", SpatialColor.YELLOW, duration))
        elif report.has_observer_loop:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.CYAN, "OBSERVER LOOP", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "⟳ 侦测器自激时钟", SpatialColor.CYAN, duration))
        else:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.GREEN, "HEALTHY TRANSMISSION", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), f"✓ 传输正常 (信号: {report.signal_strength})", SpatialColor.GREEN, duration))

        for b_pos in report.burnout_torches:
            primitives.append(SpatialPrimitive.box_outline(b_pos, SpatialColor.RED, "BURNOUT TORCH", duration))
            primitives.append(SpatialPrimitive.billboard(b_pos.offset("up"), "⚠ 火把自激烧毁高危", SpatialColor.RED, duration))

        for w_pos in report.weak_power_blockades:
            primitives.append(SpatialPrimitive.box_outline(w_pos, SpatialColor.ORANGE, "WEAK POWER", duration))
            primitives.append(SpatialPrimitive.billboard(w_pos.offset("up"), "✖ 弱充能：火把不熄灭/导线不供电", SpatialColor.ORANGE, duration))

        for r_pos in report.redirected_wires:
            primitives.append(SpatialPrimitive.box_outline(r_pos, SpatialColor.YELLOW, "REDIRECTED WIRE", duration))
            primitives.append(SpatialPrimitive.flow_arrow(r_pos, t_pos, SpatialColor.YELLOW, "REDIRECTED DISCONNECTED", duration))
            primitives.append(SpatialPrimitive.billboard(r_pos.offset("up"), "↷ 导线偏转脱离目标", SpatialColor.YELLOW, duration))

        for o_pos in report.observer_loops:
            primitives.append(SpatialPrimitive.box_outline(o_pos, SpatialColor.CYAN, "OBSERVER OSCILLATION", duration))
            primitives.append(SpatialPrimitive.billboard(o_pos.offset("up"), "⟳ 1-Clock 自激震荡", SpatialColor.CYAN, duration))

        return SpatialDirectivePacket(
            id=f"redstone-transmission-{int(time.time()*1000)}",
            category="REDSTONE_TRANSMISSION",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )

    @classmethod
    def generate_logic_overlay(cls, cluster: Optional[Any], report: Optional[Any]) -> SpatialDirectivePacket:
        if not report:
            return SpatialDirectivePacket.empty()

        primitives = []
        duration = 300
        t_pos = report.target_pos

        if report.has_race_conflict:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.RED, "LATCH RACE CONFLICT", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "⚠ 锁存器竞争冲突 (S=1, R=1)", SpatialColor.RED, duration))
        elif report.has_pulse_width_mismatch:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.YELLOW, "PULSE WIDTH MISMATCH", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "⚠ 脉冲>2gt 活塞无法吐方块", SpatialColor.YELLOW, duration))
        elif report.has_bulb_lock:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.ORANGE, "BULB LOCKED", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "💡 铜球未断电锁定", SpatialColor.ORANGE, duration))
        elif report.has_glitch_risk:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.YELLOW, "GATE GLITCH RISK", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "↷ 门电路延时毛刺高危", SpatialColor.YELLOW, duration))
        else:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.GREEN, "LOGIC HEALTHY", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), f"✓ 逻辑正常 (输出: {'ON' if report.output_state else 'OFF'})", SpatialColor.GREEN, duration))

        for c_pos in report.conflict_nodes:
            primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.RED, "CONFLICT NODE", duration))
            primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "✖ 冲突节点", SpatialColor.RED, duration))

        for a_pos in report.active_outputs:
            primitives.append(SpatialPrimitive.box_outline(a_pos, SpatialColor.CYAN, "ACTIVE OUTPUT", duration))
            primitives.append(SpatialPrimitive.billboard(a_pos.offset("up"), "⚡ 激活输出 Q=1", SpatialColor.CYAN, duration))

        for l_pos in report.logic_components:
            if l_pos != t_pos and l_pos not in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(l_pos, SpatialColor.BLUE, "LOGIC COMPONENT", duration))

        return SpatialDirectivePacket(
            id=f"redstone-logic-{int(time.time()*1000)}",
            category="REDSTONE_LOGIC",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )

    @staticmethod
    def generate_rail_overlay(cluster: Optional[Any], report: Any) -> SpatialDirectivePacket:
        if not report:
            return SpatialDirectivePacket.empty("rail-empty", "RAIL_NETWORK")

        primitives: List[SpatialPrimitive] = []
        duration = 300
        t_pos = report.target_pos

        # 1. Missing Backstop
        if report.has_missing_backstop:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.RED, "MISSING BACKSTOP", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "✖ 站台缺失挡板：静止矿车无法起动", SpatialColor.RED, duration))
            for g_pos in report.ghost_block_placements:
                primitives.append(SpatialPrimitive.ghost_block(g_pos, "minecraft:stone", color=SpatialColor.CYAN, duration_ticks=duration))
                primitives.append(SpatialPrimitive.billboard(g_pos.offset("up"), "➕ 补全坚固挡板", SpatialColor.CYAN, duration))

        # 2. Slope Stall Risk
        if report.has_slope_stall_risk:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.YELLOW, "SLOPE STALL RISK", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "⚠ 坡道动力不足：普通铁轨连续≥2格", SpatialColor.YELLOW, duration))

        # 3. Activator Lockout
        if report.has_activator_lockout:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.PURPLE, "ACTIVATOR LOCKOUT", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "⚠ 激活铁轨导致漏斗矿车停止吸物", SpatialColor.PURPLE, duration))

        # 4. Unloader Glitch Risk
        if report.has_unloader_glitch_risk:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.ORANGE, "UNLOADER GLITCH RISK", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "↷ 卸货站无延时滤波", SpatialColor.ORANGE, duration))

        # 5. Healthy rail components
        if report.is_healthy:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.GREEN, "RAIL HEALTHY", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "✔ 铁轨动力/站台配置健康", SpatialColor.GREEN, duration))

        # 6. Other rail components
        for r_pos in report.rail_components:
            if r_pos != t_pos and r_pos not in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(r_pos, SpatialColor.BLUE, "RAIL COMPONENT", duration))

        return SpatialDirectivePacket(
            id=f"rail-network-{int(time.time()*1000)}",
            category="RAIL_NETWORK",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )

    @staticmethod
    def generate_water_overlay(cluster: LocalMachineCluster, report: Any) -> SpatialDirectivePacket:
        if not report or not cluster:
            return SpatialDirectivePacket.empty()

        primitives = []
        duration = 300
        t_pos = report.target_pos

        # 1. Broken Bubble Column
        if report.has_broken_bubble_column:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.RED, "BROKEN BUBBLE COLUMN", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "✖ 气泡柱中断：此处为流动水而非水源", SpatialColor.RED, duration))
            for g_pos in report.ghost_block_placements:
                primitives.append(SpatialPrimitive.ghost_block(g_pos, "minecraft:kelp", color=SpatialColor.CYAN, duration_ticks=duration))
                primitives.append(SpatialPrimitive.billboard(g_pos.offset("up"), "➕ 种植海带转化为水源", SpatialColor.CYAN, duration))

        # 2. Top Spill Deflector
        if report.has_top_spill_risk:
            for g_pos in report.ghost_block_placements:
                primitives.append(SpatialPrimitive.box_outline(g_pos, SpatialColor.YELLOW, "TOP SPILL DEFLECTOR", duration))
                primitives.append(SpatialPrimitive.ghost_block(g_pos, "minecraft:smooth_stone_slab", color=SpatialColor.YELLOW, duration_ticks=duration))
                primitives.append(SpatialPrimitive.billboard(g_pos.offset("up"), "⚠ 补全导流顶盖防飞溅", SpatialColor.YELLOW, duration))

        # 3. Flow Stall Risk
        if report.has_flow_stall_risk:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.ORANGE, "FLOW STALL RISK", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "⚠ 水流动力衰竭：超出8格流动极限", SpatialColor.ORANGE, duration))

        # 4. Misaligned Item Stream
        if report.has_misaligned_stream:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.PURPLE, "MISALIGNED ITEM STREAM", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "⚠ 物品未对齐：双漏斗无法满速吞吐", SpatialColor.PURPLE, duration))
            for g_pos in report.ghost_block_placements:
                primitives.append(SpatialPrimitive.ghost_block(g_pos, "minecraft:honey_block", color=SpatialColor.GREEN, duration_ticks=duration))
                primitives.append(SpatialPrimitive.billboard(g_pos.offset("up"), "➕ 放置蜂蜜块对齐双漏斗", SpatialColor.GREEN, duration))

        # 5. Despawn Vortex Risk
        if report.has_despawn_vortex_risk:
            for c_pos in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(c_pos, SpatialColor.RED, "DESPAWN VORTEX RISK", duration))
                primitives.append(SpatialPrimitive.billboard(c_pos.offset("up"), "✖ 涡流对冲死角：物品将滞留5分钟后清除", SpatialColor.RED, duration))

        # 6. Healthy water components
        if report.is_healthy:
            primitives.append(SpatialPrimitive.box_outline(t_pos, SpatialColor.GREEN, "WATER LOGISTICS HEALTHY", duration))
            primitives.append(SpatialPrimitive.billboard(t_pos.offset("up"), "✔ 水流/气泡柱物流动力健康", SpatialColor.GREEN, duration))

        # 7. Other water components
        for w_pos in report.water_components:
            if w_pos != t_pos and w_pos not in report.conflict_nodes:
                primitives.append(SpatialPrimitive.box_outline(w_pos, SpatialColor.BLUE, "WATER STREAM", duration))

        return SpatialDirectivePacket(
            id=f"water-logistics-{int(time.time()*1000)}",
            category="WATER_LOGISTICS",
            primitives=primitives,
            hud_title=report.primary_diagnosis,
            hud_description=report.actionable_advice
        )
