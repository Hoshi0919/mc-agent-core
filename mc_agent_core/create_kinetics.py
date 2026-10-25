"""Create Mod Stress Capacity & Kinetics Network Analyzer."""

from dataclasses import dataclass, field
import math
from typing import List, Optional


@dataclass
class MachineEntry:
    type: str
    count: int
    rpm: float
    impact_factor: float = 4.0

    def __post_init__(self):
        self.type = self.type.lower()
        self.impact_factor = resolve_impact_factor(self.type)

    @property
    def total_impact(self) -> float:
        return self.impact_factor * self.rpm * self.count


def resolve_impact_factor(machine_type: str) -> float:
    t = machine_type.lower()
    if any(k in t for k in ["crush", "粉碎"]):
        return 8.0
    if any(k in t for k in ["press", "辊压", "冲压"]):
        return 8.0
    if any(k in t for k in ["arm", "机械臂"]):
        return 8.0
    if any(k in t for k in ["mix", "搅拌"]):
        return 4.0
    if any(k in t for k in ["saw", "锯"]):
        return 4.0
    if any(k in t for k in ["mill", "磨盘", "风磨"]):
        return 4.0
    if any(k in t for k in ["drill", "钻头"]):
        return 4.0
    if any(k in t for k in ["pump", "泵"]):
        return 4.0
    if any(k in t for k in ["belt", "带", "齿轮"]):
        return 1.0
    return 4.0


@dataclass
class KineticReport:
    source_name: str
    total_capacity: float
    total_impact: float
    load_factor: float
    is_overstressed: bool
    surplus_su: float
    deficit_su: float
    max_uniform_rpm: float
    recommendations: List[str] = field(default_factory=list)

    def format_report(self) -> str:
        lines = ["§6【Create 机械动力学：应力与转速网络诊断】§r"]
        lines.append(f"§7- 动力源: §f{self.source_name}§7 | 总应力容量: §e{self.total_capacity:.0f} SU§7 | 负载总消耗: §b{self.total_impact:.0f} SU§7 (负载率: §f{self.load_factor:.1f}%§7)§r")

        if self.is_overstressed:
            lines.append(f"§c❌ 致命状态：动力网络已【过载断裂 (Overstressed)】！转速归零停摆！赤字: -{self.deficit_su:.0f} SU§r")
        else:
            lines.append(f"§a✔ 状态正常：动力裕度充沛 (+{self.surplus_su:.0f} SU)，全线稳定运转！§r")

        if self.max_uniform_rpm > 0:
            lines.append(f"§d- 临界全线安全同步转速上限: §f{self.max_uniform_rpm:.1f} RPM§7 (当前最高不可超过此值)§r")

        if self.recommendations:
            lines.append("§e优化与调谐建议：§r")
            for rec in self.recommendations:
                lines.append(f"  §7* §f{rec}§r")

        return "\n".join(lines)


def analyze_create_network(source: str, param: int, machines: Optional[List[MachineEntry]] = None) -> KineticReport:
    s = source.lower()
    if "large_water" in s or "大水轮" in s:
        count = max(1, param)
        capacity = count * 512.0
        label = f"{count}台大型水轮 (512 SU/台 @ 4 RPM)"
    elif "water" in s or "水轮" in s:
        count = max(1, param)
        capacity = count * 256.0
        label = f"{count}台小型水轮 (256 SU/台 @ 8 RPM)"
    elif "windmill" in s or "风车" in s:
        sails = max(8, param)
        units = min(16, sails // 8)
        capacity = units * 512.0
        label = f"风车轴承 ({sails}块帆布, {units}组 @ 16 RPM)"
    elif "steam" in s or "蒸汽" in s:
        level = max(1, min(18, param))
        if level == 1:
            capacity = 2048.0
        elif level == 2:
            capacity = 4096.0
        elif level == 3:
            capacity = 8192.0
        elif level == 4:
            capacity = 16384.0
        elif level <= 9:
            capacity = level * 16384.0
        else:
            capacity = 147456.0 + (level - 9) * 16384.0
        label = f"{level}级蒸汽机锅炉阵列"
    else:
        capacity = max(512.0, float(param))
        label = f"自定义动力网络 ({source}: {capacity:.0f} SU)"

    total_impact = 0.0
    sum_k_times_count = 0.0
    if machines:
        for m in machines:
            total_impact += m.total_impact
            sum_k_times_count += m.impact_factor * m.count

    load_factor = (total_impact / capacity) * 100.0 if capacity > 0 else 999.0
    overstressed = total_impact > capacity
    surplus = max(0.0, capacity - total_impact)
    deficit = max(0.0, total_impact - capacity)
    max_rpm = capacity / sum_k_times_count if sum_k_times_count > 0 else 256.0

    recs = []
    if overstressed:
        recs.append(f"过载断裂警报：总消耗超过容量 {deficit:.0f} SU。建议增设变速齿轮降速（齿轮比 1:2 可减半应力消耗）。")
        if "windmill" in s or "风车" in s:
            needed = math.ceil(deficit / 512.0) * 8
            recs.append(f"扩容方案：为风车追加安装至少 {needed} 块帆布以补齐 {deficit:.0f} SU 缺口。")
        elif "steam" in s or "蒸汽" in s:
            recs.append("扩容方案：增加锅炉水箱容积、提升供水通量（机械泵高速注水）或喂食烈焰饼触发超频！")
        else:
            recs.append(f"扩容方案：并联至少 {math.ceil(deficit / 256.0)} 台水轮以增加基础应力输出。")
    else:
        if load_factor > 80.0:
            recs.append(f"高负载运行警报：当前负载率已达 {load_factor:.1f}%，后续新增设备易诱发过载断裂，请预留至少 20% 缓冲裕度。")
        else:
            recs.append(f"工况极佳：剩余可用裕度 {surplus:.0f} SU，可安全挂载更高转速或接入更多工艺机器。")
        recs.append("齿轮传动法则：大齿轮带动小齿轮 2:1 提速（转速翻倍但应力消耗翻倍），小齿轮带动大齿轮 1:2 降速（转速减半但消耗减半）。")

    return KineticReport(label, capacity, total_impact, load_factor, overstressed, surplus, deficit, max_rpm, recs)
