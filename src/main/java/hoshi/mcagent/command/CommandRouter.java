package hoshi.mcagent.command;

import hoshi.mcagent.McAgentCore;
import hoshi.mcagent.async.AsyncQueryDispatcher;
import hoshi.mcagent.bom.BlueprintBOM;
import hoshi.mcagent.bom.MaterialCalculator;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.context.TargetEntity;
import hoshi.mcagent.crafting.CraftingReadinessChecker;
import hoshi.mcagent.format.ChatPaginator;
import hoshi.mcagent.format.MinecraftTextFormatter;
import hoshi.mcagent.format.TellrawJsonBuilder;
import hoshi.mcagent.session.PlayerSessionManager;

import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ExecutionException;

/**
 * Universal command router and chat trigger handler for in-game /ai or /hoshi commands.
 */
public class CommandRouter {

    private final McAgentCore core;
    private final PlayerSessionManager sessionManager;

    public CommandRouter(McAgentCore core, PlayerSessionManager sessionManager) {
        this.core = Objects.requireNonNull(core, "core");
        this.sessionManager = sessionManager != null ? sessionManager : new PlayerSessionManager();
    }

    public CommandRouter(McAgentCore core) {
        this(core, new PlayerSessionManager());
    }

    public PlayerSessionManager getSessionManager() {
        return sessionManager;
    }

    /**
     * Determines whether a raw public chat message is directed at the AI assistant.
     */
    public boolean isChatTrigger(String rawMessage) {
        if (rawMessage == null) return false;
        String s = rawMessage.trim();
        return s.startsWith("!") || s.startsWith("！") ||
                s.startsWith("?") || s.startsWith("？") ||
                s.toLowerCase().startsWith("@ai ") || s.toLowerCase().startsWith("@hoshi ");
    }

    /**
     * Extracts the clean question string from a chat trigger.
     */
    public String extractChatQuery(String rawMessage) {
        if (rawMessage == null) return "";
        String s = rawMessage.trim();
        if (s.startsWith("!") || s.startsWith("！") || s.startsWith("?") || s.startsWith("？")) {
            return s.substring(1).trim();
        }
        if (s.toLowerCase().startsWith("@ai ")) {
            return s.substring(4).trim();
        }
        if (s.toLowerCase().startsWith("@hoshi ")) {
            return s.substring(7).trim();
        }
        return s;
    }

    /**
     * Routes and executes an in-game command (e.g. "/hoshi ask 怎么合下界合金" or "!怎么合下界合金").
     */
    public CommandResult execute(String playerId, String rawCommand, ContextSnapshot snapshot) {
        if (rawCommand == null || rawCommand.trim().isEmpty()) {
            return CommandResult.unknown("§c请输入有效指令，例如 /hoshi help");
        }

        String input = rawCommand.trim();
        if (input.startsWith("/")) {
            input = input.substring(1).trim();
        }

        // Handle chat triggers if passed directly
        if (isChatTrigger(input)) {
            String q = extractChatQuery(input);
            return handleAsk(playerId, q, snapshot);
        }

        String[] tokens = input.split("\\s+");
        if (tokens.length == 0) {
            return CommandResult.unknown("§c请输入有效指令，例如 /hoshi help");
        }

        int argStart = 0;
        String first = tokens[0].toLowerCase();
        if (first.equals("ai") || first.equals("hoshi")) {
            argStart = 1;
        }

        if (argStart >= tokens.length) {
            return handleHelp();
        }

        String sub = tokens[argStart].toLowerCase();

        switch (sub) {
            case "ask":
            case "q":
            case "query": {
                if (argStart + 1 >= tokens.length) {
                    return CommandResult.error("ASK", "§c请提供提问内容，例如: /hoshi ask 钻石在几层？");
                }
                StringBuilder q = new StringBuilder();
                for (int i = argStart + 1; i < tokens.length; i++) {
                    if (q.length() > 0) q.append(" ");
                    q.append(tokens[i]);
                }
                return handleAsk(playerId, q.toString(), snapshot);
            }
            case "inspect":
            case "scan": {
                return handleInspect(playerId, snapshot);
            }
            case "craft":
            case "recipe": {
                if (argStart + 1 >= tokens.length) {
                    return CommandResult.error("CRAFT", "§c请提供待合成的物品名称，例如: /hoshi craft hopper");
                }
                StringBuilder q = new StringBuilder();
                for (int i = argStart + 1; i < tokens.length; i++) {
                    if (q.length() > 0) q.append(" ");
                    q.append(tokens[i]);
                }
                return handleCraft(playerId, q.toString(), snapshot);
            }
            case "page":
            case "p": {
                if (argStart + 1 >= tokens.length) {
                    return CommandResult.error("PAGE", "§c请指定目标页码，例如: /hoshi page 2");
                }
                try {
                    int page = Integer.parseInt(tokens[argStart + 1]);
                    return handlePage(playerId, page);
                } catch (NumberFormatException e) {
                    return CommandResult.error("PAGE", "§c无效页码: " + tokens[argStart + 1]);
                }
            }
            case "bom":
            case "mat":
            case "material": {
                String blueprint = argStart + 1 < tokens.length ? tokens[argStart + 1] : "sugar_cane";
                int scale = 1;
                if (argStart + 2 < tokens.length) {
                    try {
                        scale = Integer.parseInt(tokens[argStart + 2]);
                    } catch (NumberFormatException ignored) {}
                }
                return handleBOM(playerId, blueprint, scale);
            }
            case "nether":
            case "portal": {
                return handleNether(playerId, tokens, argStart + 1, snapshot);
            }
            case "clear":
            case "reset": {
                sessionManager.clearSession(playerId);
                return CommandResult.success("CLEAR", "§a[Hoshi] 已清空当前会话记忆与翻页缓存。", null, null, null);
            }
            case "stats": {
                return handleStats();
            }
            case "help":
            default: {
                if (sub.equals("help")) {
                    return handleHelp();
                }
                // Fallback: treat unrecognized arguments as question to ask
                StringBuilder q = new StringBuilder();
                for (int i = argStart; i < tokens.length; i++) {
                    if (q.length() > 0) q.append(" ");
                    q.append(tokens[i]);
                }
                return handleAsk(playerId, q.toString(), snapshot);
            }
        }
    }

