package hoshi.mcagent.engine;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Authoritative ground truth rules for modern Minecraft (1.18 ~ 1.21.x).
 * Used for instant fast-path resolution and RAG system prompt grounding.
 */
public final class LocalGameRules {

    public record OreDistribution(String name, int minY, int maxY, int optimalY, String notes) {}

    private static final Map<String, OreDistribution> ORE_TABLE = new LinkedHashMap<>();

    static {
        ORE_TABLE.put("diamond", new OreDistribution("钻石 (Diamond)", -64, 16, -58, "1.18+ 深度越深越丰富，推荐在 Y=-58 或 Y=-59 支路挖掘，避开基岩层（-60 以下）。暴露在空气中的概率降低（深板岩洞穴暴率降低，水下或实心岩挖掘效率最高）。"));
        ORE_TABLE.put("iron", new OreDistribution("铁矿 (Iron)", -64, 320, 16, "1.18+ 呈双峰分布：主峰在 Y=16，次峰在高山 Y=232。推荐在风蚀丘陵/高山露天挖掘或地下 Y=16 附近。"));
        ORE_TABLE.put("coal", new OreDistribution("煤炭 (Coal)", 0, 256, 96, "1.18+ 不在 Y=0 以下生成！最佳高度为 Y=96（山地地表大量露天生成）。"));
        ORE_TABLE.put("copper", new OreDistribution("铜矿 (Copper)", -16, 112, 48, "最佳高度 Y=48。在滴水石洞穴（Dripstone Caves）生成量显著提升。"));
        ORE_TABLE.put("ancient_debris", new OreDistribution("远古残骸 (Ancient Debris)", 8, 119, 15, "下界矿石，不会暴露在空气中。主生成带在 Y=8~22，峰值高度在 Y=15（推荐用床爆或TNT横向挖掘）。"));
        ORE_TABLE.put("gold", new OreDistribution("金矿 (Gold)", -64, 32, -16, "普通生物群系中在 Y=-16 附近最多；但在恶地/荒野群系（Badlands），可在 Y=-64 到 Y=256 大量生成！"));
        ORE_TABLE.put("redstone", new OreDistribution("红石 (Redstone)", -64, 16, -58, "与钻石类似，越接近基岩越丰富，Y=-58 浓度最高。"));
        ORE_TABLE.put("lapis", new OreDistribution("青金石 (Lapis Lazuli)", -64, 64, 0, "三角分布，正中心峰值在海平面下方 Y=0 处。"));
    }

    public static Map<String, OreDistribution> getOreTable() {
        return Collections.unmodifiableMap(ORE_TABLE);
    }

    public static OreDistribution findOre(String query) {
        String lower = query.toLowerCase();
        // Priority 1: Multi-char or specific terms to avoid partial substring collisions
        if (lower.contains("远古残骸") || lower.contains("下界合金") || lower.contains("残骸") || lower.contains("debris")) {
            return ORE_TABLE.get("ancient_debris");
        }
        if (lower.contains("钻石") || lower.contains("diamond")) return ORE_TABLE.get("diamond");
        if (lower.contains("青金石") || lower.contains("lapis")) return ORE_TABLE.get("lapis");
        if (lower.contains("红石") || lower.contains("redstone")) return ORE_TABLE.get("redstone");
        if (lower.contains("铁") || lower.contains("iron")) return ORE_TABLE.get("iron");
        if (lower.contains("煤") || lower.contains("coal")) return ORE_TABLE.get("coal");
        if (lower.contains("铜") || lower.contains("copper")) return ORE_TABLE.get("copper");
        if ((lower.contains("金") && !lower.contains("合金")) || lower.contains("gold")) return ORE_TABLE.get("gold");
        if (lower.contains("合金")) return ORE_TABLE.get("ancient_debris");
        return null;
    }

    public static final String MOB_SPAWNING_RULE =
            "【刷怪机制 (1.18+)】\n" +
            "1. 敌对生物自然生成要求【方块内部方块光照 (Block Light) 必须完全为 0】！天空光照 (Sky Light) 在夜晚允许 <= 7。\n" +
            "2. 只要放置火把、红石灯、荧石等光源使方块光照 >= 1，即可彻底杜绝普通怪物生成。\n" +
            "3. 史莱姆在史莱姆区块（Y<40）不受此光照限制；烈焰人与潜影贝刷怪笼有单独机制。";

    public static final String NETHERITE_UPGRADE_RULE =
            "【下界合金升级机制 (1.20+)】\n" +
            "1. 1.20 之后升级下界合金装备必须在锻造台放置 3 样物品：\n" +
            "   - 锻造模板：【下界合金升级锻造模板 (Netherite Upgrade Smithing Template)】\n" +
            "   - 基础装备：钻石工具/护甲\n" +
            "   - 升级材料：下界合金锭 (Netherite Ingot)\n" +
            "2. 模板获取：仅在堡垒遗迹 (Bastion Remnant) 的宝箱中生成（藏宝室宝箱 100% 出现 1 个）。\n" +
            "3. 模板复制：在工作台用 7 个钻石 + 1 个下界岩 + 1 个下界合金升级模板，可复制出 2 个模板。";

    public static final String VERSION_1_21_MECHANICS =
            "【试炼密室与 1.21 核心机制】\n" +
            "1. 重锤 (Mace)：\n" +
            "   - 合成：1 个重型核心 (Heavy Core，试炼密室不祥宝库开启获得) + 1 个旋风棒 (Breeze Rod，旋风人掉落)。\n" +
            "   - 坠落粉碎击：下落时攻击敌人将下落动能转化为伤害（每格坠落增加基础伤害），且成功命中后完全免疫坠落伤害！\n" +
            "2. 自动合成器 (Crafter)：\n" +
            "   - 接收红石脉冲信号时自动读取 3x3 九宫格内的材料并吐出合成成品。\n" +
            "   - 可以右键点击禁用特定格子，用于固定非全满合成表（例如剑、镐、靴子）。\n" +
            "3. 旋风弹 (Wind Charge)：\n" +
            "   - 旋风棒分解或旋风人掉落，右键发射可击退生物、推动拉杆/按钮、实现高跳火箭跳。";

    public static final String NETHER_PORTAL_RULES =
            "【下界传送门换算与链接机制】\n" +
            "1. 水平坐标换算比例为 8:1：主界坐标除以 8 对应下界坐标；下界坐标乘以 8 对应主界坐标。\n" +
            "2. 公式：X_nether = floor(X_overworld / 8), Z_nether = floor(Z_overworld / 8)。高度 Y 不受 8 倍缩放影响。\n" +
            "3. 搜索半径：主界进入下界搜索半径为下界 16 格；下界进入主界搜索半径为主界 128 格。多门串门时需手动在精确对应坐标立门！";

    private LocalGameRules() {}
}
