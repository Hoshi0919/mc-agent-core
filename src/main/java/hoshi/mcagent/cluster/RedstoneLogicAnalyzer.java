package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Diagnostic analyzer for Minecraft Redstone logic gates (AND, OR, XOR),
 * memory latches (RS-NOR latch race conditions), monostable pulse shapers,
 * sticky piston 1-tick block spitting dynamics, and Minecraft 1.21 Copper Bulb
 * native T-flip-flops with 1-gametick odd delay.
 */
public final class RedstoneLogicAnalyzer {

    public enum LogicType {
        COPPER_BULB_T_FLIP_FLOP,
        RS_NOR_LATCH,
        STICKY_PISTON_T_FLIP_FLOP,
        MONOSTABLE_CIRCUIT,
        LOGIC_GATE,
        NONE
    }

    public enum GateKind {
        AND,
        OR,
        XOR,
        NOT,
        NONE
    }

    public record LogicReport(
            boolean isHealthy,
            boolean hasRaceConflict,
            boolean hasPulseWidthMismatch,
            boolean hasBulbLock,
            boolean hasGlitchRisk,
            BlockPos targetPos,
            String targetBlockType,
            LogicType logicType,
            GateKind gateKind,
            boolean outputState,
            int signalStrength,
            List<BlockPos> conflictNodes,
            List<BlockPos> activeOutputs,
            List<BlockPos> logicComponents,
            List<String> issues,
            List<String> warnings,
            String primaryDiagnosis,
            String actionableAdvice
    ) {
        public static LogicReport empty() {
            return new LogicReport(
                    true, false, false, false, false,
                    new BlockPos(0, 0, 0), "none", LogicType.NONE, GateKind.NONE,
                    false, 0,
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(), Collections.emptyList(),
                    Collections.emptyList(),
                    "未检测到红石门电路、锁存器或触发器组件", ""
            );
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("§e【红石门电路、时序锁存器与铜球触发器因果诊断报告】§r\n");
            sb.append(String.format("▸ 目标组件坐标：%s (%s)\n", targetPos, targetBlockType.toUpperCase()));
            sb.append(String.format("▸ 逻辑类型：%s | 输出状态: %s (信号强度: §6%d§r)\n",
                    formatLogicType(logicType, gateKind),
                    outputState ? "§a[激活/高电平/ON]§r" : "§7[休眠/低电平/OFF]§r",
                    signalStrength));

            if (hasRaceConflict) {
                sb.append("  ⚡ §c[锁存器竞争冲突] RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 冲突输入端: %s (双端熄灭并在撤除信号时触发亚稳态自激)\n", cPos));
                }
            }