    private CommandResult handleInspect(String playerId, ContextSnapshot snapshot) {
        if (snapshot == null) {
            return CommandResult.error("INSPECT", "§c[Hoshi] 无法获取当前玩家上下文快照。");
        }

        StringBuilder sb = new StringBuilder();
        sb.append("§b【Hoshi 准星全维环境感知扫描】§r\n");

        boolean hasData = false;
        TargetBlock tb = snapshot.targetBlock();
        if (tb != null && !tb.isAir()) {
            hasData = true;
            TargetBlock.HarvestReport harvest = tb.evaluateHarvest(snapshot.inventory());
            sb.append(String.format("▸ §6注视方块§r：%s at [%d, %d, %d]\n", tb.blockId(), tb.x(), tb.y(), tb.z()));
            sb.append(String.format("  光照：方块=%d, 天空=%d | 硬度: %.1f | 需求工具: %s\n",
                    tb.blockLight(), tb.skyLight(), tb.hardness(), harvest.toolRequirementName()));
            sb.append(String.format("  手持匹配：%s\n", harvest.advice()));

            TargetBlock.LogisticsReport log = tb.evaluateLogisticsOrRedstone();
            if (log.isLogisticsOrRedstone()) {
                sb.append(String.format("  ⚡ §c红石/物流§r：%s | %s\n", log.stateDetails(), log.actionableAdvice()));
            }
        }

        TargetEntity te = snapshot.targetEntity();
        if (te != null) {
            hasData = true;
            sb.append(String.format("▸ §d注视实体§r：%s\n", te.toSummary()));
        }

        if (snapshot.inventory() != null) {
            sb.append(String.format("▸ §e玩家护甲/手持§r：主手=%s | 护甲防御=%d/20 (金装=%b)\n",
                    snapshot.mainHandItem(), snapshot.inventory().totalArmorPoints(), snapshot.inventory().isWearingGoldArmor()));
        }

        if (!hasData) {
            sb.append("▸ §7准星未对准任何方块或实体 (Raycast Miss)。\n");
        }

        String text = sb.toString().trim();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi inspect", text, "INSPECT", paged);
        return CommandResult.success("INSPECT", text, null, paged.tellrawJson(), paged);
    }

    private CommandResult handleCraft(String playerId, String itemName, ContextSnapshot snapshot) {
        var report = CraftingReadinessChecker.evaluate(itemName, snapshot != null ? snapshot.inventory() : null);
        String text = report.formattedMessage();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi craft " + itemName, text, "CRAFT", paged);
        return CommandResult.success("CRAFT", text, report.suggestedCommand(), paged.tellrawJson(), paged);
    }

    private CommandResult handleAsk(String playerId, String question, ContextSnapshot snapshot) {
        // Fast BOM check
        Optional<BlueprintBOM> bomOpt = MaterialCalculator.matchBOM(question);
        if (bomOpt.isPresent()) {
            BlueprintBOM bom = bomOpt.get();
            String formatted = bom.toFormattedText();
            String tellraw = bom.toTellrawJson();
            ChatPaginator.PagedResult paged = ChatPaginator.paginate(formatted, 1, 6, "/hoshi page");
            sessionManager.recordInteraction(playerId, question, formatted, bom.getBlueprintId(), paged);
            return CommandResult.success("BOM", formatted, null, tellraw, paged);
        }

        try {
            AsyncQueryDispatcher.QueryResult res = core.query(playerId, question, snapshot).get();
            if (res.category().equals("RATE_LIMITED")) {
                return CommandResult.throttled(res.rawAnswer());
            }

            ChatPaginator.PagedResult paged = ChatPaginator.paginate(res.rawAnswer(), 1, 6, "/hoshi page");
            sessionManager.recordInteraction(playerId, question, res.rawAnswer(), res.category(), paged);

            return CommandResult.success("ASK", res.rawAnswer(), res.suggestedCommand(), paged.tellrawJson(), paged);
        } catch (InterruptedException | ExecutionException e) {
            return CommandResult.error("ASK", "§c执行查询异常: " + e.getMessage());
        }
    }

