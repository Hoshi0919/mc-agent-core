"""Anvil Enchantment Prior Work Penalty & Binary Tree Merge Optimizer."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class EnchantmentEntry:
    id: str
    name_zh: str
    max_level: int
    item_multiplier: int
    book_multiplier: int
    target_type: str
    conflicts: Set[str] = field(default_factory=set)

    def conflicts_with(self, other_id: Optional[str]) -> bool:
        if not other_id:
            return False
        return other_id.lower() in self.conflicts

    def is_compatible_with_gear(self, gear_type: Optional[str]) -> bool:
        if not gear_type or self.target_type == "all":
            return True
        g = gear_type.lower()
        if self.target_type == "armor":
            return any(k in g for k in ["helmet", "chestplate", "leggings", "boots", "armor", "头盔", "胸甲", "护腿", "靴子"])
        if self.target_type == "helmet":
            return "helmet" in g or "头盔" in g
        if self.target_type == "chestplate":
            return "chestplate" in g or "胸甲" in g or "elytra" in g or "鞘翅" in g
        if self.target_type == "leggings":
            return "leggings" in g or "护腿" in g
        if self.target_type == "boots":
            return "boots" in g or "靴子" in g
        if self.target_type == "sword":
            return "sword" in g or "剑" in g
        if self.target_type == "tool":
            return any(k in g for k in ["pickaxe", "axe", "shovel", "hoe", "镐", "斧", "锹", "锄"])
        if self.target_type == "bow":
            return "bow" in g or "弓" in g
        if self.target_type == "crossbow":
            return "crossbow" in g or "弩" in g
        if self.target_type == "trident":
            return "trident" in g or "三叉戟" in g
        if self.target_type == "mace":
            return "mace" in g or "重锤" in g
        return True


REGISTRY: Dict[str, EnchantmentEntry] = {}


def _register(id_: str, name_zh: str, max_lvl: int, item_m: int, book_m: int, target: str, *confs: str):
    entry = EnchantmentEntry(id_, name_zh, max_lvl, item_m, book_m, target, set(confs))
    REGISTRY[id_.lower()] = entry
    REGISTRY[name_zh.lower()] = entry


# Swords
_register("sharpness", "锋利", 5, 1, 1, "sword", "smite", "bane_of_arthropods")
_register("smite", "亡灵杀手", 5, 2, 1, "sword", "sharpness", "bane_of_arthropods")
_register("bane_of_arthropods", "节肢杀手", 5, 2, 1, "sword", "sharpness", "smite")
_register("looting", "抢夺", 3, 4, 2, "sword")
_register("sweeping_edge", "横扫之刃", 3, 4, 2, "sword")
_register("fire_aspect", "火焰附加", 2, 4, 2, "sword")
_register("knockback", "击退", 2, 2, 1, "sword")

# Tools
_register("efficiency", "效率", 5, 1, 1, "tool")
_register("fortune", "时运", 3, 4, 2, "tool", "silk_touch")
_register("silk_touch", "精准采集", 1, 8, 4, "tool", "fortune")

# Universal
_register("unbreaking", "耐久", 3, 2, 1, "all")
_register("mending", "经验修补", 1, 4, 2, "all", "infinity")

# Armor
_register("protection", "保护", 4, 1, 1, "armor", "fire_protection", "blast_protection", "projectile_protection")
_register("fire_protection", "火焰保护", 4, 2, 1, "armor", "protection", "blast_protection", "projectile_protection")
_register("blast_protection", "爆炸保护", 4, 4, 2, "armor", "protection", "fire_protection", "projectile_protection")
_register("projectile_protection", "弹射物保护", 4, 2, 1, "armor", "protection", "fire_protection", "blast_protection")
_register("thorns", "荆棘", 3, 8, 4, "armor")

# Boots & Helmet & Leggings
_register("feather_falling", "摔落保护", 4, 2, 1, "boots")
_register("depth_strider", "深海行者", 3, 4, 2, "boots", "frost_walker")
_register("frost_walker", "冰霜行者", 2, 4, 2, "boots", "depth_strider")
_register("soul_speed", "灵魂疾行", 3, 8, 4, "boots")
_register("respiration", "水下呼吸", 3, 4, 2, "helmet")
_register("aqua_affinity", "水下速掘", 1, 4, 2, "helmet")
_register("swift_sneak", "迅捷潜行", 3, 8, 4, "leggings")

# Ranged & Special
_register("power", "力量", 5, 1, 1, "bow")
_register("punch", "冲击", 2, 4, 2, "bow")
_register("flame", "火矢", 1, 4, 2, "bow")
_register("infinity", "无限", 1, 8, 4, "bow", "mending")
_register("quick_charge", "快速装填", 3, 2, 1, "crossbow")
_register("multishot", "多重射击", 1, 4, 2, "crossbow", "piercing")
_register("piercing", "穿透", 4, 1, 1, "crossbow", "multishot")

# Trident & Mace
_register("loyalty", "忠诚", 3, 1, 1, "trident", "riptide")
_register("channeling", "引雷", 1, 8, 4, "trident", "riptide")
_register("riptide", "激流", 3, 4, 2, "trident", "loyalty", "channeling")
_register("impaling", "穿刺", 5, 4, 2, "trident")
_register("wind_burst", "风爆", 3, 4, 2, "mace")
_register("density", "致密", 5, 2, 1, "mace")
_register("breach", "破甲", 4, 4, 2, "mace")


def get_enchantment(key: str) -> Optional[EnchantmentEntry]:
    return REGISTRY.get(key.strip().lower().replace(" ", "_"))


def calculate_penalty(work_count: int) -> int:
    if work_count <= 0:
        return 0
    if work_count >= 30:
        return 1073741823
    return (1 << work_count) - 1


def to_roman(level: int) -> str:
    mapping = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    return mapping.get(level, str(level))


@dataclass
class AnvilItem:
    name: str
    is_gear: bool
    work_count: int
    enchantments: Dict[str, int]

    @property
    def penalty(self) -> int:
        return calculate_penalty(self.work_count)

    def enchant_summary(self) -> str:
        if not self.enchantments:
            return "无附魔"
        parts = []
        for k, v in self.enchantments.items():
            entry = get_enchantment(k)
            name = entry.name_zh if entry else k
            parts.append(f"{name}{to_roman(v)}")
        return "+".join(parts)


@dataclass
class AnvilMergeStep:
    step_number: int
    left_item: str
    right_item: str
    result_item: str
    cost_levels: int
    prior_penalty: int
    result_work_count: int


@dataclass
class AnvilPlan:
    gear_name: str
    steps: List[AnvilMergeStep]
    total_cost_levels: int
    max_step_cost: int
    final_work_count: int
    too_expensive: bool
    warnings: List[str]

    def format_report(self) -> str:
        lines = [f"§6【铁砧附魔合并优化方案：{self.gear_name}】§r"]
        if self.too_expensive:
            lines.append("§c⚠️ 警告：检测到存在单步消耗 >= 40 级，生存模式将提示【过于昂贵！】无法锻造！§r")
        else:
            lines.append("§a✔ 状态：二叉树优化已就绪，所有单步均低于 39 级生存上限！§r")
        final_pen = (1 << self.final_work_count) - 1
        lines.append(f"§7- 合并总步数: {len(self.steps)} 步 | 总等级消耗: {self.total_cost_levels} 级 | 单步最高: {self.max_step_cost} 级 | 最终装备惩罚次数: {self.final_work_count} (惩罚: {final_pen} 级)§r")

        for w in self.warnings:
            lines.append(f"§e- 附魔提示: {w}§r")

        lines.append("§b锻造执行工序：§r")
        for s in self.steps:
            lines.append(f"  §e{s.step_number}.§r 左槽 §f{s.left_item}§r + 右槽 §f{s.right_item}§r ➔ §a{s.result_item}§r §7(消耗: {s.cost_levels} 级)§r")

        return "\n".join(lines)


def _step_cost(target: AnvilItem, sacrifice: AnvilItem) -> int:
    penalty = target.penalty + sacrifice.penalty
    cost = 0
    for k, v in sacrifice.enchantments.items():
        entry = get_enchantment(k)
        mult = (entry.item_multiplier if sacrifice.is_gear else entry.book_multiplier) if entry else 1
        tgt_lvl = target.enchantments.get(k)
        if tgt_lvl is None or tgt_lvl < v:
            cost += v * mult
        elif tgt_lvl == v:
            max_l = entry.max_level if entry else 5
            res_lvl = min(v + 1, max_l)
            cost += res_lvl * mult
        else:
            cost += 1
    return penalty + max(1, cost)


def optimize_anvil_tree(gear_name: str, requested_enchants: Dict[str, int]) -> AnvilPlan:
    warnings = []
    steps = []
    if not requested_enchants:
        return AnvilPlan(gear_name, steps, 0, 0, 0, False, ["未指定任何附魔"])

    ids = list(requested_enchants.keys())
    for i in range(len(ids)):
        eA = get_enchantment(ids[i])
        if eA:
            if not eA.is_compatible_with_gear(gear_name):
                warnings.append(f"附魔 [{eA.name_zh}] 通常不能直接赋予装备 [{gear_name}]")
            for j in range(i + 1, len(ids)):
                if eA.conflicts_with(ids[j]):
                    eB = get_enchantment(ids[j])
                    nameB = eB.name_zh if eB else ids[j]
                    warnings.append(f"冲突警报：[{eA.name_zh}] 与 [{nameB}] 互斥，铁砧无法共存！")

    gear = AnvilItem(gear_name, True, 0, {})
    books: List[AnvilItem] = []

    sorted_enchants = sorted(
        requested_enchants.items(),
        key=lambda it: (get_enchantment(it[0]).book_multiplier if get_enchantment(it[0]) else 1) * it[1],
        reverse=True
    )

    for k, v in sorted_enchants:
        ee = get_enchantment(k)
        name_zh = ee.name_zh if ee else k
        books.append(AnvilItem(f"附魔书({name_zh}{to_roman(v)})", False, 0, {k: v}))

    total_cost = 0
    max_step = 0
    too_exp = False
    step_idx = 1

    queue = list(books)
    while len(queue) > 1:
        b1 = queue.pop(0)
        b2 = queue.pop(0)

        cost = _step_cost(b1, b2)
        total_cost += cost
        max_step = max(max_step, cost)
        if cost >= 40:
            too_exp = True

        new_wc = max(b1.work_count, b2.work_count) + 1
        merged_ench = dict(b1.enchantments)
        merged_ench.update(b2.enchantments)

        res_name = f"复合书({b1.enchant_summary()}+{b2.enchant_summary()})"
        steps.append(AnvilMergeStep(step_idx, b1.name, b2.name, res_name, cost, b1.penalty + b2.penalty, new_wc))
        step_idx += 1

        queue.append(AnvilItem(res_name, False, new_wc, merged_ench))

    if queue:
        final_book = queue.pop(0)
        cost = _step_cost(gear, final_book)
        total_cost += cost
        max_step = max(max_step, cost)
        if cost >= 40:
            too_exp = True

        new_wc = max(gear.work_count, final_book.work_count) + 1
        final_ench = dict(gear.enchantments)
        final_ench.update(final_book.enchantments)

        res_gear = f"神装·{gear_name}"
        steps.append(AnvilMergeStep(step_idx, gear.name, final_book.name, res_gear, cost, gear.penalty + final_book.penalty, new_wc))
        gear.work_count = new_wc

    return AnvilPlan(gear_name, steps, total_cost, max_step, gear.work_count, too_exp, warnings)
