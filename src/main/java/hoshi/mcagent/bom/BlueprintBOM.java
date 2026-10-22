package hoshi.mcagent.bom;

import hoshi.mcagent.format.MinecraftTextFormatter;
import hoshi.mcagent.format.TellrawJsonBuilder;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Bill of Materials (BOM) representation for Minecraft redstone machines, structures, and farms.
 */
public class BlueprintBOM {
    private final String blueprintId;
    private final String title;
    private final int scale;
    private final List<ItemStack> components;
    private final List<ItemStack> rawMaterials;

    public BlueprintBOM(String blueprintId, String title, int scale, List<ItemStack> components, List<ItemStack> rawMaterials) {
        this.blueprintId = Objects.requireNonNull(blueprintId, "blueprintId");
        this.title = Objects.requireNonNull(title, "title");
        this.scale = scale;
        this.components = Collections.unmodifiableList(Objects.requireNonNull(components, "components"));
        this.rawMaterials = rawMaterials != null ? Collections.unmodifiableList(rawMaterials) : Collections.emptyList();
    }

    public String getBlueprintId() {
        return blueprintId;
    }

    public String getTitle() {
        return title;
    }

    public int getScale() {
        return scale;
    }

    public List<ItemStack> getComponents() {
        return components;
    }

    public List<ItemStack> getRawMaterials() {
        return rawMaterials;
    }

    /**
     * Formats into a clean multi-line in-game chat string with section styling.
     */
    public String toFormattedText() {
        StringBuilder sb = new StringBuilder();
        sb.append("§6【").append(title).append(" - 材料清单 (规模: ").append(scale).append(")】§r\n");
        sb.append("§e▸ 核心构件清单：§r\n");
        for (ItemStack item : components) {
            sb.append("  • §b").append(item.getDisplayName()).append("§r: §a").append(item.formatStacks()).append("§r\n");
        }
        if (!rawMaterials.isEmpty()) {
            sb.append("§e▸ 基础原料折算（合成所需）：§r\n");
            for (ItemStack raw : rawMaterials) {
                sb.append("  • §7").append(raw.getDisplayName()).append("§r: §e").append(raw.formatStacks()).append("§r\n");
            }
        }
        return sb.toString().trim();
    }

    /**
     * Converts the BOM into an interactive Vanilla /tellraw JSON with clickable /give suggestions.
     */
    public String toTellrawJson() {
        List<MinecraftTextFormatter.ChatComponent> comps = new ArrayList<>();
        comps.add(new MinecraftTextFormatter.ChatComponent("【" + title + " 材料清单 (x" + scale + ")】\n", "gold", true, false, null, null, null));
        comps.add(new MinecraftTextFormatter.ChatComponent("▸ 核心构件清单（点击填入获取指令）：\n", "yellow", false, false, null, null, null));
        for (ItemStack item : components) {
            String giveCmd = "/give @s " + item.getItemId() + " " + item.getCount();
            comps.add(new MinecraftTextFormatter.ChatComponent("  • ", "gray", false, false, null, null, null));
            comps.add(new MinecraftTextFormatter.ChatComponent(
                    item.getDisplayName() + " x" + item.formatStacks() + "\n",
                    "aqua",
                    false,
                    false,
                    "SUGGEST_COMMAND",
                    giveCmd,
                    "点击填入: " + giveCmd
            ));
        }
        if (!rawMaterials.isEmpty()) {
            comps.add(new MinecraftTextFormatter.ChatComponent("▸ 基础原料折算（合成所需）：\n", "gray", false, false, null, null, null));
            for (ItemStack raw : rawMaterials) {
                comps.add(new MinecraftTextFormatter.ChatComponent("  • " + raw.getDisplayName() + ": " + raw.formatStacks() + "\n", "gray", false, true, null, null, null));
            }
        }
        return TellrawJsonBuilder.toJson(comps);
    }
}