    private CommandResult handlePage(String playerId, int page) {
        Optional<ChatPaginator.PagedResult> pagedOpt = sessionManager.getPage(playerId, page);
        if (pagedOpt.isEmpty()) {
            return CommandResult.error("PAGE", "§c当前没有可翻页的内容，请先向助手提问。");
        }
        ChatPaginator.PagedResult paged = pagedOpt.get();
        return CommandResult.success("PAGE", paged.fullPageText(), null, paged.tellrawJson(), paged);
    }

    private CommandResult handleBOM(String playerId, String blueprint, int scale) {
        BlueprintBOM bom = MaterialCalculator.getBOM(blueprint, scale);
        String formatted = bom.toFormattedText();
        String tellraw = bom.toTellrawJson();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(formatted, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "bom " + blueprint, formatted, bom.getBlueprintId(), paged);
        return CommandResult.success("BOM", formatted, null, tellraw, paged);
    }

    private CommandResult handleNether(String playerId, String[] tokens, int offset, ContextSnapshot snapshot) {
        int x = 0, y = 64, z = 0;
        boolean isNether = false;
        if (offset + 2 < tokens.length) {
            try {
                x = Integer.parseInt(tokens[offset]);
                y = Integer.parseInt(tokens[offset + 1]);
                z = Integer.parseInt(tokens[offset + 2]);
                if (snapshot != null) isNether = snapshot.isNether();
            } catch (NumberFormatException e) {
                return CommandResult.error("NETHER", "§c坐标必须为整数: /hoshi nether <x> <y> <z>");
            }
        } else if (snapshot != null) {
            x = snapshot.blockX();
            y = snapshot.blockY();
            z = snapshot.blockZ();
            isNether = snapshot.isNether();
        } else {
            return CommandResult.error("NETHER", "§c请提供坐标或确保处于有效维度内: /hoshi nether <x> <y> <z>");
        }

        if (isNether) {
            int owX = x * 8;
            int owZ = z * 8;
            String msg = String.format("§6【下界 ➔ 主界对应坐标】§r\n▸ 下界 [%d, %d, %d] ➔ 主界 §a[%d, %d, %d]§r (8倍)", x, y, z, owX, y, owZ);
            String cmd = String.format("/tp %d %d %d", owX, y, owZ);
            var comps = MinecraftTextFormatter.parseComponents(msg, cmd);
            String tellraw = TellrawJsonBuilder.toJson(comps);
            return CommandResult.success("NETHER", msg, cmd, tellraw, null);
        } else {
            int nX = (int) Math.floor(x / 8.0);
            int nZ = (int) Math.floor(z / 8.0);
            String msg = String.format("§c【主界 ➔ 下界对应坐标】§r\n▸ 主界 [%d, %d, %d] ➔ 下界 §e[%d, %d, %d]§r (1/8)", x, y, z, nX, y, nZ);
            String cmd = String.format("/tp %d %d %d", nX, y, nZ);
            var comps = MinecraftTextFormatter.parseComponents(msg, cmd);
            String tellraw = TellrawJsonBuilder.toJson(comps);
            return CommandResult.success("NETHER", msg, cmd, tellraw, null);
        }
    }

    private CommandResult handleStats() {
        String cacheStats = core.getCache().getStats().toString();
        int activeSessions = sessionManager.getActiveSessionCount();
        String msg = String.format("§b【Hoshi AI 运行时度量】§r\n▸ 缓存统计: §a%s§r\n▸ 活跃会话数: §e%d§r\n▸ 响应状态: §a正常运行§r",
                cacheStats, activeSessions);
        return CommandResult.success("STATS", msg, null, null, null);
    }

    private CommandResult handleHelp() {
        String text = "§6【Hoshi 智能问答指令帮助】§r\n" +
                "▸ §e/hoshi ask <问题>§r - 咨询游戏机制与攻略\n" +
                "▸ §e/hoshi inspect§r - 扫描准星方块、红石物流状态与实体安全\n" +
                "▸ §e/hoshi craft <物品>§r - 评估背包原料是否满足合成条件及缺失数量\n" +
                "▸ §e/hoshi bom <方案> [数量]§r - 生成材料清单 (BOM)\n" +
                "▸ §e/hoshi page <页码>§r - 翻页长篇内容\n" +
                "▸ §e/hoshi nether [x y z]§r - 换算地狱传送门坐标\n" +
                "▸ §e/hoshi clear§r - 清理会话与翻页缓存\n" +
                "▸ §e/hoshi stats§r - 查看缓存与度量统计\n" +
                "§7公屏输入 '!问题' 也可直接提问。§r";

        var comps = MinecraftTextFormatter.parseComponents(text, "/hoshi help");
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("HELP", text, null, tellraw, null);
    }
}
