"""
Throughput & Bottleneck Analyzer for Minecraft Logistics and Automation (Python simulation).
Calculates transfer rates, deficits, bottleneck warnings, and scaling optimizations.
"""
from dataclasses import dataclass
import math

HOPPER_TRANSFER_RATE = 2.5       # 8 game ticks (0.4s) per item transfer
HOPPER_MINECART_RATE = 20.0     # 1 item per game tick (0.05s) through solid block
WATER_ICE_STREAM_RATE = 32.0    # Continuous water flow on ice
DROPPER_HIGH_FREQ_RATE = 10.0   # 2-tick observer pulse clock dropper

REGULAR_FURNACE_RATE = 0.1      # 200 game ticks (10.0s) per smelt
BLAST_FURNACE_RATE = 0.2        # 100 game ticks (5.0s) per smelt
SMOKER_RATE = 0.2               # 100 game ticks (5.0s) per smelt

@dataclass(frozen=True)
class PipelineReport:
    system_name: str
    machine_count: int
    machine_item_rate: float
    total_demand_rate: float
    transport_type: str
    supply_capacity_rate: float
    has_bottleneck: bool
    deficit_percentage: float
    max_supported_machines: int
    diagnosis: str
    optimization_advice: str

    def format_report(self) -> str:
        lines = [
            f"§6【工业物流流水线吞吐诊断：{self.system_name}】§r",
            f"▸ §7阵列规模§r：{self.machine_count} 台设备 | 单台消耗: {self.machine_item_rate:.2f} items/s | 总需求: §e{self.total_demand_rate:.2f} items/s§r",
            f"▸ §b供料管线§r：{self.transport_type} | 最大供料速率: §{'c' if self.has_bottleneck else 'a'}{self.supply_capacity_rate:.2f} items/s§r"
        ]
        if self.has_bottleneck:
            lines.append(f"▸ §c⚠️ 瓶颈告警§r：严重供料赤字！缺口达到 §c{self.deficit_percentage:.1f}%§r，主干管道无法承载！")
            lines.append(f"  当前管网最多仅能支撑 §e{self.max_supported_machines} 台§r 设备满载运转，其余 {self.machine_count - self.max_supported_machines} 台将陷入周期性断料停摆。")
            lines.append(f"▸ §a优化方案§r：{self.optimization_advice}")
        else:
            spare = self.supply_capacity_rate - self.total_demand_rate
            margin = (self.supply_capacity_rate / self.total_demand_rate - 1.0) * 100.0
            lines.append(f"▸ §a✔ 物流充盈§r：供料充足！吞吐冗余度 +{margin:.1f}% (余量 +{spare:.2f} items/s)。")
            lines.append(f"  当前供料系统最高可拓展支撑至 §e{self.max_supported_machines} 台§r 设备满载运转。")
            lines.append(f"▸ §e工程提示§r：{self.optimization_advice}")
        return "\n".join(lines)

def analyze_smelting_array(furnace_count: int, furnace_type: str = "furnace", transport_type: str = "hopper") -> PipelineReport:
    count = max(1, furnace_count)
    f_lower = (furnace_type or "furnace").lower()
    t_lower = (transport_type or "hopper").lower()

    if "blast" in f_lower or "高炉" in f_lower:
        machine_rate = BLAST_FURNACE_RATE
        name = "高炉冶炼阵列 (2x极速)"
    elif "smoker" in f_lower or "烟熏" in f_lower:
        machine_rate = SMOKER_RATE
        name = "烟熏炉烹饪阵列 (2x极速)"
    else:
        machine_rate = REGULAR_FURNACE_RATE
        name = "普通熔炉阵列"

    total_demand = count * machine_rate

    if "dual" in t_lower or "双漏斗" in t_lower:
        supply_rate = HOPPER_TRANSFER_RATE * 2.0
        t_desc = "双漏斗对称并联 (5.0 items/s)"
    elif "minecart" in t_lower or "矿车" in t_lower:
        supply_rate = HOPPER_MINECART_RATE
        t_desc = "漏斗矿车穿透极速分流 (20.0 items/s)"
    elif "water" in t_lower or "水流" in t_lower or "冰道" in t_lower:
        supply_rate = WATER_ICE_STREAM_RATE
        t_desc = "水流浮冰高速通道 (32.0 items/s)"
    elif "dropper" in t_lower or "投掷器" in t_lower:
        supply_rate = DROPPER_HIGH_FREQ_RATE
        t_desc = "侦测器双频投掷器 (10.0 items/s)"
    else:
        supply_rate = HOPPER_TRANSFER_RATE
        t_desc = "单漏斗传输 (2.5 items/s)"

    bottleneck = supply_rate < total_demand
    deficit = ((total_demand - supply_rate) / total_demand * 100.0) if bottleneck else 0.0
    max_supported = math.floor(supply_rate / machine_rate)

    if bottleneck:
        if "hopper" in t_lower and "dual" not in t_lower:
            advice = "单漏斗 2.5/s 上限锁死！建议升级为【双漏斗对称推入】(支持 25 台高炉) 或部署【漏斗矿车来回巡回分流】(支持 100 台高炉)。"
        elif "dual" in t_lower:
            advice = "双漏斗 5.0/s 已饱和！建议改用【顶部漏斗矿车站】穿透下料或【水流冰道投掷器批量分流】。"
        else:
            advice = "建议将阵列拆分为独立的双路对称单元，或增加前置缓冲分配箱。"
    else:
        advice = "当前物流供料处于完全健康区间，下层出料口漏斗排空速率建议同步匹配，避免出料堵塞。"

    return PipelineReport(
        system_name=name,
        machine_count=count,
        machine_item_rate=machine_rate,
        total_demand_rate=total_demand,
        transport_type=t_desc,
        supply_capacity_rate=supply_rate,
        has_bottleneck=bottleneck,
        deficit_percentage=deficit,
        max_supported_machines=int(max_supported),
        diagnosis="SUPPLY_BOTTLENECK" if bottleneck else "THROUGHPUT_HEALTHY",
        optimization_advice=advice
    )