            if (hasPulseWidthMismatch) {
                sb.append("  ⚡ §e[脉宽不匹配失效] 粘性活塞 T 触发器输入脉冲 > 2 gameticks (检测到按钮或长持续供电)！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 超宽输入电源: %s (活塞伸缩带回方块，无法脱离方块翻转)\n", cPos));
                }
            }

            if (hasBulbLock) {
                sb.append("  ⚡ §6[铜球未复位锁定] 1.21 铜球处于持续充能状态 (powered=true)，无法响应后续脉冲！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ✖ 持续通电锁定点: %s (需先断开信号恢复 powered=false)\n", cPos));
                }
            }

            if (hasGlitchRisk) {
                sb.append("  ⚡ §e[门电路毛刺风险] 复合门多路输入存在延时差 (>=2 ticks)，切换瞬间可能激发出瞬态假脉冲！§r\n");
                for (BlockPos cPos : conflictNodes) {
                    sb.append(String.format("     ↷ 延时失配输入端: %s\n", cPos));
                }
            }

            if (isHealthy) {
                sb.append("  ✓ §a[逻辑健康] 时序逻辑与门电路逻辑状态清晰，无竞争冒险、脉宽失配或锁死隐患。§r\n");
            }

            sb.append(String.format("▸ 核心诊断：%s\n", primaryDiagnosis));
            if (!actionableAdvice.isEmpty()) {
                sb.append(String.format("▸ 修复建议：%s\n", actionableAdvice));
            }
            return sb.toString();
        }

        private static String formatLogicType(LogicType lt, GateKind gk) {
            return switch (lt) {
                case COPPER_BULB_T_FLIP_FLOP -> "§b1.21 铜球原生 T 触发器 (Copper Bulb T-Flip-Flop)§r";
                case RS_NOR_LATCH -> "§aRS-NOR 保持锁存器 (Bi-stable Latch)§r";
                case STICKY_PISTON_T_FLIP_FLOP -> "§3粘性活塞 1 刻吐方块 T 触发器 (Piston 1-Tick Spit)§r";
                case MONOSTABLE_CIRCUIT -> "§6单稳态脉冲限制器 (Monostable Pulse Limiter)§r";
                case LOGIC_GATE -> String.format("§d复合门电路 (%s 门)§r", gk);
                case NONE -> "§7无特定门电路§r";
            };
        }
    }

    private RedstoneLogicAnalyzer() {}

    /**
     * Diagnostic analysis of redstone logic, latches, flip-flops, and gates in cluster.
     */
    public static LogicReport analyzeLogic(LocalMachineCluster cluster, BlockPos targetPos) {
        if (cluster == null || cluster.isEmpty()) {
            return LogicReport.empty();
        }

        LocalBlock target = cluster.getBlock(targetPos);
        BlockPos focusPos = (target != null && !target.isAir()) ? targetPos : cluster.origin();
        LocalBlock focusBlock = cluster.getBlock(focusPos);

        // 1. Check if target or cluster has a Copper Bulb
        if (focusBlock != null && focusBlock.isCopperBulb()) {
            return analyzeCopperBulb(cluster, focusBlock);
        }
        for (LocalBlock b : cluster.getConnectedCopperBulbs()) {
            return analyzeCopperBulb(cluster, b);
        }

        // 2. Check if target or cluster has RS-NOR Latch
        LogicReport latchReport = scanRsNorLatch(cluster, focusPos);
        if (latchReport != null) {
            return latchReport;
        }

        // 3. Check if target or cluster has Sticky Piston T-Flip-Flop
        if (focusBlock != null && focusBlock.isStickyPiston()) {
            return analyzePistonTFlipFlop(cluster, focusBlock);
        }
        for (LocalBlock b : cluster.getConnectedPistons()) {
            if (b.isStickyPiston()) {
                return analyzePistonTFlipFlop(cluster, b);
            }
        }

        // 4. Check if target or cluster has Monostable Circuit
        LogicReport monostableReport = scanMonostableCircuit(cluster, focusPos);
        if (monostableReport != null) {
            return monostableReport;
        }

        // 5. Check if target or cluster has Logic Gate (AND / OR / XOR)
        LogicReport gateReport = scanLogicGate(cluster, focusPos);
        if (gateReport != null) {
            return gateReport;
        }

        return LogicReport.empty();
    }

    /**
     * 1.21 Copper Bulb T-Flip-Flop analysis.
     */
    private static LogicReport analyzeCopperBulb(LocalMachineCluster cluster, LocalBlock bulb) {
        BlockPos pos = bulb.pos();
        boolean isLit = bulb.isCopperBulbLit();
        boolean isPowered = bulb.isPowered();

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> activeOutputs = new ArrayList<>();
        List<BlockPos> logicComponents = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        logicComponents.add(pos);
        if (isLit) {
            activeOutputs.add(pos);
        }

        boolean hasBulbLock = false;
        boolean hasLoopOscillation = false;

        // Check if held powered (lever or active continuous signal without reset)
        if (isPowered) {
            hasBulbLock = true;
            conflictNodes.add(pos);
            issues.add("铜球当前处于持续充能状态 (powered=true)，若无断电过程无法响应后续红石脉冲切换 lit 状态！");
        }

        // Check adjacent comparators reading from copper bulb
        int comparatorSignal = isLit ? 15 : 0;
        for (BlockPos nPos : pos.neighbors()) {
            LocalBlock nb = cluster.getBlock(nPos);
            if (nb != null && nb.isComparator()) {
                logicComponents.add(nPos);
                String cFacing = nb.facing();
                // Comparator reading from bulb (rear facing towards bulb)
                if (nPos.offset(cFacing).equals(pos) || nPos.offset(reverseFacing(cFacing)).equals(pos)) {
                    // Check if comparator output loops back to copper bulb without repeater
                    BlockPos compOut = nPos.offset(cFacing);
                    if (compOut.equals(pos) || compOut.neighbors().contains(pos)) {
                        hasLoopOscillation = true;
                        conflictNodes.add(nPos);
                        issues.add("检测到铜球经由比较器直连自反馈回路，将引发 1-gt 极限高频啸叫振荡！");
                    }
                }
            }
        }

        boolean isHealthy = !hasBulbLock && !hasLoopOscillation;
        String diag;
        String advice;

        if (hasLoopOscillation) {
            diag = "铜球与比较器构成无延时自反馈闭环，将诱发 1-gametick 极限高频啸叫自激！";
            advice = "在比较器输出端接入红石中继器或断开直连反馈，避免服务器卡顿。";
        } else if (hasBulbLock) {
            diag = "1.21 铜球处于持续充能锁定状态 (powered=true)，后续红石脉冲将失效。";
            advice = "断开持续供电信号（如将拉杆切为按钮，或确保前置信号能及时断电归零）。";
        } else {
            diag = String.format("1.21 原生铜球 T 触发器状态正常 (lit=%b, powered=%b)，具 1-gt 奇数刻极速延迟", isLit, isPowered);
            advice = "可后接红石比较器无损读取 15 级高信噪满信号，或用于奇数刻超紧凑时钟。";
        }

        return new LogicReport(
                isHealthy,
                false,
                false,
                hasBulbLock || hasLoopOscillation,
                false,
                pos,
                bulb.blockId(),
                LogicType.COPPER_BULB_T_FLIP_FLOP,
                GateKind.NONE,
                isLit,
                comparatorSignal,
                conflictNodes,
                activeOutputs,
                logicComponents,
                issues,
                warnings,
                diag,
                advice
        );
    }

    /**
     * RS-NOR Latch bi-stable circuit analysis.
     */
    private static LogicReport scanRsNorLatch(LocalMachineCluster cluster, BlockPos focusPos) {
        // Find pairs of cross-coupled torches or inverter bases
        List<LocalBlock> torches = cluster.blocks().values().stream()
                .filter(LocalBlock::isRedstoneTorch)
                .collect(Collectors.toList());

        if (torches.size() < 2) {
            // Also check if cluster explicitly marked latch properties
            LocalBlock target = cluster.getBlock(focusPos);
            if (target != null && ("true".equalsIgnoreCase(target.getProperty("latch", "false")) ||
                    target.getProperty("circuit", "").equalsIgnoreCase("rs_nor"))) {
                return evaluateExplicitRsNor(cluster, target);
            }
            return null;
        }

        for (int i = 0; i < torches.size(); i++) {
            for (int j = i + 1; j < torches.size(); j++) {
                LocalBlock tA = torches.get(i);
                LocalBlock tB = torches.get(j);
                if (isLatchPair(cluster, tA, tB)) {
                    return evaluateRsNorPair(cluster, tA, tB);
                }
            }
        }

        LocalBlock target = cluster.getBlock(focusPos);
        if (target != null && ("true".equalsIgnoreCase(target.getProperty("latch", "false")) ||
                target.getProperty("circuit", "").equalsIgnoreCase("rs_nor"))) {
            return evaluateExplicitRsNor(cluster, target);
        }

        return null;
    }

    private static boolean isLatchPair(LocalMachineCluster cluster, LocalBlock tA, LocalBlock tB) {
        // Check if distance is small (<= 5 blocks) and in cluster
        int dist = Math.abs(tA.pos().x() - tB.pos().x()) +
                   Math.abs(tA.pos().y() - tB.pos().y()) +
                   Math.abs(tA.pos().z() - tB.pos().z());
        return dist <= 5;
    }

    private static LogicReport evaluateRsNorPair(LocalMachineCluster cluster, LocalBlock tA, LocalBlock tB) {
        BlockPos posA = tA.pos();
        BlockPos posB = tB.pos();

        boolean litA = !"false".equalsIgnoreCase(tA.getProperty("lit", "true"));
        boolean litB = !"false".equalsIgnoreCase(tB.getProperty("lit", "false"));

        // Check inputs S and R
        boolean sActive = "true".equalsIgnoreCase(tA.getProperty("set", "false")) ||
                          "true".equalsIgnoreCase(cluster.getBlock(posA.offset("down")) != null ? cluster.getBlock(posA.offset("down")).getProperty("powered", "false") : "false");
        boolean rActive = "true".equalsIgnoreCase(tB.getProperty("reset", "false")) ||
                          "true".equalsIgnoreCase(cluster.getBlock(posB.offset("down")) != null ? cluster.getBlock(posB.offset("down")).getProperty("powered", "false") : "false");

        // Check if external power is applied to bases
        for (BlockPos n : posA.neighbors()) {
            LocalBlock nb = cluster.getBlock(n);
            if (nb != null && (nb.isButton() || nb.isLever()) && nb.isPowered()) {
                sActive = true;
            }
        }
        for (BlockPos n : posB.neighbors()) {
            LocalBlock nb = cluster.getBlock(n);
            if (nb != null && (nb.isButton() || nb.isLever()) && nb.isPowered()) {
                rActive = true;
            }
        }

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> activeOutputs = new ArrayList<>();
        List<BlockPos> components = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        components.add(posA);
        components.add(posB);

        boolean hasRaceConflict = sActive && rActive;
        if (hasRaceConflict) {
            conflictNodes.add(posA);
            conflictNodes.add(posB);
            issues.add("RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！两路输出均被强行熄灭，撤除时引发亚稳态竞争自激！");
        }

        if (litA) activeOutputs.add(posA);
        if (litB) activeOutputs.add(posB);

        boolean qState = litB || (!litA && !rActive);
        int signal = qState ? 15 : 0;

        String diag;
        String advice;
        if (hasRaceConflict) {
            diag = "RS-NOR 保持锁存器检测到非法竞争状态 (S=1 & R=1)，两路火把熄灭，存在竞争冒险高危";
            advice = "在 Set 与 Reset 输入端增加前置互锁逻辑或双向仲裁电路，禁止双侧同时触发。";
        } else {
            diag = String.format("RS-NOR 保持锁存器工作正常 [Q=%d, Q_BAR=%d] (S=%b, R=%b)", qState ? 1 : 0, qState ? 0 : 1, sActive, rActive);
            advice = "保持 Set 与 Reset 互斥脉冲输入，避免同时通电。";
        }

        return new LogicReport(
                !hasRaceConflict,
                hasRaceConflict,
                false,
                false,
                false,
                posB,
                "minecraft:redstone_torch",
                LogicType.RS_NOR_LATCH,
                GateKind.NONE,
                qState,
                signal,
                conflictNodes,
                activeOutputs,
                components,
                issues,
                warnings,
                diag,
                advice
        );
    }

    private static LogicReport evaluateExplicitRsNor(LocalMachineCluster cluster, LocalBlock target) {
        boolean sActive = "true".equalsIgnoreCase(target.getProperty("set", "false"));
        boolean rActive = "true".equalsIgnoreCase(target.getProperty("reset", "false"));
        boolean hasRace = sActive && rActive;

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> activeOutputs = new ArrayList<>();
        List<BlockPos> components = List.of(target.pos());
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        if (hasRace) {
            conflictNodes.add(target.pos());
            issues.add("RS-NOR 保持锁存器检测到 Set 与 Reset 同时激活 (S=1, R=1)！两端强行熄灭并在撤除时诱发亚稳态！");
        }

        boolean q = sActive || (!rActive && !"false".equalsIgnoreCase(target.getProperty("q", "true")));
        if (q && !hasRace) activeOutputs.add(target.pos());

        return new LogicReport(
                !hasRace,
                hasRace,
                false,
                false,
                false,
                target.pos(),
                target.blockId(),
                LogicType.RS_NOR_LATCH,
                GateKind.NONE,
                q,
                q ? 15 : 0,
                conflictNodes,
                activeOutputs,
                components,
                issues,
                warnings,
                hasRace ? "RS-NOR 保持锁存器检测到非法输入冲突 (S=1 & R=1)" : "RS-NOR 保持锁存器工作正常",
                hasRace ? "增加前置互锁电路禁止双端同时通电" : "保持当前输入分离"
        );
    }

    /**
     * Sticky Piston 1-Tick Spit T-Flip-Flop analysis.
     */
    private static LogicReport analyzePistonTFlipFlop(LocalMachineCluster cluster, LocalBlock piston) {
        BlockPos pos = piston.pos();
        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> activeOutputs = new ArrayList<>();
        List<BlockPos> components = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        components.add(pos);
        String facing = piston.facing();
        BlockPos spitPos = pos.offset(facing);

        // Check input pulse width
        boolean hasMonostable = "true".equalsIgnoreCase(piston.getProperty("has_monostable", "false"));
        int pulseWidthGt = Integer.parseInt(piston.getProperty("pulse_width", "0"));

        boolean hasButtonInput = false;
        BlockPos inputSourcePos = null;

        for (BlockPos n : pos.neighbors()) {
            LocalBlock nb = cluster.getBlock(n);
            if (nb == null) continue;
            if (nb.isButton()) {
                hasButtonInput = true;
                inputSourcePos = n;
                if (pulseWidthGt == 0) {
                    pulseWidthGt = nb.blockId().contains("wood") ? 30 : 20; // Wood 30gt, Stone 20gt
                }
            } else if (nb.isLever() && nb.isPowered()) {
                hasButtonInput = true;
                inputSourcePos = n;
                if (pulseWidthGt == 0) pulseWidthGt = 100; // Continuous
            } else if (nb.isRepeater()) {
                int repDelay = Integer.parseInt(nb.getProperty("delay", "1"));
                if (repDelay >= 2 && pulseWidthGt == 0) {
                    pulseWidthGt = repDelay * 2;
                }
            }
        }

        boolean hasPulseWidthMismatch = !hasMonostable && (pulseWidthGt > 2 || hasButtonInput);

        if (hasPulseWidthMismatch) {
            conflictNodes.add(pos);
            if (inputSourcePos != null) conflictNodes.add(inputSourcePos);
            issues.add(String.format("粘性活塞 T 触发器输入脉冲宽度为 %d gameticks (> 2 gt)！活塞伸缩后将吸回方块，无法脱离方块翻转！", pulseWidthGt));
        }

        boolean isExtended = piston.isExtended() || "true".equalsIgnoreCase(piston.getProperty("spit_out", "false"));
        if (isExtended) {
            activeOutputs.add(spitPos);
        }

        boolean isHealthy = !hasPulseWidthMismatch;
        String diag;
        String advice;

        if (hasPulseWidthMismatch) {
            diag = String.format("粘性活塞 T 触发器输入脉宽过长 (%d gt > 2 gt)，活塞拉回方块无法吐出", pulseWidthGt);
            advice = "在输入端前置接入单稳态电路（如普通活塞切线单稳态或双路反相延时器），将脉宽精确裁剪至 <= 2 gameticks (1 redstone tick)。";
        } else {
            diag = "粘性活塞 1 刻吐方块 T 触发器工作正常 (脉冲 <= 2 gt 瞬间脱离)";
            advice = "保持超短脉冲输入以维持可靠双稳态切换。";
        }

        return new LogicReport(
                isHealthy,
                false,
                hasPulseWidthMismatch,
                false,
                false,
                pos,
                piston.blockId(),
                LogicType.STICKY_PISTON_T_FLIP_FLOP,
                GateKind.NONE,
                isExtended,
                isExtended ? 15 : 0,
                conflictNodes,
                activeOutputs,
                components,
                issues,
                warnings,
                diag,
                advice
        );
    }

    /**
     * Monostable Circuit / Pulse Limiter analysis.
     */
    private static LogicReport scanMonostableCircuit(LocalMachineCluster cluster, BlockPos focusPos) {
        LocalBlock target = cluster.getBlock(focusPos);
        if (target != null && ("true".equalsIgnoreCase(target.getProperty("monostable", "false")) ||
                target.getProperty("circuit", "").equalsIgnoreCase("monostable"))) {
            List<BlockPos> components = List.of(target.pos());
            return new LogicReport(
                    true, false, false, false, false,
                    target.pos(), target.blockId(),
                    LogicType.MONOSTABLE_CIRCUIT, GateKind.NONE,
                    target.isPowered(), target.isPowered() ? 15 : 0,
                    Collections.emptyList(),
                    target.isPowered() ? List.of(target.pos()) : Collections.emptyList(),
                    components,
                    Collections.emptyList(), Collections.emptyList(),
                    "单稳态脉冲限制器工作正常，输出 1 redstone tick (2 gt) 极短脉冲",
                    "可用于粘性活塞吐方块、计数器或发射器点射"
            );
        }
        return null;
    }

    /**
     * Logic Gate (AND / OR / XOR) analysis.
     */
    private static LogicReport scanLogicGate(LocalMachineCluster cluster, BlockPos focusPos) {
        LocalBlock target = cluster.getBlock(focusPos);
        if (target == null) return null;

        String circuit = target.getProperty("circuit", "").toLowerCase();
        String gate = target.getProperty("gate", "").toLowerCase();

        GateKind kind = GateKind.NONE;
        if (circuit.contains("and") || gate.contains("and")) kind = GateKind.AND;
        else if (circuit.contains("xor") || gate.contains("xor")) kind = GateKind.XOR;
        else if (circuit.contains("or") || gate.contains("or")) kind = GateKind.OR;

        if (kind == GateKind.NONE) {
            return null;
        }

        boolean inA = "true".equalsIgnoreCase(target.getProperty("input_a", "false"));
        boolean inB = "true".equalsIgnoreCase(target.getProperty("input_b", "false"));
        int delayA = Integer.parseInt(target.getProperty("delay_a", "0"));
        int delayB = Integer.parseInt(target.getProperty("delay_b", "0"));

        boolean hasGlitchRisk = Math.abs(delayA - delayB) >= 2;

        boolean out = switch (kind) {
            case AND -> inA && inB;
            case OR -> inA || inB;
            case XOR -> inA ^ inB;
            case NOT -> !inA;
            case NONE -> false;
        };

        List<BlockPos> conflictNodes = new ArrayList<>();
        List<BlockPos> activeOutputs = new ArrayList<>();
        List<BlockPos> components = List.of(target.pos());
        List<String> issues = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        if (hasGlitchRisk) {
            conflictNodes.add(target.pos());
            warnings.add(String.format("门电路双路输入延时差为 %d ticks (>= 2 ticks)，在同时切换瞬间可能出现 1-tick 瞬态毛刺脉冲 (Glitch)！", Math.abs(delayA - delayB)));
        }

        if (out) activeOutputs.add(target.pos());

        String diag = hasGlitchRisk ?
                String.format("复合门电路 (%s 门) 输入延迟不对齐 (差值 %d ticks)，存在毛刺冒险", kind, Math.abs(delayA - delayB)) :
                String.format("复合门电路 (%s 门) 逻辑运算正常 [A=%b, B=%b -> OUT=%b]", kind, inA, inB, out);
        String advice = hasGlitchRisk ?
                "在延迟较短的输入通路上串联中继器平衡时间，避免瞬态毛刺误触下级机械。" :
                "逻辑信号对称，保持当前布线。";

        return new LogicReport(
                !hasGlitchRisk,
                false,
                false,
                false,
                hasGlitchRisk,
                target.pos(),
                target.blockId(),
                LogicType.LOGIC_GATE,
                kind,
                out,
                out ? 15 : 0,
                conflictNodes,
                activeOutputs,
                components,
                issues,
                warnings,
                diag,
                advice
        );
    }

    private static String reverseFacing(String facing) {
        return switch (facing.toLowerCase()) {
            case "north" -> "south";
            case "south" -> "north";
            case "east" -> "west";
            case "west" -> "east";
            case "up" -> "down";
            default -> "up";
        };
    }
}
