package hoshi.mcagent.format;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Paginates long Q&A texts into multi-page chat views with clickable Minecraft tellraw navigation.
 * Prevents chat screen spamming and ensures optimal readability on Minecraft HUDs.
 */
public final class ChatPaginator {

    public record PagedResult(
            int currentPage,
            int totalPages,
            int pageSize,
            int totalLines,
            List<String> pageLines,
            String fullPageText,
            List<MinecraftTextFormatter.ChatComponent> components,
            String tellrawJson
    ) {}

    public static final int DEFAULT_PAGE_SIZE = 5;
    public static final String DEFAULT_PAGE_CMD_PREFIX = "/mcagent page";

    /**
     * Paginates a multiline text into the requested page.
     */
    public static PagedResult paginate(String rawText, int targetPage, int pageSize, String commandPrefix) {
        if (pageSize <= 0) pageSize = DEFAULT_PAGE_SIZE;
        String prefix = (commandPrefix != null && !commandPrefix.trim().isEmpty())
                ? commandPrefix.trim()
                : DEFAULT_PAGE_CMD_PREFIX;

        List<String> allLines = new ArrayList<>();
        if (rawText != null && !rawText.trim().isEmpty()) {
            String[] split = rawText.split("\\r?\\n");
            allLines.addAll(Arrays.asList(split));
        }

        int totalLines = allLines.size();
        int totalPages = totalLines == 0 ? 1 : (int) Math.ceil((double) totalLines / pageSize);
        int page = Math.max(1, Math.min(targetPage, totalPages));

        int startIdx = (page - 1) * pageSize;
        int endIdx = Math.min(startIdx + pageSize, totalLines);

        List<String> currentLines = (startIdx < totalLines)
                ? allLines.subList(startIdx, endIdx)
                : List.of("§7(本页无内容)§r");

        StringBuilder pageText = new StringBuilder();
        pageText.append(String.format("§b[Hoshi 助手]§7 (第 %d/%d 页)§r\n", page, totalPages));
        for (String line : currentLines) {
            pageText.append(line).append("\n");
        }

        List<MinecraftTextFormatter.ChatComponent> components = new ArrayList<>();
        components.add(new MinecraftTextFormatter.ChatComponent(
                String.format("[Hoshi 助手] (第 %d/%d 页)\n", page, totalPages),
                "aqua",
                true,
                false,
                null,
                null,
                "Minecraft Agent Paged View"
        ));

        for (String line : currentLines) {
            components.add(new MinecraftTextFormatter.ChatComponent(line + "\n", "white", false, false, null, null, null));
        }

        if (totalPages > 1) {
            components.add(new MinecraftTextFormatter.ChatComponent("§8[ ", "dark_gray", false, false, null, null, null));

            // Previous Page Button
            if (page > 1) {
                components.add(new MinecraftTextFormatter.ChatComponent(
                        "◀ 上一页",
                        "aqua",
                        true,
                        false,
                        "RUN_COMMAND",
                        prefix + " " + (page - 1),
                        "点击翻至第 " + (page - 1) + " 页"
                ));
            } else {
                components.add(new MinecraftTextFormatter.ChatComponent(
                        "◀ 上一页",
                        "dark_gray",
                        false,
                        false,
                        null,
                        null,
                        "已是第一页"
                ));
            }

            components.add(new MinecraftTextFormatter.ChatComponent(" §8]  §7[ ", "dark_gray", false, false, null, null, null));
            components.add(new MinecraftTextFormatter.ChatComponent(
                    String.format("第 %d/%d 页", page, totalPages),
                    "yellow",
                    false,
                    false,
                    null,
                    null,
                    String.format("共 %d 行内容", totalLines)
            ));
            components.add(new MinecraftTextFormatter.ChatComponent(" §7]  §8[ ", "dark_gray", false, false, null, null, null));

            // Next Page Button
            if (page < totalPages) {
                components.add(new MinecraftTextFormatter.ChatComponent(
                        "下一页 ▶",
                        "aqua",
                        true,
                        false,
                        "RUN_COMMAND",
                        prefix + " " + (page + 1),
                        "点击翻至第 " + (page + 1) + " 页"
                ));
            } else {
                components.add(new MinecraftTextFormatter.ChatComponent(
                        "下一页 ▶",
                        "dark_gray",
                        false,
                        false,
                        null,
                        null,
                        "已是最后一页"
                ));
            }

            components.add(new MinecraftTextFormatter.ChatComponent(" §8]\n", "dark_gray", false, false, null, null, null));
        }

        String tellraw = TellrawJsonBuilder.toJson(components);
        return new PagedResult(page, totalPages, pageSize, totalLines, currentLines, pageText.toString(), components, tellraw);
    }

    private ChatPaginator() {}
}
