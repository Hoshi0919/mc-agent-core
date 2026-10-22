import math
from dataclasses import dataclass
from typing import List, Optional
from mc_agent_core.formatter import ChatComponent
from mc_agent_core.tellraw import TellrawJsonBuilder


@dataclass(frozen=True)
class PagedResult:
    current_page: int
    total_pages: int
    page_size: int
    total_lines: int
    page_lines: List[str]
    full_page_text: str
    components: List[ChatComponent]
    tellraw_json: str


class ChatPaginator:
    """
    Paginates multiline Q&A responses into pages with interactive clickable tellraw buttons.
    """

    DEFAULT_PAGE_SIZE = 5
    DEFAULT_PAGE_CMD_PREFIX = "/mcagent page"

    @staticmethod
    def paginate(
        raw_text: Optional[str],
        target_page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        command_prefix: str = DEFAULT_PAGE_CMD_PREFIX,
    ) -> PagedResult:
        if page_size <= 0:
            page_size = ChatPaginator.DEFAULT_PAGE_SIZE
        prefix = command_prefix.strip() if command_prefix and command_prefix.strip() else ChatPaginator.DEFAULT_PAGE_CMD_PREFIX

        all_lines: List[str] = []
        if raw_text and raw_text.strip():
            all_lines = raw_text.splitlines()

        total_lines = len(all_lines)
        total_pages = max(1, math.ceil(total_lines / page_size))
        page = max(1, min(target_page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_lines)
        current_lines = all_lines[start_idx:end_idx] if start_idx < total_lines else ["§7(本页无内容)§r"]

        page_text_lines = [f"§b[Hoshi 助手]§7 (第 {page}/{total_pages} 页)§r"]
        page_text_lines.extend(current_lines)
        full_page_text = "\n".join(page_text_lines) + "\n"

        components: List[ChatComponent] = [
            ChatComponent(
                text=f"[Hoshi 助手] (第 {page}/{total_pages} 页)\n",
                color="aqua",
                bold=True,
                hover_text="Minecraft Agent Paged View",
            )
        ]

        for line in current_lines:
            components.append(ChatComponent(text=line + "\n", color="white"))

        if total_pages > 1:
            components.append(ChatComponent(text="§8[ ", color="dark_gray"))

            if page > 1:
                components.append(
                    ChatComponent(
                        text="◀ 上一页",
                        color="aqua",
                        bold=True,
                        click_action="RUN_COMMAND",
                        click_value=f"{prefix} {page - 1}",
                        hover_text=f"点击翻至第 {page - 1} 页",
                    )
                )
            else:
                components.append(
                    ChatComponent(
                        text="◀ 上一页",
                        color="dark_gray",
                        hover_text="已是第一页",
                    )
                )

            components.append(ChatComponent(text=" §8]  §7[ ", color="dark_gray"))
            components.append(
                ChatComponent(
                    text=f"第 {page}/{total_pages} 页",
                    color="yellow",
                    hover_text=f"共 {total_lines} 行内容",
                )
            )
            components.append(ChatComponent(text=" §7]  §8[ ", color="dark_gray"))

            if page < total_pages:
                components.append(
                    ChatComponent(
                        text="下一页 ▶",
                        color="aqua",
                        bold=True,
                        click_action="RUN_COMMAND",
                        click_value=f"{prefix} {page + 1}",
                        hover_text=f"点击翻至第 {page + 1} 页",
                    )
                )
            else:
                components.append(
                    ChatComponent(
                        text="下一页 ▶",
                        color="dark_gray",
                        hover_text="已是最后一页",
                    )
                )

            components.append(ChatComponent(text=" §8]\n", color="dark_gray"))

        tellraw_json = TellrawJsonBuilder.to_json(components)
        return PagedResult(
            current_page=page,
            total_pages=total_pages,
            page_size=page_size,
            total_lines=total_lines,
            page_lines=current_lines,
            full_page_text=full_page_text,
            components=components,
            tellraw_json=tellraw_json,
        )
