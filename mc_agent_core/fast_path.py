from dataclasses import dataclass
from typing import Optional
from .context import ContextSnapshot
from .rules import LocalGameRules, NETHER_PORTAL_RULES


@dataclass(frozen=True)
class Resolution:
    text_response: str
    suggested_command: Optional[str]
    category: str


class FastPathResolver:
    @staticmethod
    def try_resolve(raw_query: str, context: Optional[ContextSnapshot]) -> Optional[Resolution]:
        if not raw_query or not raw_query.strip():
            return None
        q = raw_query.strip().lower()

        # 1. Nether Portal / Coordinate math
        if any(k in q for k in ("地狱坐标", "下界坐标", "传送门坐标", "对应坐标", "换算坐标")):
            return FastPathResolver._resolve_coordinates(context)

        # 2. Ore depth distribution lookup
        if any(k in q for k in ("在几层", "在第几层", "层数", "在哪挖", "矿石分布", "高度", "怎么挖")):
            ore = LocalGameRules.find_ore(q)
            if ore:
                resp = (
                    f"§6【{ore.name} 生成高度指南 (1.18+)】§r\n"
                    f"▸ 高度区间：Y={ore.min_y} 至 Y={ore.max_y}\n"
                    f"▸ 最优层数：§aY={ore.optimal_y}§r\n"
                    f"▸ 提示：{ore.notes}"
                )
                cmd = f"/waypoint add {ore.name.split()[0]} Y={ore.optimal_y}"
                return Resolution(text_response=resp, suggested_command=cmd, category="ORE_LOOKUP")

        # 3. Mob spawning & light level check
        if "不刷怪" in q or ("刷怪" in q and any(k in q for k in ("亮度", "条件", "为什么", "怎么", "不生成"))):
            lines = ["§b【1.18+ 敌对生物刷怪判定】§r"]
            if context and context.target_block and not context.target_block.is_air:
                tb = context.target_block
                lines.append(
                    f"▸ 您当前注视方块：[{tb.x}, {tb.y}, {tb.z}] | 方块光照：{tb.block_light} | 天空光照：{tb.sky_light}"
                )
                if tb.block_light > 0:
                    lines.append(
                        f"▸ §c注意：当前方块光照为 {tb.block_light} (>=1)，由于 1.18+ 规定方块光照必须为 0，此处绝不可能自然刷怪！§r"
                    )
                else:
                    lines.append("▸ 当前方块光照为 0，满足光照刷怪条件（需检查周围 24~128 格玩家距离及生物群系限制）。")
            else:
                lines.append("▸ 1.18+ 规则：方块内部【方块光照 (Block Light) 必须为 0】才能生成敌对怪！")
            lines.append("▸ 彻底点亮：任意方块光照 >= 1 即安全；刷怪塔必须做到 0 漏光。")
            return Resolution(text_response="\n".join(lines), suggested_command=None, category="MOB_SPAWN_LIGHT")

        # 4. Netherite upgrade (1.20+)
        if "合金" in q and any(k in q for k in ("怎么", "升级", "模板", "锻造", "做", "合")):
            resp = (
                "§6【下界合金装备升级 (1.20+)】§r\n"
                "▸ 1.20+ 锻造台不可直接合！必须放入三样：\n"
                "  ① §e下界合金升级锻造模板§r（堡垒遗迹宝箱获取）\n"
                "  ② 钻石装备/工具\n"
                "  ③ 下界合金锭\n"
                "▸ §a模板复制秘籍§r：工作台放置 7 个钻石 + 1 个下界岩 + 1 个升级模板 ➔ 复制出 2 个模板！"
            )
            return Resolution(
                text_response=resp,
                suggested_command="/locate structure minecraft:bastion_remnant",
                category="NETHERITE_UPGRADE",
            )

        # 5. Mace / Heavy Core (1.21)
        if any(k in q for k in ("重锤", "mace", "重型核心", "旋风棒")):
            resp = (
                "§d【重锤 (Mace) 制作与机制 (1.21)】§r\n"
                "▸ 合成配方：1 个重型核心 (Heavy Core) + 1 个旋风棒 (Breeze Rod)\n"
                "▸ 获取途径：重型核心仅在试炼密室 (Trial Chamber) 的【不祥宝库】用不祥试炼钥匙开启获得\n"
                "▸ 核心特效：坠落攻击伤害随下落高度倍增，击中目标时完全免疫坠落伤害！"
            )
            return Resolution(
                text_response=resp,
                suggested_command="/locate structure minecraft:trial_chambers",
                category="MACE_1_21",
            )

        # 6. Crafter (1.21)
        if any(k in q for k in ("合成器", "自动合成", "crafter")):
            resp = (
                "§b【自动合成器 (Crafter) 指南 (1.21)】§r\n"
                "▸ 激活方式：需要红石脉冲（如时钟信号或侦测器）触发一次合成。\n"
                "▸ 槽位锁定：右键点击 3x3 槽位可禁用该格，使其不接受漏斗漏入物品。\n"
                "▸ 自动化技巧：通过红石比较器检测槽位填满度，满配方后触发脉冲发射成品。"
            )
            return Resolution(text_response=resp, suggested_command=None, category="CRAFTER_1_21")

        return None

    @staticmethod
    def _resolve_coordinates(ctx: Optional[ContextSnapshot]) -> Resolution:
        if not ctx:
            return Resolution(text_response=NETHER_PORTAL_RULES, suggested_command=None, category="COORDINATES_GENERAL")

        if ctx.is_overworld:
            nx, ny, nz = ctx.get_nether_equivalent_coords()
            text = (
                "§e【主世界 ➔ 下界对应传送门坐标】§r\n"
                f"▸ 当前主界坐标：[{ctx.block_x}, {ctx.block_y}, {ctx.block_z}]\n"
                f"▸ 对应下界坐标：§a[{nx}, {ny}, {nz}]§r (X/8, Z/8)\n"
                "▸ 建议：在下界该精确坐标建门，可避免多门串线干扰！"
            )
            cmd = f"/tp {nx} {ny} {nz}"
            return Resolution(text_response=text, suggested_command=cmd, category="COORDINATES_NETHER")
        elif ctx.is_nether:
            ox, oy, oz = ctx.get_overworld_equivalent_coords()
            text = (
                "§e【下界 ➔ 主世界对应传送门坐标】§r\n"
                f"▸ 当前下界坐标：[{ctx.block_x}, {ctx.block_y}, {ctx.block_z}]\n"
                f"▸ 对应主界坐标：§a[{ox}, {oy}, {oz}]§r (X*8, Z*8)\n"
                "▸ 建议：在主世界该坐标建造地表传送门完成精准链接！"
            )
            cmd = f"/tp {ox} {oy} {oz}"
            return Resolution(text_response=text, suggested_command=cmd, category="COORDINATES_OVERWORLD")
        else:
            text = (
                f"▸ 您当前处于末地 (The End) [{ctx.block_x}, {ctx.block_y}, {ctx.block_z}]，"
                "末地不适用 8:1 下界坐标换算。"
            )
            return Resolution(text_response=text, suggested_command=None, category="COORDINATES_END")
