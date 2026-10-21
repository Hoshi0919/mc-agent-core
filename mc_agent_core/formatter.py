import re
from dataclasses import dataclass
from typing import List, Optional

BOLD_PATTERN = re.compile(r"\*\*(.*?)\*\*")
CODE_PATTERN = re.compile(r"`(.*?)`")
COORD_PATTERN = re.compile(r"\[(-?\d+),\s*(-?\d+),\s*(-?\d+)\]")


@dataclass(frozen=True)
class ChatComponent:
    text: str
    color: str = "white"
    bold: bool = False
    italic: bool = False
    click_action: Optional[str] = None
    click_value: Optional[str] = None
    hover_text: Optional[str] = None


class MinecraftTextFormatter:
    PREFIX = "§b[Hoshi]§r "

    @staticmethod
    def to_section_string(text: Optional[str]) -> str:
        if not text:
            return ""
        res = BOLD_PATTERN.sub(r"§l\1§r", text)
        res = CODE_PATTERN.sub(r"§e\1§r", res)
        return res

    @staticmethod
    def parse_components(raw_text: Optional[str], default_suggested_command: Optional[str] = None) -> List[ChatComponent]:
        components: List[ChatComponent] = []
        if not raw_text:
            return components

        # Add prefix
        components.append(
            ChatComponent(
                text="[Hoshi] ",
                color="aqua",
                bold=True,
                hover_text="AI In-Game Assistant"
            )
        )

        last_end = 0
        for match in COORD_PATTERN.finditer(raw_text):
            start, end = match.span()
            if start > last_end:
                segment = raw_text[last_end:start]
                components.append(ChatComponent(text=segment, color="white"))

            coord_str = match.group(0)
            x = int(match.group(1))
            y = int(match.group(2))
            z = int(match.group(3))
            tp_cmd = f"/tp {x} {y} {z}"

            components.append(
                ChatComponent(
                    text=coord_str,
                    color="gold",
                    bold=True,
                    click_action="SUGGEST_COMMAND",
                    click_value=tp_cmd,
                    hover_text=f"点击将传送指令填入聊天框: {tp_cmd}",
                )
            )
            last_end = end

        if last_end < len(raw_text):
            remainder = raw_text[last_end:]
            components.append(ChatComponent(text=remainder, color="white"))

        if default_suggested_command:
            components.append(ChatComponent(text="\n", color="white"))
            components.append(
                ChatComponent(
                    text=f" [▸ 点击执行/填入: {default_suggested_command}]",
                    color="green",
                    bold=True,
                    click_action="SUGGEST_COMMAND",
                    click_value=default_suggested_command,
                    hover_text=f"点击填入指令: {default_suggested_command}",
                )
            )

        return components
