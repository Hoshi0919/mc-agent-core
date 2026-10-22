from dataclasses import dataclass, field
from typing import Dict, List, Optional
from mc_agent_core.context import InventorySnapshot


@dataclass(frozen=True)
class CraftingRecipe:
    recipe_id: str
    display_name: str
    category: str
    output_count: int
    ingredients: Dict[str, int]
    craft_tip: str


@dataclass(frozen=True)
class IngredientStatus:
    item_id: str
    required_count: int
    current_count: int
    is_sufficient: bool

    @property
    def missing_count(self) -> int:
        return max(0, self.required_count - self.current_count)


@dataclass(frozen=True)
class CraftingReport:
    is_known_recipe: bool
    recipe: Optional[CraftingRecipe]
    is_ready: bool
    max_craftable: int
    ingredient_statuses: List[IngredientStatus]
    formatted_message: str
    suggested_command: Optional[str]


RECIPES: Dict[str, CraftingRecipe] = {
    "hopper": CraftingRecipe(
        "hopper", "漏斗", "REDSTONE", 1,
        {"iron_ingot": 5, "chest": 1},
        "漏斗支持漏斗矿车与全自动物流，铁锭不够可用原木现合箱子"
    ),
    "piston": CraftingRecipe(
        "piston", "普通活塞", "REDSTONE", 1,
        {"planks": 3, "cobblestone": 4, "iron_ingot": 1, "redstone": 1},
        "木板可使用任意原木合成，圆石需使用镐子挖掘"
    ),
    "beacon": CraftingRecipe(
        "beacon", "信标", "UTILITY", 1,
        {"nether_star": 1, "obsidian": 3, "glass": 5},
        "击败凋灵掉落下界之星；基座需由 9~164 块矿物块搭建"
    )
}


class CraftingReadinessChecker:
    @staticmethod
    def evaluate(query: str, inventory: Optional[InventorySnapshot]) -> CraftingReport:
        q = (query or "").lower().replace("minecraft:", "").strip()
        matched = None
        for k, r in RECIPES.items():
            if k in q or r.display_name.lower() in q:
                matched = r
                break

        if not matched:
            return CraftingReport(
                False, None, False, 0, [],
                "§c[Hoshi] 未找到匹配的合成配方。支持查询：漏斗、活塞、信标等。",
                "/hoshi craft hopper"
            )

        statuses: List[IngredientStatus] = []
        all_ready = True
        max_craft = 999999

        for item_id, req in matched.ingredients.items():
            have = 0
            if inventory:
                have = inventory.count_item(item_id)
                if have == 0 and "planks" in item_id:
                    for p in ("oak_planks", "spruce_planks", "birch_planks"):
                        have += inventory.count_item(p)

            ok = have >= req
            if not ok:
                all_ready = False
            craftable = (have // req) if req > 0 else 0
            if craftable < max_craft:
                max_craft = craftable
            statuses.append(IngredientStatus(item_id, req, have, ok))

        if not all_ready:
            max_craft = 0

        if all_ready:
            msg = f"§a✔【材料齐全！可合成 {matched.display_name}】§r\n▸ 可合成：{max_craft} 个\n▸ 提示：{matched.craft_tip}"
        else:
            missing = [f"{st.item_id} (缺少 {st.missing_count})" for st in statuses if not st.is_sufficient]
            msg = f"§c✖【材料不足！无法合成 {matched.display_name}】§r\n▸ 缺少：{', '.join(missing)}\n▸ 提示：{matched.craft_tip}"

        return CraftingReport(True, matched, all_ready, max_craft, statuses, msg, None)
