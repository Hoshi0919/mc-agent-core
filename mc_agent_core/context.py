from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math


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

    def to_summary(self) -> str:
        if self.is_air:
            return "None (Looking at air / open sky)"
        tool = self.required_tool if self.required_tool else "None"
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

    def get_nether_equivalent_coords(self) -> tuple[int, int, int]:
        return (math.floor(self.x / 8.0), self.block_y, math.floor(self.z / 8.0))

    def get_overworld_equivalent_coords(self) -> tuple[int, int, int]:
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
        if self.active_effects:
            lines.append(f"Active Effects: {', '.join(self.active_effects)}")
        env_state = "Night" if self.is_night else "Day"
        lines.append(f"Environment: TimeTicks={self.time_of_day_ticks} ({env_state}) | Rain={self.is_raining} | Thunder={self.is_thundering}")
        if self.target_block:
            lines.append(f"Target Block: {self.target_block.to_summary()}")
        lines.append("</player_context>")
        return "\n".join(lines)
