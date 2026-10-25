"""Portal Chunk Loader & Permaloader Dynamics Analyzer."""

from dataclasses import dataclass, field
import math
from typing import List, Optional


@dataclass
class AlignmentResult:
    overworld_x: float
    overworld_y: float
    overworld_z: float
    nether_x: float
    nether_y: float
    nether_z: float
    ideal_nether_x: int
    ideal_nether_z: int
    drift_distance: float
    is_perfect: bool
    is_safe: bool
    is_bleed_risk: bool
    advice: str

    def format_report(self) -> str:
        lines = ["§6【生电下界传送门：8:1 坐标对齐与串门风险诊断】§r"]
        lines.append(f"§7- 主世界坐标: §f({self.overworld_x:.1f}, {self.overworld_y:.1f}, {self.overworld_z:.1f})§7 ➔ 下界理想坐标: §e({self.ideal_nether_x}, ~ , {self.ideal_nether_z})§r")
        lines.append(f"§7- 下界实际坐标: §f({self.nether_x:.1f}, {self.nether_y:.1f}, {self.nether_z:.1f})§7 | 空间漂移误差: §b{self.drift_distance:.2f} 格§r")

        if self.is_perfect:
            lines.append("§a✔ 状态：完美的 1:1 双向绝对严格对称绑定！零串门风险！§r")
        elif self.is_safe:
            lines.append("§e✔ 状态：处于 16 格安全容差圈内，可正常双向互通。§r")
        else:
            lines.append("§c❌ 致命风险：漂移距离超过 16 格，存在严重【单向串门撕裂 (Portal Bleed)】！从下界返回时可能在主世界另行生成新门！§r")

        lines.append(f"§7- 纠正建议: {self.advice}§r")
        return "\n".join(lines)


def evaluate_portal_alignment(ow_x: float, ow_y: float, ow_z: float, n_x: float, n_y: float, n_z: float) -> AlignmentResult:
    ideal_x = math.floor(ow_x / 8.0)
    ideal_z = math.floor(ow_z / 8.0)
    drift = math.hypot(n_x - ideal_x, n_z - ideal_z)
    perfect = drift < 0.001
    safe = drift <= 16.0
    bleed = drift > 16.0

    if perfect:
        advice = "坐标已达极致对齐，无需任何调整。"
    elif safe:
        advice = f"若需规避任何潜在临近门干扰，建议将下界门精确迁至 X={ideal_x}, Z={ideal_z}。"
    else:
        advice = f"强烈建议立即拆毁当前下界门，并精确移动至 X={ideal_x}, Z={ideal_z} 处重新点燃以修复对称拓扑！"

    return AlignmentResult(ow_x, ow_y, ow_z, n_x, n_y, n_z, ideal_x, ideal_z, drift, perfect, safe, bleed, advice)


@dataclass
class PermaloaderReport:
    interval_seconds: float
    transport_type: str
    is_valid: bool
    is_expired: bool
    ticket_ticks_remaining: float
    details: List[str] = field(default_factory=list)

    def format_report(self) -> str:
        lines = ["§6【生电传送门常载网 (Permaloader) 强加载动力学诊断】§r"]
        lines.append(f"§7- 投掷/穿梭周期: §f{self.interval_seconds:.2f} 秒 ({self.interval_seconds * 20.0:.0f} Ticks)§7 | 物流载具: §b{self.transport_type}§r")

        if not self.is_valid:
            lines.append("§c❌ 错误：穿梭周期必须大于 0 秒！§r")
        elif self.is_expired:
            lines.append("§c❌ 致命故障：投掷周期 >= 15.0 秒 (300 Ticks)！Ticket 30 强加载票在实体到达前已彻底过期，常载区块必定卸载死锁！§r")
        else:
            lines.append(f"§a✔ 状态：强加载时钟维持正常！每次穿梭后保留 {self.ticket_ticks_remaining:.1f} Ticks 强加载安全裕度。§r")

        lines.append("§e区块加载范围与层级矩阵：§r")
        lines.append("  §7* §f3x3 区块 (48x48 格)§7: 实体完全运算区 (Entity Ticking, Ticket 30) - 怪物AI/矿车/红石全速运算")
        lines.append("  §7* §f5x5 区块 (80x80 格)§7: 方块红石运算区 (Block Ticking, Ticket 31) - 红石与作物生长，生物AI冻结")
        lines.append("  §7* §f7x7 区块 (112x112 格)§7: 懒惰边界区 (Lazy Chunks, Ticket 32) - 仅常驻内存供寻路，不执行Tick")

        if self.details:
            lines.append("§b生电工程建议：§r")
            for d in self.details:
                lines.append(f"  §7- §f{d}§r")

        return "\n".join(lines)


def analyze_permaloader(interval_seconds: float, transport: str = "hopper_dropper_clock") -> PermaloaderReport:
    if interval_seconds <= 0.0:
        return PermaloaderReport(interval_seconds, transport, False, True, 0.0, ["无效周期"])

    expired = interval_seconds >= 15.0
    remaining = max(0.0, (15.0 - interval_seconds) * 20.0)
    details = []

    if expired:
        details.append("必须将投掷时钟缩短至 15.0 秒以内（生电标准黄金周期：8.0 ~ 12.0 秒），以防服务端 TPS 波动导致加载断流。")
        details.append("下界侧必须配建完备的收集装置或反向投掷回路，严防堆积 70+ 掉落物造成服务器卡顿或 despawn。")
    else:
        if interval_seconds > 12.0:
            details.append("警报：当前周期接近 15.0 秒临界点，一旦出现卡顿掉 Tick，常载票可能偶发断裂，建议优化至 10 秒左右。")
        else:
            details.append("时钟非常稳健，具备充裕的防断流冗余。")
        details.append("崩溃自愈建议：增设侦测器+投掷器自激振荡脉冲，确保服务端重启后能自启动循环。")

    return PermaloaderReport(interval_seconds, transport, True, expired, remaining, details)
