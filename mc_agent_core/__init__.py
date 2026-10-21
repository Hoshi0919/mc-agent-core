"""
mc_agent_core: Grounded, Non-blocking In-Game AI Assistant Core for Minecraft (1.18 ~ 1.21.x)
"""

from .context import ContextSnapshot, TargetBlock
from .rules import LocalGameRules
from .fast_path import FastPathResolver, Resolution
from .fence import PromptSafetyFence, FencedPrompt
from .formatter import MinecraftTextFormatter, ChatComponent
from .dispatcher import AsyncQueryDispatcher, QueryResult

__all__ = [
    "ContextSnapshot",
    "TargetBlock",
    "LocalGameRules",
    "FastPathResolver",
    "Resolution",
    "PromptSafetyFence",
    "FencedPrompt",
    "MinecraftTextFormatter",
    "ChatComponent",
    "AsyncQueryDispatcher",
    "QueryResult",
]
