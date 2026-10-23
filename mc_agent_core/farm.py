"""
Hostile mob spawning dynamics, despawn sphere geometry and monster spawner analyzer.
"""
from dataclasses import dataclass
from enum import Enum


class DespawnZone(Enum):
    NO_SPAWN = ("0~24格绝对禁刷盲区", False, "玩家距离刷怪面过近(<24格)，游戏引擎禁止自然生成敌对生物！请拉开挂机距离。")
    ACTIVE_GOLDEN = ("24~32格黄金高频活动圈", True, "极佳挂机区间！生物生成后立即自由寻路/活动，不触发随机清除，产出效率最高。")
    RANDOM_DESPAWN = ("33~128格随机清除区", True, "生物每tick有1/800几率被清除(半衰期约28s)；必须配套极速水流冲刷或致死摔落井。")
    INSTANT_DESPAWN = (">128格瞬间清除视界", False, "致命失误！生物生成瞬间(>128格)在下一个tick被强制清除，产出彻底为零！")

    def __init__(self, label: str, viable: bool, advice: str):
        self.label = label
        self.viable = viable
        self.advice = advice


@dataclass
class FarmReport:
    distance: float
    zone: DespawnZone
    caves_lit: bool
    mob_cap_risk: bool
    height_advantage_ratio: float
    formatted_report: str


@dataclass
class SpawnerReport:
    player_distance: float
    block_light: int
    player_in_range: bool
    light_suppressed: bool
    active: bool
    formatted_report: str


def evaluate_mob_farm(afk_y: float, farm_y: float, caves_lit: bool = False) -> FarmReport:
    dist = abs(afk_y - farm_y)
    if dist < 24.0:
        zone = DespawnZone.NO_SPAWN
    elif dist <= 32.0:
        zone = DespawnZone.ACTIVE_GOLDEN
    elif dist <= 128.0:
        zone = DespawnZone.RANDOM_DESPAWN
    else:
        zone = DespawnZone.INSTANT_DESPAWN

    mob_cap_risk = not caves_lit and (zone in (DespawnZone.ACTIVE_GOLDEN, DespawnZone.RANDOM_DESPAWN))

    current_span = max(10.0, 320.0 - farm_y)
    baseline_span = 320.0 - 64.0
    height_advantage_ratio = round((baseline_span / current_span), 2)

    lines = [
        "§4【敌对生物生成动力学与清除球诊断】§r",
        f"▸ 挂机垂直净距：{dist:.1f} 格 (挂机 Y={afk_y:.0f}, 平台 Y={farm_y:.0f})",
        f"▸ 清除球区间判定：{zone.label}",
        f"▸ 区域力学评估：{zone.advice}",
    ]
    if mob_cap_risk:
        lines.append("▸ §c⚠️ 敌对生物上限告警§r：周边128格未完全点亮！70只敌对生物Cap将被地下洞穴怪物迅速占满，导致平台断崖式停产！建议高空挂机或点亮128格矿洞。")
    elif caves_lit:
        lines.append("▸ §a✔ 洞穴压制状态良好§r：周围128格已有效点亮，70生物Cap全额倾斜至刷怪平台。")

    if height_advantage_ratio > 1.2:
        lines.append(f"▸ §e基岩低Y轴优势§r：当前高度抽样效率为常规地表的 {height_advantage_ratio:.2f} 倍！")

    return FarmReport(dist, zone, caves_lit, mob_cap_risk, height_advantage_ratio, "\n".join(lines))


def evaluate_spawner(player_dist: float, block_light: int) -> SpawnerReport:
    in_range = player_dist <= 16.0
    suppressed = block_light >= 11
    active = in_range and not suppressed

    lines = [
        "§6【刷怪笼激活与光照压制诊断】§r",
        f"▸ 玩家距离：{player_dist:.1f} 格 ({'§a≤16格 激活范围内§r' if in_range else '§c>16格 超出范围休眠§r'})",
        f"▸ 方块光照：{block_light} 级 ({'§a≥11级 彻底熄灭压制§r' if suppressed else '§e<11级 允许生成§r'})",
    ]
    if not in_range:
        lines.append("▸ §c状态：休眠§r。刷怪笼内旋转模型停止，无火焰粒子，玩家必须靠近至 16 格以内。")
    elif suppressed:
        lines.append("▸ §a状态：安全熄灭§r。高光照已彻底破坏生成条件，无怪物生成。")
    else:
        lines.append("▸ §e状态：活跃生成中§r！建议底部铺设流水快速冲离 9x9x3 检查盒，防止同类实体达到 6 只导致生成暂停。")

    return SpawnerReport(player_dist, block_light, in_range, suppressed, active, "\n".join(lines))
