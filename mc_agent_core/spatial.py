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
