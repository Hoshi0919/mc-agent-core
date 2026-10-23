import math
from dataclasses import dataclass
from typing import Optional
from .bom import BlueprintBOM, MaterialCalculator
from .context import ContextSnapshot
from .crafting import CraftingReadinessChecker
from .dispatcher import AsyncQueryDispatcher, QueryResult
from .formatter import MinecraftTextFormatter
from .paginator import ChatPaginator, PagedResult
from .session import PlayerSessionManager
from .tellraw import TellrawJsonBuilder


@dataclass(frozen=True)
class CommandResult:
    status: str
    action: str
    message: str
    command_suggestion: Optional[str] = None
    tellraw_json: Optional[str] = None
    paged_result: Optional[PagedResult] = None

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"


class CommandRouter:
    def __init__(self, dispatcher: AsyncQueryDispatcher, session_manager: Optional[PlayerSessionManager] = None):
        self.dispatcher = dispatcher
        self.session_manager = session_manager or PlayerSessionManager()

    @staticmethod
    def is_chat_trigger(raw_message: Optional[str]) -> bool:
        if not raw_message:
            return False
        s = raw_message.strip()
        return (
            s.startswith("!")
            or s.startswith("！")
            or s.startswith("?")
            or s.startswith("？")
            or s.lower().startswith("@ai ")
            or s.lower().startswith("@hoshi ")
        )

    @staticmethod
    def extract_chat_query(raw_message: Optional[str]) -> str:
        if not raw_message:
            return ""
        s = raw_message.strip()
        if s.startswith("!") or s.startswith("！") or s.startswith("?") or s.startswith("？"):
            return s[1:].strip()
        if s.lower().startswith("@ai "):
            return s[4:].strip()
        if s.lower().startswith("@hoshi "):
            return s[7:].strip()
        return s

    def execute(self, player_id: Optional[str], raw_command: Optional[str], snapshot: Optional[ContextSnapshot] = None) -> CommandResult:
        if not raw_command or not raw_command.strip():
            return CommandResult(status="UNKNOWN_SUBCOMMAND", action="UNKNOWN", message="§c请输入有效指令，例如 /hoshi help")

        inp = raw_command.strip()
        if inp.startswith("/"):
            inp = inp[1:].strip()

        if self.is_chat_trigger(inp):
            q = self.extract_chat_query(inp)
            return self._handle_ask(player_id, q, snapshot)

        tokens = inp.split()
        if not tokens:
            return CommandResult(status="UNKNOWN_SUBCOMMAND", action="UNKNOWN", message="§c请输入有效指令，例如 /hoshi help")

        arg_start = 0
        first = tokens[0].lower()
        if first in ("ai", "hoshi", "mcagent"):
            arg_start = 1

        if arg_start >= len(tokens):
            return self._handle_help()

        sub = tokens[arg_start].lower()

        if sub in ("inspect", "scan"):
            return self._handle_inspect(player_id, snapshot)

        elif sub in ("craft", "recipe"):
            if arg_start + 1 >= len(tokens):
                return CommandResult(status="ERROR", action="CRAFT", message="§c请提供待合成的物品名称，例如: /hoshi craft hopper")
            item_name = " ".join(tokens[arg_start + 1:])
            return self._handle_craft(player_id, item_name, snapshot)

        elif sub in ("ask", "q", "query"):
            if arg_start + 1 >= len(tokens):
                return CommandResult(status="ERROR", action="ASK", message="§c请提供提问内容，例如: /hoshi ask 钻石在几层？")
            question = " ".join(tokens[arg_start + 1 :])
            return self._handle_ask(player_id, question, snapshot)

        elif sub in ("page", "p"):
            if arg_start + 1 >= len(tokens):
                return CommandResult(status="ERROR", action="PAGE", message="§c请指定目标页码，例如: /hoshi page 2")
            try:
                page = int(tokens[arg_start + 1])
                return self._handle_page(player_id, page)
            except ValueError:
                return CommandResult(status="ERROR", action="PAGE", message=f"§c无效页码: {tokens[arg_start + 1]}")

        elif sub in ("bom", "mat", "material"):
            blueprint = tokens[arg_start + 1] if arg_start + 1 < len(tokens) else "sugar_cane"
            scale = 1
            if arg_start + 2 < len(tokens):
                try:
                    scale = int(tokens[arg_start + 2])
                except ValueError:
                    scale = 1
            return self._handle_bom(player_id, blueprint, scale)

        elif sub in ("nether", "portal"):
            return self._handle_nether(player_id, tokens, arg_start + 1, snapshot)

        elif sub in ("clear", "reset"):
            self.session_manager.clear_session(player_id)
            return CommandResult(status="SUCCESS", action="CLEAR", message="§a[Hoshi] 已清空当前会话记忆与翻页缓存。")

        elif sub == "stats":
            return self._handle_stats()

        elif sub == "help":
            return self._handle_help()

        else:
            # Fallback treat as ask
            question = " ".join(tokens[arg_start:])
            return self._handle_ask(player_id, question, snapshot)

    def _handle_inspect(self, player_id: Optional[str], snapshot: Optional[ContextSnapshot]) -> CommandResult:
        if not snapshot:
            return CommandResult(status="ERROR", action="INSPECT", message="§c[Hoshi] 无法获取当前玩家上下文快照。")
        lines = ["§b【Hoshi 准星全维环境感知扫描】§r"]
        has_data = False
        if snapshot.target_block and not snapshot.target_block.is_air:
            has_data = True
            tb = snapshot.target_block
            harvest = tb.evaluate_harvest(snapshot.inventory)
            lines.append(f"▸ §6注视方块§r：{tb.block_id} at [{tb.x}, {tb.y}, {tb.z}]")
            lines.append(f"  光照：方块={tb.block_light}, 天空={tb.sky_light} | 硬度: {tb.hardness:.1f} | 需求工具: {harvest.tool_requirement_name}")
            lines.append(f"  手持匹配：{harvest.advice}")
            log = tb.evaluate_logistics_or_redstone()
            if log.is_logistics_or_redstone:
                lines.append(f"  ⚡ §c红石/物流§r：{log.state_details} | {log.actionable_advice}")
        if snapshot.target_entity:
            has_data = True
            lines.append(f"▸ §d注视实体§r：{snapshot.target_entity.to_summary()}")
        if snapshot.inventory:
            lines.append(f"▸ §e玩家护甲/手持§r：主手={snapshot.main_hand_item} | 护甲防御={snapshot.inventory.total_armor_points}/20 (金装={snapshot.inventory.is_wearing_gold_armor})")
        if not has_data:
            lines.append("▸ §7准星未对准任何方块或实体 (Raycast Miss)。")
        text = "\n".join(lines)
        paged = ChatPaginator.paginate(text, target_page=1, page_size=6, command_prefix="/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi inspect", text, "INSPECT", paged)
        return CommandResult(status="SUCCESS", action="INSPECT", message=text, tellraw_json=paged.tellraw_json, paged_result=paged)

    def _handle_craft(self, player_id: Optional[str], item_name: str, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        report = CraftingReadinessChecker.evaluate(item_name, snapshot.inventory if snapshot else None)
        text = report.formatted_message
        paged = ChatPaginator.paginate(text, target_page=1, page_size=6, command_prefix="/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi craft " + item_name, text, "CRAFT", paged)
        return CommandResult(status="SUCCESS", action="CRAFT", message=text, command_suggestion=report.suggested_command, tellraw_json=paged.tellraw_json, paged_result=paged)

    def _handle_ask(self, player_id: Optional[str], question: str, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        # Check BOM fast match
        bom = MaterialCalculator.match_bom(question)
        if bom:
            formatted = bom.to_formatted_text()
            tellraw = bom.to_tellraw_json()
            paged = ChatPaginator.paginate(formatted, target_page=1, page_size=6, command_prefix="/hoshi page")
            self.session_manager.record_interaction(player_id, question, formatted, bom.blueprint_id, paged)
            return CommandResult(status="SUCCESS", action="BOM", message=formatted, tellraw_json=tellraw, paged_result=paged)

        res: QueryResult = self.dispatcher.dispatch(raw_query=question, context=snapshot, player_id=player_id or "player")
        if res.category == "RATE_LIMITED":
            return CommandResult(status="THROTTLED", action="THROTTLED", message=res.raw_answer)

        paged = ChatPaginator.paginate(res.raw_answer, target_page=1, page_size=6, command_prefix="/hoshi page")
        self.session_manager.record_interaction(player_id, question, res.raw_answer, res.category, paged)
        return CommandResult(
            status="SUCCESS",
            action="ASK",
            message=res.raw_answer,
            command_suggestion=res.suggested_command,
            tellraw_json=paged.tellraw_json,
            paged_result=paged,
        )

    def _handle_page(self, player_id: Optional[str], page: int) -> CommandResult:
        paged = self.session_manager.get_page(player_id, page)
        if not paged:
            return CommandResult(status="ERROR", action="PAGE", message="§c当前没有可翻页的内容，请先向助手提问。")
        return CommandResult(status="SUCCESS", action="PAGE", message=paged.full_page_text, tellraw_json=paged.tellraw_json, paged_result=paged)

    def _handle_bom(self, player_id: Optional[str], blueprint: str, scale: int) -> CommandResult:
        bom = MaterialCalculator.get_bom(blueprint, scale)
        formatted = bom.to_formatted_text()
        tellraw = bom.to_tellraw_json()
        paged = ChatPaginator.paginate(formatted, target_page=1, page_size=6, command_prefix="/hoshi page")
        self.session_manager.record_interaction(player_id, f"bom {blueprint}", formatted, bom.blueprint_id, paged)
        return CommandResult(status="SUCCESS", action="BOM", message=formatted, tellraw_json=tellraw, paged_result=paged)

    def _handle_nether(self, player_id: Optional[str], tokens: list, offset: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        x, y, z = 0, 64, 0
        is_nether = False
        if offset + 2 < len(tokens):
            try:
                x = int(tokens[offset])
                y = int(tokens[offset + 1])
                z = int(tokens[offset + 2])
                if snapshot:
                    is_nether = snapshot.is_nether
            except ValueError:
                return CommandResult(status="ERROR", action="NETHER", message="§c坐标必须为整数: /hoshi nether <x> <y> <z>")
        elif snapshot:
            x = snapshot.block_x
            y = snapshot.block_y
            z = snapshot.block_z
            is_nether = snapshot.is_nether
        else:
            return CommandResult(status="ERROR", action="NETHER", message="§c请提供坐标或确保处于有效维度内: /hoshi nether <x> <y> <z>")

        if is_nether:
            ow_x = x * 8
            ow_z = z * 8
            msg = f"§6【下界 ➔ 主界对应坐标】§r\n▸ 下界 [{x}, {y}, {z}] ➔ 主界 §a[{ow_x}, {y}, {ow_z}]§r (8倍)"
            cmd = f"/tp {ow_x} {y} {ow_z}"
            comps = MinecraftTextFormatter.parse_components(msg, cmd)
            tellraw = TellrawJsonBuilder.to_json(comps)
            return CommandResult(status="SUCCESS", action="NETHER", message=msg, command_suggestion=cmd, tellraw_json=tellraw)
        else:
            nx = math.floor(x / 8.0)
            nz = math.floor(z / 8.0)
            msg = f"§c【主界 ➔ 下界对应坐标】§r\n▸ 主界 [{x}, {y}, {z}] ➔ 下界 §e[{nx}, {y}, {nz}]§r (1/8)"
            cmd = f"/tp {nx} {y} {nz}"
            comps = MinecraftTextFormatter.parse_components(msg, cmd)
            tellraw = TellrawJsonBuilder.to_json(comps)
            return CommandResult(status="SUCCESS", action="NETHER", message=msg, command_suggestion=cmd, tellraw_json=tellraw)

    def _handle_stats(self) -> CommandResult:
        cache_stats = str(self.dispatcher.cache.get_stats()) if self.dispatcher.cache else "N/A"
        active = self.session_manager.active_session_count
        msg = f"§b【Hoshi AI 运行时度量】§r\n▸ 缓存统计: §a{cache_stats}§r\n▸ 活跃会话数: §e{active}§r\n▸ 响应状态: §a正常运行§r"
        return CommandResult(status="SUCCESS", action="STATS", message=msg)

    def _handle_help(self) -> CommandResult:
        text = (
            "§6【Hoshi 智能问答指令帮助】§r\n"
            "▸ §e/hoshi ask <问题>§r - 咨询游戏机制与攻略\n"
            "▸ §e/hoshi bom <方案> [数量]§r - 生成材料清单 (BOM)\n"
            "▸ §e/hoshi page <页码>§r - 翻页长篇内容\n"
            "▸ §e/hoshi nether [x y z]§r - 换算地狱传送门坐标\n"
            "▸ §e/hoshi clear§r - 清理会话与翻页缓存\n"
            "▸ §e/hoshi stats§r - 查看缓存与度量统计\n"
            "§7公屏输入 '!问题' 也可直接提问。§r"
        )
        comps = MinecraftTextFormatter.parse_components(text, "/hoshi help")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="HELP", message=text, tellraw_json=tellraw)
