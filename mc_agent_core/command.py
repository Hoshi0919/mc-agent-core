from typing import Optional, Any
from .spatial import SpatialDirectivePacket, SpatialDirectiveGenerator
import math
from dataclasses import dataclass
from typing import Optional
from .bom import BlueprintBOM, MaterialCalculator
from .context import ContextSnapshot
from .crafting import CraftingReadinessChecker
from .multiblock import find_blueprint, validate_inventory
from .pipeline import analyze_smelting_array
from .farm import evaluate_mob_farm, evaluate_spawner
from .villager import diagnose_iron_farm, diagnose_breeder, diagnose_trading
from .anvil import optimize_anvil_tree
from .create_kinetics import analyze_create_network, MachineEntry
from .chunkload import evaluate_portal_alignment, analyze_permaloader
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
    spatial_directive: Optional[Any] = None

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"

    @property
    def has_spatial_directive(self) -> bool:
        return self.spatial_directive is not None and not self.spatial_directive.is_empty()


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

        elif sub in ("multiblock", "mb"):
            bp_name = tokens[arg_start + 1] if arg_start + 1 < len(tokens) else "conduit"
            return self._handle_multiblock(player_id, bp_name, snapshot)

        elif sub in ("pipeline", "pipe"):
            machine = tokens[arg_start + 1] if arg_start + 1 < len(tokens) else "furnace"
            count = 16
            if arg_start + 2 < len(tokens):
                try:
                    count = int(tokens[arg_start + 2])
                except ValueError:
                    count = 16
            transport = tokens[arg_start + 3] if arg_start + 3 < len(tokens) else "hopper"
            return self._handle_pipeline(player_id, machine, count, transport)

        elif sub in ("mobfarm", "mf"):
            afk_y = 120.0
            farm_y = 64.0
            caves_lit = False
            if arg_start + 1 < len(tokens):
                try: afk_y = float(tokens[arg_start + 1])
                except ValueError: pass
            if arg_start + 2 < len(tokens):
                try: farm_y = float(tokens[arg_start + 2])
                except ValueError: pass
            if arg_start + 3 < len(tokens):
                caves_lit = tokens[arg_start + 3].lower() in ("true", "1", "yes")
            return self._handle_mobfarm(player_id, afk_y, farm_y, caves_lit)

        elif sub == "spawner":
            dist = 10.0
            light = 0
            if arg_start + 1 < len(tokens):
                try: dist = float(tokens[arg_start + 1])
                except ValueError: pass
            if arg_start + 2 < len(tokens):
                try: light = int(tokens[arg_start + 2])
                except ValueError: pass
            return self._handle_spawner(player_id, dist, light)

        elif sub in ("villager", "v"):
            type_name = tokens[arg_start + 1] if arg_start + 1 < len(tokens) else "iron"
            return self._handle_villager(player_id, type_name, tokens, arg_start)

        elif sub in ("anvil", "enchant"):
            return self._handle_anvil(player_id, tokens, arg_start)

        elif sub in ("create", "kinetics"):
            return self._handle_create(player_id, tokens, arg_start)

        elif sub in ("ae2", "me"):
            return self._handle_ae2(player_id, tokens, arg_start, snapshot)
        elif sub in ("piston", "qc", "bud"):
            return self._handle_piston(player_id, tokens, arg_start, snapshot)
        elif sub in ("comparator", "comp", "sorter"):
            return self._handle_comparator(player_id, tokens, arg_start, snapshot)
        elif sub in ("transmission", "power", "wire"):
            return self._handle_transmission(player_id, tokens, arg_start, snapshot)
        elif sub in ("logic", "latch", "gate", "bulb"):
            return self._handle_logic(player_id, tokens, arg_start, snapshot)
        elif sub in ("cluster", "topo"):
            return self._handle_cluster(player_id, tokens, arg_start, snapshot)
        elif sub in ("highlight", "hl"):
            return self._handle_highlight(player_id, tokens, arg_start, snapshot)
        elif sub in ("chunkloader", "cl"):
            return self._handle_chunkloader(player_id, tokens, arg_start)

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

    def _handle_multiblock(self, player_id: Optional[str], query: str, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        bp = find_blueprint(query)
        if not bp:
            return CommandResult(status="ERROR", action="MULTIBLOCK", message=f"§c未识别的多方块蓝图: {query}。可选: conduit, beacon, nether_portal, end_portal, wither, golem")
        report = validate_inventory(bp, snapshot.inventory if snapshot else None)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi multiblock {bp.id}", text, "MULTIBLOCK", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi multiblock {bp.id}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="MULTIBLOCK", message=paged.full_page_text, command_suggestion=f"/hoshi multiblock {bp.id}", tellraw_json=tellraw, paged_result=paged)

    def _handle_pipeline(self, player_id: Optional[str], machine: str, count: int, transport: str) -> CommandResult:
        report = analyze_smelting_array(count, machine, transport)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi pipeline {machine} {count} {transport}", text, "PIPELINE", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi pipeline {machine} {count} {transport}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="PIPELINE", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_mobfarm(self, player_id: Optional[str], afk_y: float, farm_y: float, caves_lit: bool) -> CommandResult:
        report = evaluate_mob_farm(afk_y, farm_y, caves_lit)
        text = report.formatted_report
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi mobfarm {afk_y:.0f} {farm_y:.0f} {caves_lit}", text, "MOBFARM", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi mobfarm {afk_y:.0f} {farm_y:.0f} {caves_lit}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="MOBFARM", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_spawner(self, player_id: Optional[str], dist: float, light: int) -> CommandResult:
        report = evaluate_spawner(dist, light)
        text = report.formatted_report
        comps = MinecraftTextFormatter.parse_components(text, f"/hoshi spawner {dist:.0f} {light}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="SPAWNER", message=text, tellraw_json=tellraw)

    def _handle_villager(self, player_id: Optional[str], type_name: str, tokens: list[str], arg_start: int) -> CommandResult:
        t = type_name.lower()
        if "iron" in t or "golem" in t or t in ("铁", "刷铁"):
            count = 3
            los = False
            slept = True
            if arg_start + 2 < len(tokens):
                try: count = int(tokens[arg_start + 2])
                except ValueError: pass
            if arg_start + 3 < len(tokens):
                los = tokens[arg_start + 3].lower() in ("true", "1", "yes")
            if arg_start + 4 < len(tokens):
                slept = tokens[arg_start + 4].lower() in ("true", "1", "yes")
            text = diagnose_iron_farm(count, los, slept).formatted_report
        elif "breed" in t or "baby" in t or t == "繁殖":
            food = 6
            beds = True
            ceil_h = 2
            if arg_start + 2 < len(tokens):
                try: food = int(tokens[arg_start + 2])
                except ValueError: pass
            if arg_start + 3 < len(tokens):
                beds = tokens[arg_start + 3].lower() in ("true", "1", "yes")
            if arg_start + 4 < len(tokens):
                try: ceil_h = int(tokens[arg_start + 4])
                except ValueError: pass
            text = diagnose_breeder(food, beds, ceil_h).formatted_report
        else:
            traded = True
            reach = True
            if arg_start + 2 < len(tokens):
                traded = tokens[arg_start + 2].lower() in ("true", "1", "yes")
            if arg_start + 3 < len(tokens):
                reach = tokens[arg_start + 3].lower() in ("true", "1", "yes")
            text = diagnose_trading(traded, reach).formatted_report

        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi villager {type_name}", text, "VILLAGER", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi villager {type_name}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="VILLAGER", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_anvil(self, player_id: Optional[str], tokens: list[str], arg_start: int) -> CommandResult:
        gear_name = tokens[arg_start + 1].lower() if arg_start + 1 < len(tokens) else "netherite_sword"
        enchants = {}
        if arg_start + 2 < len(tokens):
            for token in tokens[arg_start + 2:]:
                parts = token.replace("：", ":").split(":")
                id_ = parts[0].lower()
                lvl = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                enchants[id_] = lvl
        else:
            if "sword" in gear_name or "剑" in gear_name:
                enchants = {"sharpness": 5, "unbreaking": 3, "mending": 1, "looting": 3, "sweeping_edge": 3}
            elif "pickaxe" in gear_name or "镐" in gear_name:
                enchants = {"efficiency": 5, "unbreaking": 3, "fortune": 3, "mending": 1}
            elif "bow" in gear_name or "弓" in gear_name:
                enchants = {"power": 5, "unbreaking": 3, "infinity": 1, "flame": 1}
            else:
                enchants = {"protection": 4, "unbreaking": 3, "mending": 1}

        plan = optimize_anvil_tree(gear_name, enchants)
        text = plan.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi anvil {gear_name}", text, "ANVIL", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi anvil {gear_name}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="ANVIL", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_create(self, player_id: Optional[str], tokens: list[str], arg_start: int) -> CommandResult:
        source = "steam"
        param = 9
        if arg_start + 1 < len(tokens):
            s = tokens[arg_start + 1].lower()
            if s in ("stress", "kinetics"):
                if arg_start + 2 < len(tokens):
                    source = tokens[arg_start + 2]
                if arg_start + 3 < len(tokens) and tokens[arg_start + 3].isdigit():
                    param = int(tokens[arg_start + 3])
            else:
                source = s
                if arg_start + 2 < len(tokens) and tokens[arg_start + 2].isdigit():
                    param = int(tokens[arg_start + 2])

        machines = [
            MachineEntry("crushing_wheel", 4, 64.0),
            MachineEntry("mechanical_press", 2, 64.0),
            MachineEntry("mechanical_arm", 2, 32.0),
            MachineEntry("fluid_pump", 4, 16.0),
        ]
        report = analyze_create_network(source, param, machines)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi create {source}", text, "CREATE", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi create {source}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="CREATE", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_chunkloader(self, player_id: Optional[str], tokens: list[str], arg_start: int) -> CommandResult:
        sub = tokens[arg_start + 1].lower() if arg_start + 1 < len(tokens) else "permaloader"
        if sub in ("portal", "align", "coord"):
            ow_x = float(tokens[arg_start + 2]) if arg_start + 2 < len(tokens) else 800.0
            ow_z = float(tokens[arg_start + 3]) if arg_start + 3 < len(tokens) else -1600.0
            n_x = float(tokens[arg_start + 4]) if arg_start + 4 < len(tokens) else 100.0
            n_z = float(tokens[arg_start + 5]) if arg_start + 5 < len(tokens) else -200.0
            text = evaluate_portal_alignment(ow_x, 64.0, ow_z, n_x, 64.0, n_z).format_report()
        else:
            interval = float(tokens[arg_start + 2]) if arg_start + 2 < len(tokens) else 10.0
            trans = tokens[arg_start + 3] if arg_start + 3 < len(tokens) else "hopper_dropper_clock"
            text = analyze_permaloader(interval, trans).format_report()

        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, f"/hoshi chunkloader {sub}", text, "CHUNKLOADER", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, f"/hoshi chunkloader {sub}")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="CHUNKLOADER", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged)

    def _handle_stats(self) -> CommandResult:
        cache_stats = str(self.dispatcher.cache.get_stats()) if self.dispatcher.cache else "N/A"
        active = self.session_manager.active_session_count
        msg = f"§b【Hoshi AI 运行时度量】§r\n▸ 缓存统计: §a{cache_stats}§r\n▸ 活跃会话数: §e{active}§r\n▸ 响应状态: §a正常运行§r"
        return CommandResult(status="SUCCESS", action="STATS", message=msg)



    def _handle_cluster(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        sub = tokens[arg_start + 1].lower() if arg_start + 1 < len(tokens) else "all"
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None

        if not cluster or cluster.is_empty:
            msg = ("§6【局部机器拓扑诊断】§r\n"
                   "当前准星未捕捉到局部多方块机器集群数据。\n"
                   "支持子诊断：\n"
                   "▸ §e/hoshi cluster kinetics§r - 诊断 Create 机械动力齿轮卡死与反向啮合\n"
                   "▸ §e/hoshi cluster hopper§r - 诊断漏斗流水线死锁环路、背压与分类器串线\n"
                   "▸ §e/hoshi cluster ae2§r - 诊断 AE2 数字化网络拓扑与频道过载\n"
                   "▸ §e/hoshi cluster piston§r - 诊断活塞准连接 (QC) 与推块链动力学\n"
                   "▸ §e/hoshi cluster crafter§r - 诊断 1.21 自动合成器槽位遮罩与脉冲时钟")
            return CommandResult(status="SUCCESS", action="CLUSTER", message=msg)

        sb = []
        sb.append(f"§6【局部机器集群拓扑诊断 ({sub.upper()})】§r")
        sb.append(f"▸ 集群中心：{cluster.origin} | 包含方块：{cluster.size} 个")

        if sub in ("kinetics", "all"):
            from mc_agent_core.cluster import KineticNetworkAnalyzer
            k = KineticNetworkAnalyzer.analyze(cluster)
            sb.append(f"▸ 动力状态：{k.primary_diagnosis}")
            if k.is_jammed:
                for c in k.conflicts:
                    sb.append(f"  ✖ {c}")
                sb.append(f"  建议：{k.actionable_remediation}")

        if sub in ("ae2", "all"):
            from mc_agent_core.cluster import Ae2NetworkAnalyzer
            a = Ae2NetworkAnalyzer.analyze(cluster)
            if a.total_controllers > 0 or a.total_cables > 0 or a.total_devices > 0:
                sb.append(f"▸ AE2 网络：{a.primary_diagnosis}")
                for iss in a.issues:
                    sb.append(f"  ✖ {iss}")
                sb.append(f"  建议：{a.actionable_remediation}")

        if sub in ("comparator", "sorter", "all"):
            from mc_agent_core.cluster import ComparatorRedstoneAnalyzer
            c = ComparatorRedstoneAnalyzer.analyze(cluster, cluster.origin)
            if cluster.get_connected_comparators():
                sb.append(f"▸ 比较器状态：{c.primary_diagnosis}")
                for iss in c.issues:
                    sb.append(f"  ✖ {iss}")
                sb.append(f"  建议：{c.actionable_advice}")

        if sub in ("piston", "qc", "all"):
            from mc_agent_core.cluster import PistonRedstoneAnalyzer
            p = PistonRedstoneAnalyzer.analyze(cluster)
            if cluster.get_connected_pistons():
                sb.append(f"▸ 活塞动力：{p.primary_diagnosis}")
                for iss in p.issues:
                    sb.append(f"  ✖ {iss}")
                sb.append(f"  建议：{p.actionable_advice}")

        if sub in ("hopper", "all"):
            from mc_agent_core.cluster import HopperNetworkAnalyzer
            h = HopperNetworkAnalyzer.analyze(cluster)
            sb.append(f"▸ 物流状态：{h.primary_diagnosis}")
            if h.has_deadlock:
                for d in h.deadlocks:
                    sb.append(f"  ⚡ {d}")
            if h.warnings:
                for w in h.warnings:
                    sb.append(f"  ⚠ {w}")
            sb.append(f"  建议：{h.actionable_advice}")

        packet = None
        if sub == "kinetics":
            from mc_agent_core.cluster import KineticNetworkAnalyzer
            k = KineticNetworkAnalyzer.analyze(cluster)
            packet = SpatialDirectiveGenerator.generate_kinetic_overlay(cluster, k)
        elif sub == "ae2":
            from mc_agent_core.cluster import Ae2NetworkAnalyzer
            a = Ae2NetworkAnalyzer.analyze(cluster)
            packet = SpatialDirectiveGenerator.generate_ae2_overlay(cluster, a)
        elif sub in ("piston", "qc"):
            from mc_agent_core.cluster import PistonRedstoneAnalyzer
            p = PistonRedstoneAnalyzer.analyze(cluster)
            packet = SpatialDirectiveGenerator.generate_piston_overlay(cluster, p)
        elif sub in ("transmission", "power", "wire"):
            from mc_agent_core.cluster import RedstoneTransmissionAnalyzer, BlockPos
            t_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
            t = RedstoneTransmissionAnalyzer.analyze(cluster, t_pos)
            packet = SpatialDirectiveGenerator.generate_transmission_overlay(cluster, t)
        elif sub in ("logic", "latch", "gate", "bulb"):
            from mc_agent_core.cluster import RedstoneLogicAnalyzer, BlockPos
            focus_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
            l = RedstoneLogicAnalyzer.analyze(cluster, focus_pos)
            packet = SpatialDirectiveGenerator.generate_logic_overlay(cluster, l)
        elif sub in ("comparator", "sorter"):
            from mc_agent_core.cluster import ComparatorRedstoneAnalyzer
            c = ComparatorRedstoneAnalyzer.analyze(cluster, cluster.origin)
            packet = SpatialDirectiveGenerator.generate_comparator_overlay(cluster, c)
        elif sub == "hopper":
            from mc_agent_core.cluster import HopperNetworkAnalyzer
            h = HopperNetworkAnalyzer.analyze(cluster)
            packet = SpatialDirectiveGenerator.generate_hopper_overlay(cluster, h)
        elif sub == "all":
            from mc_agent_core.cluster import KineticNetworkAnalyzer, HopperNetworkAnalyzer
            k = KineticNetworkAnalyzer.analyze(cluster)
            h = HopperNetworkAnalyzer.analyze(cluster)
            if k.is_jammed:
                packet = SpatialDirectiveGenerator.generate_kinetic_overlay(cluster, k)
            elif h.has_deadlock or h.has_backpressure or h.has_bleed_risk:
                packet = SpatialDirectiveGenerator.generate_hopper_overlay(cluster, h)

        return CommandResult(status="SUCCESS", action="CLUSTER", message="\n".join(sb), spatial_directive=packet)


    def _handle_logic(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
        if not cluster or cluster.is_empty:
            msg = ("§e【红石时序逻辑与门电路因果诊断】§r\n"
                   "当前准星未捕捉到局部红石门电路、锁存器或触发器集群。\n"
                   "请将准星对准 1.21 铜球、红石火把、粘性活塞或门电路，然后输入 `/hoshi logic` 触发双稳态与时序因果分析！")
            return CommandResult(status="SUCCESS", action="LOGIC", message=msg)
        from mc_agent_core.cluster import RedstoneLogicAnalyzer, BlockPos
        target_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
        report = RedstoneLogicAnalyzer.analyze(cluster, target_pos)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi logic", text, "LOGIC", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, "/hoshi logic")
        tellraw = TellrawJsonBuilder.to_json(comps)
        pkt = SpatialDirectiveGenerator.generate_logic_overlay(cluster, report)
        return CommandResult(status="SUCCESS", action="LOGIC", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged, spatial_directive=pkt)
    def _handle_transmission(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
        if not cluster or cluster.is_empty:
            msg = ("§e【红石传输拓扑与充能因果诊断】§r\n"
                   "当前准星未捕捉到局部红石导线、火把或供电集群。\n"
                   "请将准星对准红石粉、红石火把、中继器或受电方块，然后再次输入 `/hoshi transmission` 触发传输物理与强弱充能分析！")
            return CommandResult(status="SUCCESS", action="TRANSMISSION", message=msg)
        from mc_agent_core.cluster import RedstoneTransmissionAnalyzer, BlockPos
        target_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
        report = RedstoneTransmissionAnalyzer.analyze(cluster, target_pos)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi transmission", text, "TRANSMISSION", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, "/hoshi transmission")
        tellraw = TellrawJsonBuilder.to_json(comps)
        pkt = SpatialDirectiveGenerator.generate_transmission_overlay(cluster, report)
        return CommandResult(status="SUCCESS", action="TRANSMISSION", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged, spatial_directive=pkt)

    def _handle_comparator(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
        if not cluster or cluster.is_empty or not cluster.get_connected_comparators():
            msg = ("§e【红石比较器与容器分类诊断】§r\n"
                   "当前准星未捕捉到局部比较器或分类机漏斗集群。\n"
                   "请将准星对准红石比较器、漏斗或红石粉，然后再次输入 `/hoshi comparator` 触发容器信号与防串扰诊断！")
            return CommandResult(status="SUCCESS", action="COMPARATOR", message=msg)
        from mc_agent_core.cluster import ComparatorRedstoneAnalyzer
        report = ComparatorRedstoneAnalyzer.analyze(cluster, cluster.origin)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi comparator", text, "COMPARATOR", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, "/hoshi comparator")
        tellraw = TellrawJsonBuilder.to_json(comps)
        pkt = SpatialDirectiveGenerator.generate_comparator_overlay(cluster, report)
        return CommandResult(status="SUCCESS", action="COMPARATOR", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged, spatial_directive=pkt)

    def _handle_piston(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
        if not cluster or cluster.is_empty or not cluster.get_connected_pistons():
            msg = ("§e【红石活塞与准连接 (QC) 诊断】§r\n"
                   "当前准星未捕捉到局部活塞或红石机械集群。\n"
                   "请将准星对准活塞、粘性活塞或其相邻红石方块，然后再次输入 `/hoshi piston` 触发准连接 (QC) 与推块链动力学诊断！")
            return CommandResult(status="SUCCESS", action="PISTON", message=msg)
        from mc_agent_core.cluster import PistonRedstoneAnalyzer
        report = PistonRedstoneAnalyzer.analyze(cluster)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi piston", text, "PISTON", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, "/hoshi piston")
        tellraw = TellrawJsonBuilder.to_json(comps)
        pkt = SpatialDirectiveGenerator.generate_piston_overlay(cluster, report)
        return CommandResult(status="SUCCESS", action="PISTON", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged, spatial_directive=pkt)

    def _handle_ae2(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
        if not cluster or cluster.is_empty:
            msg = ("§b【AE2 数字化网络诊断】§r\n"
                   "当前准星未捕捉到局部 AE2 机器或线缆集群。\n"
                   "请将准星对准 ME 控制器、线缆、驱动器或终端方块，然后再次输入 `/hoshi ae2` 触发实时图论与频道分析！")
            return CommandResult(status="SUCCESS", action="AE2", message=msg)
        from mc_agent_core.cluster import Ae2NetworkAnalyzer
        report = Ae2NetworkAnalyzer.analyze(cluster)
        text = report.format_report()
        paged = ChatPaginator.paginate(text, 1, 6, "/hoshi page")
        self.session_manager.record_interaction(player_id, "/hoshi ae2", text, "AE2", paged)
        comps = MinecraftTextFormatter.parse_components(paged.full_page_text, "/hoshi ae2")
        tellraw = TellrawJsonBuilder.to_json(comps)
        pkt = SpatialDirectiveGenerator.generate_ae2_overlay(cluster, report)
        return CommandResult(status="SUCCESS", action="AE2", message=paged.full_page_text, tellraw_json=tellraw, paged_result=paged, spatial_directive=pkt)

    def _handle_highlight(self, player_id: Optional[str], tokens: list, arg_start: int, snapshot: Optional[ContextSnapshot]) -> CommandResult:
        sub = tokens[arg_start + 1].lower() if arg_start + 1 < len(tokens) else "help"

        if sub in ("clear", "reset"):
            pkt = SpatialDirectivePacket.clear("ALL")
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message="§a[Hoshi] 已发送清除所有空间高亮覆盖层指令。", spatial_directive=pkt)

        if sub in ("kinetics", "create", "gear"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到局部机械动力组件，无法投射动力高亮。")
            from mc_agent_core.cluster import KineticNetworkAnalyzer
            k = KineticNetworkAnalyzer.analyze(cluster)
            pkt = SpatialDirectiveGenerator.generate_kinetic_overlay(cluster, k)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("transmission", "power", "wire"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到红石传输组件，无法投射传输高亮。")
            from mc_agent_core.cluster import RedstoneTransmissionAnalyzer, BlockPos
            t_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
            t = RedstoneTransmissionAnalyzer.analyze(cluster, t_pos)
            pkt = SpatialDirectiveGenerator.generate_transmission_overlay(cluster, t)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("logic", "latch", "gate", "bulb"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到红石逻辑组件，无法投射逻辑高亮。")
            from mc_agent_core.cluster import RedstoneLogicAnalyzer, BlockPos
            focus_pos = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z) if (snapshot and snapshot.target_block) else cluster.origin
            l = RedstoneLogicAnalyzer.analyze(cluster, focus_pos)
            pkt = SpatialDirectiveGenerator.generate_logic_overlay(cluster, l)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("comparator", "sorter", "comp"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty or not cluster.get_connected_comparators():
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到局部比较器组件，无法投射比较器高亮。")
            from mc_agent_core.cluster import ComparatorRedstoneAnalyzer
            c = ComparatorRedstoneAnalyzer.analyze(cluster, cluster.origin)
            pkt = SpatialDirectiveGenerator.generate_comparator_overlay(cluster, c)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("piston", "qc", "bud"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty or not cluster.get_connected_pistons():
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到局部活塞机械组件，无法投射活塞动力高亮。")
            from mc_agent_core.cluster import PistonRedstoneAnalyzer
            p = PistonRedstoneAnalyzer.analyze(cluster)
            pkt = SpatialDirectiveGenerator.generate_piston_overlay(cluster, p)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("ae2", "me"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到局部 AE2 数字化网络组件，无法投射 AE2 高亮。")
            from mc_agent_core.cluster import Ae2NetworkAnalyzer
            a = Ae2NetworkAnalyzer.analyze(cluster)
            pkt = SpatialDirectiveGenerator.generate_ae2_overlay(cluster, a)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("hopper", "pipe"):
            cluster = getattr(snapshot, "machine_cluster", None) if snapshot else None
            if not cluster or cluster.is_empty:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message="§c准星未捕捉到漏斗物流组件，无法投射物流高亮。")
            from mc_agent_core.cluster import HopperNetworkAnalyzer
            h = HopperNetworkAnalyzer.analyze(cluster)
            pkt = SpatialDirectiveGenerator.generate_hopper_overlay(cluster, h)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("mobfarm", "spheres"):
            px = snapshot.x if snapshot else 0.0
            py = snapshot.y if snapshot else 64.0
            pz = snapshot.z if snapshot else 0.0
            pkt = SpatialDirectiveGenerator.generate_mob_farm_overlay(px, py, pz)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 高亮] {pkt.hud_title}", spatial_directive=pkt)

        if sub in ("multiblock", "mb", "ghost"):
            query = tokens[arg_start + 2] if arg_start + 2 < len(tokens) else "conduit"
            bp = find_blueprint(query)
            if not bp:
                return CommandResult(status="ERROR", action="HIGHLIGHT", message=f"§c未识别的多方块蓝图: {query}")
            from .cluster import BlockPos
            if snapshot and snapshot.target_block and not snapshot.target_block.is_air:
                center = BlockPos(snapshot.target_block.x, snapshot.target_block.y, snapshot.target_block.z)
            elif snapshot:
                center = BlockPos(int(snapshot.x), int(snapshot.y), int(snapshot.z))
            else:
                center = BlockPos(0, 64, 0)
            pkt = SpatialDirectiveGenerator.generate_multiblock_ghost_overlay(bp, center)
            return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=f"§a[Hoshi 3D 虚影] {pkt.hud_title}", spatial_directive=pkt)

        msg = ("§6【Hoshi 3D 空间全息高亮指令】§r\n"
               "▸ §e/hoshi highlight kinetics§r - 在游戏世界高亮冲突齿轮与流向\n"
               "▸ §e/hoshi highlight hopper§r - 投射漏斗死锁环路与物流方向箭头\n"
               "▸ §e/hoshi highlight transmission§r - 投射红石火把烧毁高危、弱充能阻断点与偏转断路导线\n"
            "▸ §e/hoshi highlight logic§r - 投射锁存器冲突、活塞脉宽失配与 1.21 铜球触发器全息覆盖层\n" +
               "▸ §e/hoshi highlight comparator§r - 投射比较器信号、串扰高危线路与漏斗负载\n" +
               "▸ §e/hoshi highlight piston§r - 投射准连接 QC 隔电源、BUD 锁定与推块超载\n"
               "▸ §e/hoshi highlight multiblock <名称>§r - 在准星位置投射多方块虚影蓝图\n"
               "▸ §e/hoshi highlight mobfarm§r - 以自身为中心投射 24/32/128m 刷怪动力学清除圈\n"
               "▸ §e/hoshi highlight clear§r - 清除所有世界高亮与全息虚影")
        return CommandResult(status="SUCCESS", action="HIGHLIGHT", message=msg)

    def _handle_help(self) -> CommandResult:
        text = (
            "§6【Hoshi 智能问答指令帮助】§r\n"
            "▸ §e/hoshi ask <问题>§r - 咨询游戏机制与攻略\n"
            "▸ §e/hoshi inspect§r - 扫描准星方块、红石物流状态与实体安全\n"
            "▸ §e/hoshi craft <物品>§r - 评估背包原料是否满足合成条件及缺失数量\n"
            "▸ §e/hoshi multiblock <方案>§r - 调阅多方块蓝图与背包材料校验\n"
            "▸ §e/hoshi pipeline <设备> [数量] [物流]§r - 诊断工业流水线供料瓶颈\n"
            "▸ §e/hoshi mobfarm <挂机Y> <平台Y> [洞穴点亮]§r - 诊断清除球与生物Cap占用\n"
            "▸ §e/hoshi villager <iron/breeder/trading>§r - 诊断刷铁机/繁殖/工作站死锁\n"
            "▸ §e/hoshi bom <方案> [数量]§r - 生成材料清单 (BOM)\n"
            "▸ §e/hoshi page <页码>§r - 翻页长篇内容\n"
            "▸ §e/hoshi anvil <装备> [附魔:等级...]§r - 规划二叉树最优附魔工序规避过于昂贵\n"
            "▸ §e/hoshi create stress <动力源> [规模]§r - 诊断 Create 模组动力网应力与过载转速\n"
            "▸ §e/hoshi ae2§r - 诊断准星 AE2 数字化网络拓扑、控制器合法性与 8/32 频道溢出\n"
            "▸ §e/hoshi transmission§r - 诊断红石火把极速自激烧毁、强弱充能传递阻断与导线偏转断路\n"
            "▸ §e/hoshi logic§r - 诊断 RS-NOR 保持锁存器竞争、活塞 1 刻吐方块脉宽与 1.21 铜球状态机\n" +
            "▸ §e/hoshi comparator§r - 诊断准星比较器信号强度、分类机满溢串扰与防溢出保护\n" +
            "▸ §e/hoshi piston§r - 诊断准星活塞准连接 (QC)、BUD 锁定与推块链超载\n"
            "▸ §e/hoshi highlight ae2§r - 投射 AE2 频道过载红线与掉线设备 3D 空间全息覆盖层\n"
            "▸ §e/hoshi cluster - 诊断局部机器拓扑\n▸ §e/hoshi chunkloader <permaloader/portal>§r - 诊断生电传送门常载网与 8:1 坐标漂移\n"
            "▸ §e/hoshi nether [x y z]§r - 换算地狱传送门坐标\n"
            "▸ §e/hoshi clear§r - 清理会话与翻页缓存\n"
            "▸ §e/hoshi stats§r - 查看缓存与度量统计\n"
            "§7公屏输入 '!问题' 也可直接提问。§r"
        )
        comps = MinecraftTextFormatter.parse_components(text, "/hoshi help")
        tellraw = TellrawJsonBuilder.to_json(comps)
        return CommandResult(status="SUCCESS", action="HELP", message=text, tellraw_json=tellraw)
