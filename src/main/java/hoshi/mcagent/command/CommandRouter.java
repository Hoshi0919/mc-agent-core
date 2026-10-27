package hoshi.mcagent.command;

import hoshi.mcagent.cluster.BlockPos;
import hoshi.mcagent.spatial.SpatialDirectiveGenerator;
import hoshi.mcagent.spatial.SpatialDirectivePacket;
import hoshi.mcagent.McAgentCore;
import hoshi.mcagent.async.AsyncQueryDispatcher;
import hoshi.mcagent.multiblock.MultiblockBlueprint;
import hoshi.mcagent.multiblock.MultiblockValidator;
import hoshi.mcagent.pipeline.PipelineThroughputAnalyzer;
import hoshi.mcagent.farm.MobFarmDynamics;
import hoshi.mcagent.villager.VillagerDynamics;
import hoshi.mcagent.anvil.AnvilOptimizer;
import hoshi.mcagent.anvil.AnvilPlan;
import hoshi.mcagent.create.CreateKineticsAnalyzer;
import hoshi.mcagent.chunkload.PortalChunkLoaderAnalyzer;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.ArrayList;
import hoshi.mcagent.bom.BlueprintBOM;
import hoshi.mcagent.bom.MaterialCalculator;
import hoshi.mcagent.context.ContextSnapshot;
import hoshi.mcagent.context.TargetBlock;
import hoshi.mcagent.cluster.KineticNetworkAnalyzer;
import hoshi.mcagent.cluster.HopperNetworkAnalyzer;
import hoshi.mcagent.cluster.CrafterPipelineAnalyzer;
import hoshi.mcagent.cluster.LocalMachineCluster;
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
            case "multiblock":
            case "mb": {
                String bpName = argStart + 1 < tokens.length ? tokens[argStart + 1] : "conduit";
                return handleMultiblock(playerId, bpName, snapshot);
            }
            case "pipeline":
            case "pipe": {
                String machine = argStart + 1 < tokens.length ? tokens[argStart + 1] : "furnace";
                int count = 16;
                if (argStart + 2 < tokens.length) {
                    try {
                        count = Integer.parseInt(tokens[argStart + 2]);
                    } catch (NumberFormatException ignored) {}
                }
                String transport = argStart + 3 < tokens.length ? tokens[argStart + 3] : "hopper";
                return handlePipeline(playerId, machine, count, transport);
            }
            case "mobfarm":
            case "mf": {
                double afkY = 120.0;
                double farmY = 64.0;
                boolean cavesLit = false;
                if (argStart + 1 < tokens.length) {
                    try { afkY = Double.parseDouble(tokens[argStart + 1]); } catch (NumberFormatException ignored) {}
                }
                if (argStart + 2 < tokens.length) {
                    try { farmY = Double.parseDouble(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
                }
                if (argStart + 3 < tokens.length) {
                    cavesLit = Boolean.parseBoolean(tokens[argStart + 3]) || tokens[argStart + 3].equalsIgnoreCase("true") || tokens[argStart + 3].equals("1");
                }
                return handleMobFarm(playerId, afkY, farmY, cavesLit);
            }
            case "spawner": {
                double dist = 10.0;
                int light = 0;
                if (argStart + 1 < tokens.length) {
                    try { dist = Double.parseDouble(tokens[argStart + 1]); } catch (NumberFormatException ignored) {}
                }
                if (argStart + 2 < tokens.length) {
                    try { light = Integer.parseInt(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
                }
                return handleSpawner(playerId, dist, light);
            }
            case "villager":
            case "v": {
                String type = argStart + 1 < tokens.length ? tokens[argStart + 1] : "iron";
                return handleVillager(playerId, type, tokens, argStart);
            }
            case "anvil":
            case "enchant": {
                return handleAnvil(playerId, tokens, argStart);
            }
            case "create":
            case "kinetics": {
                return handleCreate(playerId, tokens, argStart);
            }
            case "chunkloader":
            case "cl": {
                return handleChunkloader(playerId, tokens, argStart);
            }
            case "cluster":
            case "topo": {
                return handleCluster(playerId, tokens, argStart, snapshot);
            }
            case "highlight":
            case "hl": {
                return handleHighlight(playerId, tokens, argStart, snapshot);
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

        if (snapshot.machineCluster() != null && !snapshot.machineCluster().isEmpty()) {
            hasData = true;
            sb.append(String.format("▸ §e机器拓扑集群§r：%s\n", snapshot.machineCluster().toSummary()));
            var kinetic = KineticNetworkAnalyzer.analyze(snapshot.machineCluster());
            if (kinetic.isJammed()) {
                sb.append(String.format("  §c✖ 动力卡死：%s§r\n", kinetic.primaryDiagnosis()));
            }
            var hopper = HopperNetworkAnalyzer.analyze(snapshot.machineCluster());
            if (hopper.hasDeadlock() || hopper.hasBackpressure() || hopper.hasBleedRisk()) {
                sb.append(String.format("  §c⚠ 物流异常：%s§r\n", hopper.primaryDiagnosis()));
            }
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

    private CommandResult handleMultiblock(String playerId, String query, ContextSnapshot snapshot) {
        var bpOpt = MultiblockValidator.findBlueprint(query);
        if (bpOpt.isEmpty()) {
            return CommandResult.error("MULTIBLOCK", "§c未识别的多方块蓝图: " + query + "。可选: conduit (潮涌), beacon (信标), nether_portal (地狱门), end_portal (末地门), wither (凋灵), golem (铁傀儡)");
        }
        MultiblockBlueprint bp = bpOpt.get();
        MultiblockValidator.MultiblockReport report = MultiblockValidator.validateInventory(bp, snapshot != null ? snapshot.inventory() : null);
        String text = report.formatReport();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi multiblock " + bp.id(), text, "MULTIBLOCK", paged);

        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi multiblock " + bp.id());
        String tellraw = TellrawJsonBuilder.toJson(comps);

        BlockPos center;
        if (snapshot != null && snapshot.targetBlock() != null && !snapshot.targetBlock().isAir()) {
            center = new BlockPos(snapshot.targetBlock().x(), snapshot.targetBlock().y(), snapshot.targetBlock().z());
        } else if (snapshot != null) {
            center = new BlockPos((int) Math.floor(snapshot.x()), (int) Math.floor(snapshot.y()), (int) Math.floor(snapshot.z()));
        } else {
            center = new BlockPos(0, 64, 0);
        }
        var ghostPacket = SpatialDirectiveGenerator.generateMultiblockGhostOverlay(bp, center);
        return CommandResult.success("MULTIBLOCK", paged.fullPageText(), "/hoshi multiblock " + bp.id(), tellraw, paged, ghostPacket);
    }

    private CommandResult handlePipeline(String playerId, String machine, int count, String transport) {
        PipelineThroughputAnalyzer.PipelineReport report = PipelineThroughputAnalyzer.analyzeSmeltingArray(count, machine, transport);
        String text = report.formatReport();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi pipeline " + machine + " " + count + " " + transport, text, "PIPELINE", paged);

        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi pipeline " + machine + " " + count + " " + transport);
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("PIPELINE", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleMobFarm(String playerId, double afkY, double farmY, boolean cavesLit) {
        MobFarmDynamics.FarmReport report = MobFarmDynamics.evaluate(afkY, farmY, cavesLit);
        String text = report.formattedReport();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, String.format("/hoshi mobfarm %.0f %.0f %s", afkY, farmY, cavesLit), text, "MOBFARM", paged);

        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), String.format("/hoshi mobfarm %.0f %.0f %s", afkY, farmY, cavesLit));
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("MOBFARM", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleSpawner(String playerId, double dist, int light) {
        MobFarmDynamics.SpawnerReport report = MobFarmDynamics.evaluateSpawner(dist, light);
        String text = report.formattedReport();
        var comps = MinecraftTextFormatter.parseComponents(text, String.format("/hoshi spawner %.0f %d", dist, light));
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("SPAWNER", text, null, tellraw, null);
    }

    private CommandResult handleVillager(String playerId, String type, String[] tokens, int argStart) {
        String t = type.toLowerCase();
        String text;
        if (t.contains("iron") || t.contains("golem") || t.equals("铁") || t.equals("刷铁")) {
            int villagers = 3;
            boolean hasLosBreak = false;
            boolean hasSlept = true;
            if (argStart + 2 < tokens.length) {
                try { villagers = Integer.parseInt(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
            }
            if (argStart + 3 < tokens.length) {
                hasLosBreak = Boolean.parseBoolean(tokens[argStart + 3]) || tokens[argStart + 3].equalsIgnoreCase("true");
            }
            if (argStart + 4 < tokens.length) {
                hasSlept = Boolean.parseBoolean(tokens[argStart + 4]) || tokens[argStart + 4].equalsIgnoreCase("true");
            }
            text = VillagerDynamics.diagnoseIronFarm(villagers, hasLosBreak, hasSlept).formattedReport();
        } else if (t.contains("breed") || t.contains("baby") || t.equals("繁殖")) {
            int food = 6;
            boolean beds = true;
            int ceiling = 2;
            if (argStart + 2 < tokens.length) {
                try { food = Integer.parseInt(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
            }
            if (argStart + 3 < tokens.length) {
                beds = Boolean.parseBoolean(tokens[argStart + 3]) || tokens[argStart + 3].equalsIgnoreCase("true");
            }
            if (argStart + 4 < tokens.length) {
                try { ceiling = Integer.parseInt(tokens[argStart + 4]); } catch (NumberFormatException ignored) {}
            }
            text = VillagerDynamics.diagnoseBreeder(food, beds, ceiling).formattedReport();
        } else {
            boolean traded = true;
            boolean canReach = true;
            if (argStart + 2 < tokens.length) {
                traded = Boolean.parseBoolean(tokens[argStart + 2]) || tokens[argStart + 2].equalsIgnoreCase("true");
            }
            if (argStart + 3 < tokens.length) {
                canReach = Boolean.parseBoolean(tokens[argStart + 3]) || tokens[argStart + 3].equalsIgnoreCase("true");
            }
            text = VillagerDynamics.diagnoseTrading(traded, canReach).formattedReport();
        }

        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi villager " + type, text, "VILLAGER", paged);
        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi villager " + type);
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("VILLAGER", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleAnvil(String playerId, String[] tokens, int argStart) {
        String gearName = "netherite_sword";
        Map<String, Integer> enchants = new LinkedHashMap<>();

        if (argStart + 1 < tokens.length) {
            gearName = tokens[argStart + 1].toLowerCase();
        }

        if (argStart + 2 < tokens.length) {
            for (int i = argStart + 2; i < tokens.length; i++) {
                String token = tokens[i];
                String[] parts = token.split("[:：=]");
                String id = parts[0].toLowerCase();
                int level = 1;
                if (parts.length > 1) {
                    try {
                        level = Integer.parseInt(parts[1]);
                    } catch (NumberFormatException ignored) {}
                }
                enchants.put(id, level);
            }
        } else {
            // Default top-tier set
            if (gearName.contains("sword") || gearName.contains("剑")) {
                enchants.put("sharpness", 5);
                enchants.put("unbreaking", 3);
                enchants.put("mending", 1);
                enchants.put("looting", 3);
                enchants.put("sweeping_edge", 3);
            } else if (gearName.contains("pickaxe") || gearName.contains("镐")) {
                enchants.put("efficiency", 5);
                enchants.put("unbreaking", 3);
                enchants.put("fortune", 3);
                enchants.put("mending", 1);
            } else if (gearName.contains("bow") || gearName.contains("弓")) {
                enchants.put("power", 5);
                enchants.put("unbreaking", 3);
                enchants.put("infinity", 1);
                enchants.put("flame", 1);
            } else {
                enchants.put("protection", 4);
                enchants.put("unbreaking", 3);
                enchants.put("mending", 1);
            }
        }

        AnvilPlan plan = AnvilOptimizer.optimize(gearName, enchants);
        String text = plan.formatReport();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi anvil " + gearName, text, "ANVIL", paged);
        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi anvil " + gearName);
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("ANVIL", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleCreate(String playerId, String[] tokens, int argStart) {
        String source = "steam";
        int param = 9;
        if (argStart + 1 < tokens.length) {
            String s = tokens[argStart + 1].toLowerCase();
            if (s.equals("stress") || s.equals("kinetics")) {
                if (argStart + 2 < tokens.length) source = tokens[argStart + 2];
                if (argStart + 3 < tokens.length) {
                    try { param = Integer.parseInt(tokens[argStart + 3]); } catch (NumberFormatException ignored) {}
                }
            } else {
                source = s;
                if (argStart + 2 < tokens.length) {
                    try { param = Integer.parseInt(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
                }
            }
        }

        List<CreateKineticsAnalyzer.MachineEntry> machines = new ArrayList<>();
        machines.add(new CreateKineticsAnalyzer.MachineEntry("crushing_wheel", 4, 64.0));
        machines.add(new CreateKineticsAnalyzer.MachineEntry("mechanical_press", 2, 64.0));
        machines.add(new CreateKineticsAnalyzer.MachineEntry("mechanical_arm", 2, 32.0));
        machines.add(new CreateKineticsAnalyzer.MachineEntry("fluid_pump", 4, 16.0));

        var report = CreateKineticsAnalyzer.analyze(source, param, machines);
        String text = report.formatReport();
        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi create " + source, text, "CREATE", paged);
        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi create " + source);
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("CREATE", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleChunkloader(String playerId, String[] tokens, int argStart) {
        String sub = argStart + 1 < tokens.length ? tokens[argStart + 1].toLowerCase() : "permaloader";
        String text;

        if (sub.equals("portal") || sub.equals("align") || sub.equals("coord")) {
            double owX = 800.0, owZ = -1600.0, nX = 100.0, nZ = -200.0;
            if (argStart + 2 < tokens.length) {
                try { owX = Double.parseDouble(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
            }
            if (argStart + 3 < tokens.length) {
                try { owZ = Double.parseDouble(tokens[argStart + 3]); } catch (NumberFormatException ignored) {}
            }
            if (argStart + 4 < tokens.length) {
                try { nX = Double.parseDouble(tokens[argStart + 4]); } catch (NumberFormatException ignored) {}
            }
            if (argStart + 5 < tokens.length) {
                try { nZ = Double.parseDouble(tokens[argStart + 5]); } catch (NumberFormatException ignored) {}
            }
            text = PortalChunkLoaderAnalyzer.evaluateAlignment(owX, 64.0, owZ, nX, 64.0, nZ).formatReport();
        } else {
            double interval = 10.0;
            if (argStart + 2 < tokens.length) {
                try { interval = Double.parseDouble(tokens[argStart + 2]); } catch (NumberFormatException ignored) {}
            }
            String transport = argStart + 3 < tokens.length ? tokens[argStart + 3] : "hopper_dropper_clock";
            text = PortalChunkLoaderAnalyzer.analyzePermaloader(interval, transport).formatReport();
        }

        ChatPaginator.PagedResult paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page");
        sessionManager.recordInteraction(playerId, "/hoshi chunkloader " + sub, text, "CHUNKLOADER", paged);
        var comps = MinecraftTextFormatter.parseComponents(paged.fullPageText(), "/hoshi chunkloader " + sub);
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("CHUNKLOADER", paged.fullPageText(), null, tellraw, paged);
    }

    private CommandResult handleStats() {
        String cacheStats = core.getCache().getStats().toString();
        int activeSessions = sessionManager.getActiveSessionCount();
        String msg = String.format("§b【Hoshi AI 运行时度量】§r\n▸ 缓存统计: §a%s§r\n▸ 活跃会话数: §e%d§r\n▸ 响应状态: §a正常运行§r",
                cacheStats, activeSessions);
        return CommandResult.success("STATS", msg, null, null, null);
    }

    private CommandResult handleCluster(String playerId, String[] tokens, int argStart, ContextSnapshot snapshot) {
        String sub = argStart + 1 < tokens.length ? tokens[argStart + 1].toLowerCase() : "all";
        LocalMachineCluster cluster = snapshot != null ? snapshot.machineCluster() : null;

        if (cluster == null || cluster.isEmpty()) {
            String msg = "§6【局部机器拓扑诊断】§r\n" +
                    "当前准星未捕捉到局部多方块机器集群数据。\n" +
                    "支持子诊断：\n" +
                    "▸ §e/hoshi cluster kinetics§r - 诊断 Create 机械动力齿轮卡死与反向啮合\n" +
                    "▸ §e/hoshi cluster hopper§r - 诊断漏斗流水线死锁环路、背压与分类器串线\n" +
                    "▸ §e/hoshi cluster crafter§r - 诊断 1.21 自动合成器槽位遮罩与脉冲时钟";
            return CommandResult.success("CLUSTER", msg, null, null, null);
        }

        StringBuilder sb = new StringBuilder();
        sb.append(String.format("§6【局部机器集群拓扑诊断 (%s)】§r\n", sub.toUpperCase()));
        sb.append(String.format("▸ 集群中心：%s | 包含方块：%d 个\n", cluster.origin(), cluster.size()));

        if ("kinetics".equals(sub) || "all".equals(sub)) {
            var k = KineticNetworkAnalyzer.analyze(cluster);
            sb.append(String.format("▸ 动力状态：%s\n", k.primaryDiagnosis()));
            if (k.isJammed()) {
                for (String c : k.conflicts()) sb.append("  ✖ ").append(c).append("\n");
                sb.append("  建议：").append(k.actionableRemediation()).append("\n");
            }
        }

        if ("hopper".equals(sub) || "all".equals(sub)) {
            var h = HopperNetworkAnalyzer.analyze(cluster);
            sb.append(String.format("▸ 物流状态：%s\n", h.primaryDiagnosis()));
            if (h.hasDeadlock()) {
                for (String d : h.deadlocks()) sb.append("  ⚡ ").append(d).append("\n");
            }
            if (!h.warnings().isEmpty()) {
                for (String w : h.warnings()) sb.append("  ⚠ ").append(w).append("\n");
            }
            sb.append("  建议：").append(h.actionableAdvice()).append("\n");
        }

        SpatialDirectivePacket packet = null;
        if ("kinetics".equals(sub)) {
            var k = KineticNetworkAnalyzer.analyze(cluster);
            packet = SpatialDirectiveGenerator.generateKineticOverlay(cluster, k);
        } else if ("hopper".equals(sub)) {
            var h = HopperNetworkAnalyzer.analyze(cluster);
            packet = SpatialDirectiveGenerator.generateHopperOverlay(cluster, h);
        } else if ("all".equals(sub)) {
            var k = KineticNetworkAnalyzer.analyze(cluster);
            if (k.isJammed()) {
                packet = SpatialDirectiveGenerator.generateKineticOverlay(cluster, k);
            } else {
                var h = HopperNetworkAnalyzer.analyze(cluster);
                if (h.hasDeadlock() || h.hasBackpressure() || h.hasBleedRisk()) {
                    packet = SpatialDirectiveGenerator.generateHopperOverlay(cluster, h);
                }
            }
        }

        return CommandResult.success("CLUSTER", sb.toString().trim(), null, null, null, packet);
    }

    private CommandResult handleHighlight(String playerId, String[] tokens, int argStart, ContextSnapshot snapshot) {
        String sub = argStart + 1 < tokens.length ? tokens[argStart + 1].toLowerCase() : "help";

        if ("clear".equals(sub) || "reset".equals(sub)) {
            var clearPacket = SpatialDirectivePacket.clear("ALL");
            return CommandResult.success("HIGHLIGHT", "§a[Hoshi] 已发送清除所有空间高亮覆盖层指令。", null, clearPacket.toTellrawFallback(), null, clearPacket);
        }

        if ("kinetics".equals(sub) || "create".equals(sub) || "gear".equals(sub)) {
            LocalMachineCluster cluster = snapshot != null ? snapshot.machineCluster() : null;
            if (cluster == null || cluster.isEmpty()) {
                return CommandResult.error("HIGHLIGHT", "§c准星未捕捉到局部机械动力组件，无法投射动力高亮。");
            }
            var k = KineticNetworkAnalyzer.analyze(cluster);
            var packet = SpatialDirectiveGenerator.generateKineticOverlay(cluster, k);
            return CommandResult.success("HIGHLIGHT", "§a[Hoshi 3D 高亮] " + packet.hudTitle(), null, packet.toTellrawFallback(), null, packet);
        }

        if ("hopper".equals(sub) || "pipe".equals(sub)) {
            LocalMachineCluster cluster = snapshot != null ? snapshot.machineCluster() : null;
            if (cluster == null || cluster.isEmpty()) {
                return CommandResult.error("HIGHLIGHT", "§c准星未捕捉到漏斗物流组件，无法投射物流高亮。");
            }
            var h = HopperNetworkAnalyzer.analyze(cluster);
            var packet = SpatialDirectiveGenerator.generateHopperOverlay(cluster, h);
            return CommandResult.success("HIGHLIGHT", "§a[Hoshi 3D 高亮] " + packet.hudTitle(), null, packet.toTellrawFallback(), null, packet);
        }

        if ("mobfarm".equals(sub) || "spheres".equals(sub)) {
            double px = snapshot != null ? snapshot.x() : 0.0;
            double py = snapshot != null ? snapshot.y() : 64.0;
            double pz = snapshot != null ? snapshot.z() : 0.0;
            var packet = SpatialDirectiveGenerator.generateMobFarmOverlay(px, py, pz);
            return CommandResult.success("HIGHLIGHT", "§a[Hoshi 3D 高亮] " + packet.hudTitle(), null, packet.toTellrawFallback(), null, packet);
        }

        if ("multiblock".equals(sub) || "mb".equals(sub) || "ghost".equals(sub)) {
            String query = argStart + 2 < tokens.length ? tokens[argStart + 2] : "conduit";
            var bpOpt = MultiblockValidator.findBlueprint(query);
            if (bpOpt.isEmpty()) {
                return CommandResult.error("HIGHLIGHT", "§c未识别的多方块蓝图: " + query);
            }
            BlockPos center;
            if (snapshot != null && snapshot.targetBlock() != null && !snapshot.targetBlock().isAir()) {
                center = new BlockPos(snapshot.targetBlock().x(), snapshot.targetBlock().y(), snapshot.targetBlock().z());
            } else if (snapshot != null) {
                center = new BlockPos((int) Math.floor(snapshot.x()), (int) Math.floor(snapshot.y()), (int) Math.floor(snapshot.z()));
            } else {
                center = new BlockPos(0, 64, 0);
            }
            var packet = SpatialDirectiveGenerator.generateMultiblockGhostOverlay(bpOpt.get(), center);
            return CommandResult.success("HIGHLIGHT", "§a[Hoshi 3D 虚影] " + packet.hudTitle(), null, packet.toTellrawFallback(), null, packet);
        }

        String msg = "§6【Hoshi 3D 空间全息高亮指令】§r\n" +
                "▸ §e/hoshi highlight kinetics§r - 在游戏世界高亮冲突齿轮与流向\n" +
                "▸ §e/hoshi highlight hopper§r - 投射漏斗死锁环路与物流方向箭头\n" +
                "▸ §e/hoshi highlight multiblock <名称>§r - 在准星位置投射多方块虚影蓝图\n" +
                "▸ §e/hoshi highlight mobfarm§r - 以自身为中心投射 24/32/128m 刷怪动力学清除圈\n" +
                "▸ §e/hoshi highlight clear§r - 清除所有世界高亮与全息虚影";
        return CommandResult.success("HIGHLIGHT", msg, null, null, null);
    }

    private CommandResult handleHelp() {
        String text = "§6【Hoshi 智能问答指令帮助】§r\n" +
                "▸ §e/hoshi ask <问题>§r - 咨询游戏机制与攻略\n" +
                "▸ §e/hoshi inspect§r - 扫描准星方块、红石物流状态与实体安全\n" +
                "▸ §e/hoshi craft <物品>§r - 评估背包原料是否满足合成条件及缺失数量\n" +
                "▸ §e/hoshi bom <方案> [数量]§r - 生成材料清单 (BOM)\n" +
                "▸ §e/hoshi page <页码>§r - 翻页长篇内容\n" +
                "▸ §e/hoshi multiblock <方案>§r - 调阅多方块蓝图与背包材料校验\n" +
                "▸ §e/hoshi pipeline <设备> [数量] [物流]§r - 诊断工业流水线供料瓶颈\n" +
                "▸ §e/hoshi mobfarm <挂机Y> <平台Y> [洞穴点亮]§r - 诊断清除球与生物Cap占用\n" +
                "▸ §e/hoshi villager <iron/breeder/trading>§r - 诊断刷铁机/繁殖/工作站死锁\n" +
                "▸ §e/hoshi anvil <装备> [附魔:等级...]§r - 规划二叉树最优附魔工序规避过于昂贵\n" +
                "▸ §e/hoshi create stress <动力源> [规模]§r - 诊断 Create 模组动力网应力与过载转速\n" +
                "▸ §e/hoshi chunkloader <permaloader/portal>§r - 诊断生电传送门常载网与 8:1 坐标漂移\n" +
                "▸ §e/hoshi cluster [kinetics/hopper/crafter]§r - 诊断局部机器拓扑、齿轮卡死与漏斗回路\n" +
                "▸ §e/hoshi highlight [kinetics/hopper/multiblock/mobfarm/clear]§r - 投射 3D 空间高亮与全息虚影\n" +
                "▸ §e/hoshi nether [x y z]§r - 换算地狱传送门坐标\n" +
                "▸ §e/hoshi clear§r - 清理会话与翻页缓存\n" +
                "▸ §e/hoshi stats§r - 查看缓存与度量统计\n" +
                "§7公屏输入 '!问题' 也可直接提问。§r";

        var comps = MinecraftTextFormatter.parseComponents(text, "/hoshi help");
        String tellraw = TellrawJsonBuilder.toJson(comps);
        return CommandResult.success("HELP", text, null, tellraw, null);
    }
}
