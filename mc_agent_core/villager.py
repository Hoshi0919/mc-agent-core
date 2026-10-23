"""
Villager AI dynamics: Iron farm panic timing, bed clearance, and workstation binding.
"""
from dataclasses import dataclass
from enum import Enum


class FarmType(Enum):
    IRON_FARM = "刷铁机 (Iron Farm)"
    BREEDER = "村民繁殖机 (Villager Breeder)"
    TRADING_HALL = "村民交易大厅 (Trading Hall)"


@dataclass
class VillagerReport:
    farm_type: FarmType
    healthy: bool
    issue: str
    solution: str
    formatted_report: str


def diagnose_iron_farm(villager_count: int, has_los_break: bool, has_slept_recently: bool) -> VillagerReport:
    healthy = True
    issue = "运行正常"
    solution = "保持当前配置，注意收集水流防卡。"

    if villager_count < 3:
        healthy = False
        issue = f"村民数量不足（当前 {villager_count} 名，硬性最低需要 3 名）"
        solution = "补充至至少 3 名具有有效床位的村民。"
    elif not has_los_break:
        healthy = False
        issue = "致命缺陷：永恒恐慌失眠 (Permanent Panic Insomnia)！村民 24 小时目视僵尸，无法入睡。"
        solution = "必须设置视线遮挡 (LOS Break)！使用活塞定期遮挡视线、或水流颠簸，让村民每隔数秒能躺下床 1 tick 满足'20分钟内睡过觉'的前置硬性条件！"
    elif not has_slept_recently:
        healthy = False
        issue = "村民在过去 20 分钟内未成功入睡过 (Sleep Timer Expired)。"
        solution = "等待夜晚来临，暂时遮挡僵尸 3 秒让村民躺下一次即可重新激活铁傀儡刷新。"

    lines = [
        "§3【刷铁机恐慌时序与运行诊断】§r",
        f"▸ 村民编组：{villager_count} 名 (要求 ≥ 3 名)",
        f"▸ 视线周期遮断 (LOS Break)：{'§a✔ 已配置§r' if has_los_break else '§c✖ 未配置 (致命失眠停摆)§r'}",
        f"▸ 20分钟内睡眠记录：{'§a✔ 满足§r' if has_slept_recently else '§c✖ 未满足§r'}",
        f"▸ 综合判定：{'§a✔ 运转健康§r' if healthy else '§c✖ 存在故障§r'}",
    ]
    if not healthy:
        lines.append(f"▸ 故障根因：{issue}")
        lines.append(f"▸ 修复方案：{solution}")
    else:
        lines.append(f"▸ 运行建议：{solution}")

    return VillagerReport(FarmType.IRON_FARM, healthy, issue, solution, "\n".join(lines))


def diagnose_breeder(food_count: int, has_unclaimed_beds: bool, ceiling_height: int) -> VillagerReport:
    healthy = True
    issue = "运行正常"
    solution = "村民将在满足意愿后自动交配繁殖。"

    if ceiling_height < 2:
        healthy = False
        issue = f"床头上方净空不足（当前 {ceiling_height} 格，硬性要求至少 2 格净空）"
        solution = "幼年村民必须能在床头方块上跳跃寻路！清除床头上方多余方块，确保至少 2 格完整空气。"
    elif food_count < 3:
        healthy = False
        issue = f"食物意愿储备不足（当前 {food_count}，单次繁殖双方各需 3 面包或 12 胡萝卜）"
        solution = "投喂至少 3 个面包或 12 个胡萝卜/马铃薯。"
    elif not has_unclaimed_beds:
        healthy = False
        issue = "村庄内无多余空闲床位"
        solution = "村民总数不能超过有效床位数，请在安全区增设更多床位。"

    lines = [
        "§d【村民繁殖机结构与意愿诊断】§r",
        f"▸ 床头上方净空：{ceiling_height} 格 ({'§a✔ 合规§r' if ceiling_height >= 2 else '§c✖ 阻挡寻路§r'})",
        f"▸ 食物意愿储量：{food_count} 份 ({'§a✔ 充足§r' if food_count >= 3 else '§c✖ 不足§r'})",
        f"▸ 多余空闲床位：{'§a✔ 充足§r' if has_unclaimed_beds else '§c✖ 缺乏§r'}",
        f"▸ 综合判定：{'§a✔ 具备繁殖条件§r' if healthy else '§c✖ 繁殖停滞§r'}",
    ]
    if not healthy:
        lines.append(f"▸ 故障根因：{issue}")
        lines.append(f"▸ 修复方案：{solution}")
    else:
        lines.append(f"▸ 运行建议：{solution}")

    return VillagerReport(FarmType.BREEDER, healthy, issue, solution, "\n".join(lines))


def diagnose_trading(traded_before: bool, can_reach_workstation: bool) -> VillagerReport:
    healthy = True
    issue = "运行正常"
    solution = "村民每天工作时段至多补货两次。"

    if traded_before and not can_reach_workstation:
        healthy = False
        issue = "职业已锁定 (XP>0)，但村民无法触碰工作台补货！"
        solution = "拆除阻挡方块，确保村民能够贴合工作台方块脚部。"
    elif not traded_before and not can_reach_workstation:
        healthy = False
        issue = "无法转职：未锁定职业且无法寻路至工作台。"
        solution = "将工作台摆放在村民视线与脚部可到达处。"

    lines = [
        "§b【村民交易大厅与工作站诊断】§r",
        f"▸ 交易历史锁定：{'§e已锁定职业 (XP>0)§r' if traded_before else '§7未锁定 (可自由转职)§r'}",
        f"▸ 工作站物理可达：{'§a✔ 可触碰§r' if can_reach_workstation else '§c✖ 路径阻挡§r'}",
        f"▸ 综合判定：{'§a✔ 状态健康§r' if healthy else '§c✖ 存在死锁§r'}",
    ]
    if not healthy:
        lines.append(f"▸ 故障根因：{issue}")
        lines.append(f"▸ 修复方案：{solution}")
    else:
        lines.append(f"▸ 运行建议：{solution}")

    return VillagerReport(FarmType.TRADING_HALL, healthy, issue, solution, "\n".join(lines))
