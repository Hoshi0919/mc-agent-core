package hoshi.mcagent.engine;

import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;

import java.util.Optional;

/**
 * Fast-path resolver that computes answers deterministically in 0ms without calling LLMs.
 * Saves tokens, prevents hallucinations on mathematical/version facts, and keeps TPS unaffected.
 */
public final class FastPathResolver {

    public record Resolution(
            String textResponse,
            String suggestedCommand,
            String category
    ) {}

    public static Optional<Resolution> tryResolve(String rawQuery, ContextSnapshot context) {
        if (rawQuery == null || rawQuery.trim().isEmpty()) {
            return Optional.empty();
        }
        String q = rawQuery.trim().toLowerCase();

        // 1. Nether Portal / Coordinate math
        if (q.contains("地狱坐标") || q.contains("下界坐标") || q.contains("传送门坐标") || q.contains("对应坐标") || q.contains("换算坐标")) {
            return Optional.of(resolveCoordinates(context));
        }

        // 2. Ore depth distribution lookup
        if (q.contains("在几层") || q.contains("在第几层") || q.contains("层数") || q.contains("在哪挖") || q.contains("矿石分布") || q.contains("高度") || q.contains("怎么挖")) {
            LocalGameRules.OreDistribution ore = LocalGameRules.findOre(q);
            if (ore != null) {
                String resp = String.format("§6【%s 生成高度指南 (1.18+)】§r\n" +
                                "▸ 高度区间：Y=%d 至 Y=%d\n" +
                                "▸ 最优层数：§aY=%d§r\n" +
                                "▸ 提示：%s",
                        ore.name(), ore.minY(), ore.maxY(), ore.optimalY(), ore.notes());
                String cmd = String.format("/waypoint add %s Y=%d", ore.name().split(" ")[0], ore.optimalY());
                return Optional.of(new Resolution(resp, cmd, "ORE_LOOKUP"));
            }
        }

        // 3. Mob spawning & light level check (flexible matching for "为什么这里不刷怪", "不刷怪", "刷怪亮度")
        if (q.contains("不刷怪") || (q.contains("刷怪") && (q.contains("亮度") || q.contains("条件") || q.contains("为什么") || q.contains("怎么") || q.contains("不生成")))) {
            StringBuilder sb = new StringBuilder();
            sb.append("§b【1.18+ 敌对生物刷怪判定】§r\n");
            if (context != null && context.targetBlock() != null && !context.targetBlock().isAir()) {
                TargetBlock tb = context.targetBlock();
                sb.append(String.format("▸ 您当前注视方块：[%d, %d, %d] | 方块光照：%d | 天空光照：%d\n",
                        tb.x(), tb.y(), tb.z(), tb.blockLight(), tb.skyLight()));
                if (tb.blockLight() > 0) {
                    sb.append(String.format("▸ §c注意：当前方块光照为 %d (>=1)，由于 1.18+ 规定方块光照必须为 0，此处绝不可能自然刷怪！§r\n", tb.blockLight()));
                } else {
                    sb.append("▸ 当前方块光照为 0，满足光照刷怪条件（需检查周围 24~128 格玩家距离及生物群系限制）。\n");
                }
            } else {
                sb.append("▸ 1.18+ 规则：方块内部【方块光照 (Block Light) 必须为 0】才能生成敌对怪！\n");
            }
            sb.append("▸ 彻底点亮：任意方块光照 >= 1 即安全；刷怪塔必须做到 0 漏光。");
            return Optional.of(new Resolution(sb.toString(), null, "MOB_SPAWN_LIGHT"));
        }

        // 4. Netherite upgrade (1.20+)
        if (q.contains("合金") && (q.contains("怎么") || q.contains("升级") || q.contains("模板") || q.contains("锻造") || q.contains("做") || q.contains("合"))) {
            String resp = "§6【下界合金装备升级 (1.20+)】§r\n" +
                    "▸ 1.20+ 锻造台不可直接合！必须放入三样：\n" +
                    "  ① §e下界合金升级锻造模板§r（堡垒遗迹宝箱获取）\n" +
                    "  ② 钻石装备/工具\n" +
                    "  ③ 下界合金锭\n" +
                    "▸ §a模板复制秘籍§r：工作台放置 7 个钻石 + 1 个下界岩 + 1 个升级模板 ➔ 复制出 2 个模板！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:bastion_remnant", "NETHERITE_UPGRADE"));
        }

        // 5. Mace / Heavy Core (1.21)
        if (q.contains("重锤") || q.contains("mace") || q.contains("重型核心") || q.contains("旋风棒")) {
            String resp = "§d【重锤 (Mace) 制作与机制 (1.21)】§r\n" +
                    "▸ 合成配方：1 个重型核心 (Heavy Core) + 1 个旋风棒 (Breeze Rod)\n" +
                    "▸ 获取途径：重型核心仅在试炼密室 (Trial Chamber) 的【不祥宝库】用不祥试炼钥匙开启获得\n" +
                    "▸ 核心特效：坠落攻击伤害随下落高度倍增，击中目标时完全免疫坠落伤害！";
            return Optional.of(new Resolution(resp, "/locate structure minecraft:trial_chambers", "MACE_1_21"));
        }

        // 6. Crafter (1.21)
        if (q.contains("合成器") || q.contains("自动合成") || q.contains("crafter")) {
            String resp = "§b【自动合成器 (Crafter) 指南 (1.21)】§r\n" +
                    "▸ 激活方式：需要红石脉冲（如时钟信号或侦测器）触发一次合成。\n" +
                    "▸ 槽位锁定：右键点击 3x3 槽位可禁用该格，使其不接受漏斗漏入物品。\n" +
                    "▸ 自动化技巧：通过红石比较器检测槽位填满度，满配方后触发脉冲发射成品。\n";
            return Optional.of(new Resolution(resp, null, "CRAFTER_1_21"));
        }

        return Optional.empty();
    }

    private static Resolution resolveCoordinates(ContextSnapshot ctx) {
        if (ctx == null) {
            return new Resolution(LocalGameRules.NETHER_PORTAL_RULES, null, "COORDINATES_GENERAL");
        }
        if (ctx.isOverworld()) {
            int[] nether = ctx.getNetherEquivalentCoords();
            String text = String.format("§e【主世界 ➔ 下界对应传送门坐标】§r\n" +
                            "▸ 当前主界坐标：[%d, %d, %d]\n" +
                            "▸ 对应下界坐标：§a[%d, %d, %d]§r (X/8, Z/8)\n" +
                            "▸ 建议：在下界该精确坐标建门，可避免多门串线干扰！",
                    ctx.blockX(), ctx.blockY(), ctx.blockZ(), nether[0], nether[1], nether[2]);
            String cmd = String.format("/tp %d %d %d", nether[0], nether[1], nether[2]);
            return new Resolution(text, cmd, "COORDINATES_NETHER");
        } else if (ctx.isNether()) {
            int[] overworld = ctx.getOverworldEquivalentCoords();
            String text = String.format("§e【下界 ➔ 主世界对应传送门坐标】§r\n" +
                            "▸ 当前下界坐标：[%d, %d, %d]\n" +
                            "▸ 对应主界坐标：§a[%d, %d, %d]§r (X*8, Z*8)\n" +
                            "▸ 建议：在主世界该坐标建造地表传送门完成精准链接！",
                    ctx.blockX(), ctx.blockY(), ctx.blockZ(), overworld[0], overworld[1], overworld[2]);
            String cmd = String.format("/tp %d %d %d", overworld[0], overworld[1], overworld[2]);
            return new Resolution(text, cmd, "COORDINATES_OVERWORLD");
        } else {
            return new Resolution(String.format("▸ 您当前处于末地 (The End) [%d, %d, %d]，末地不适用 8:1 下界坐标换算。",
                    ctx.blockX(), ctx.blockY(), ctx.blockZ()), null, "COORDINATES_END");
        }
    }

    private FastPathResolver() {}
}
