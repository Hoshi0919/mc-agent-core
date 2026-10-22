import json
from typing import List, Optional
from mc_agent_core.formatter import ChatComponent, MinecraftTextFormatter


class TellrawJsonBuilder:
    """
    Serializes ChatComponent objects into standard Vanilla Minecraft /tellraw JSON.
    Compatible with Minecraft 1.16 through 1.21.x.
    """

    @staticmethod
    def to_json(components: List[ChatComponent]) -> str:
        if not components:
            return '{"text":""}'

        extra = []
        for c in components:
            item = {"text": c.text}
            if c.color:
                item["color"] = c.color.lower()
            if c.bold:
                item["bold"] = True
            if c.italic:
                item["italic"] = True
            if c.click_action and c.click_value:
                item["clickEvent"] = {
                    "action": c.click_action.lower(),
                    "value": c.click_value,
                }
            if c.hover_text:
                item["hoverEvent"] = {
                    "action": "show_text",
                    "contents": c.hover_text,
                }
            extra.append(item)

        return json.dumps({"text": "", "extra": extra}, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def to_tellraw_command(target_selector: Optional[str], components: List[ChatComponent]) -> str:
        target = target_selector.strip() if target_selector and target_selector.strip() else "@s"
        return f"/tellraw {target} {TellrawJsonBuilder.to_json(components)}"

    @staticmethod
    def to_tellraw_from_text(target_selector: Optional[str], raw_text: str) -> str:
        components = MinecraftTextFormatter.parse_components(raw_text, None)
        return TellrawJsonBuilder.to_tellraw_command(target_selector, components)
