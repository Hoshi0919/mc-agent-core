import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional
from .paginator import ChatPaginator, PagedResult


@dataclass(frozen=True)
class Turn:
    prompt: str
    response: str
    category: str
    timestamp_ms: int


class PlayerSession:
    def __init__(self, player_id: str, max_history_turns: int = 5):
        self.player_id = player_id
        self.max_history_turns = max(1, max_history_turns)
        self.history: deque[Turn] = deque(maxlen=self.max_history_turns)
        self.active_paged_result: Optional[PagedResult] = None
        self.last_active_topic: Optional[str] = None
        self.last_active_time_ms: int = int(time.time() * 1000)

    def record_turn(self, prompt: str, response: str, category: Optional[str], paged: Optional[PagedResult] = None):
        now = int(time.time() * 1000)
        self.last_active_time_ms = now
        if category:
            self.last_active_topic = category
        if paged:
            self.active_paged_result = paged
        self.history.append(Turn(prompt=prompt, response=response, category=category or "", timestamp_ms=now))

    def set_active_paged_result(self, paged: PagedResult):
        self.active_paged_result = paged
        self.last_active_time_ms = int(time.time() * 1000)

    def get_page(self, target_page: int) -> Optional[PagedResult]:
        if not self.active_paged_result:
            return None
        if self.active_paged_result.current_page == target_page:
            return self.active_paged_result

        # Re-paginate using stored raw_text
        new_page = ChatPaginator.paginate(
            self.active_paged_result.raw_text,
            target_page=target_page,
            page_size=self.active_paged_result.page_size,
            command_prefix=self.active_paged_result.command_prefix,
        )
        self.active_paged_result = new_page
        self.last_active_time_ms = int(time.time() * 1000)
        return new_page

    def get_history(self) -> List[Turn]:
        return list(self.history)

    def clear(self):
        self.history.clear()
        self.active_paged_result = None
        self.last_active_topic = None
        self.last_active_time_ms = int(time.time() * 1000)

    def is_expired(self, ttl_ms: int, now_ms: Optional[int] = None) -> bool:
        now = now_ms or int(time.time() * 1000)
        return (now - self.last_active_time_ms) > ttl_ms


class PlayerSessionManager:
    def __init__(self, max_history_turns: int = 5, session_ttl_ms: int = 15 * 60 * 1000):
        self.max_history_turns = max(1, max_history_turns)
        self.session_ttl_ms = max(1000, session_ttl_ms)
        self.sessions: Dict[str, PlayerSession] = {}

    def get_or_create_session(self, player_id: Optional[str]) -> PlayerSession:
        pid = player_id or "global"
        if pid not in self.sessions:
            self.sessions[pid] = PlayerSession(pid, self.max_history_turns)
        return self.sessions[pid]

    def get_session(self, player_id: Optional[str]) -> Optional[PlayerSession]:
        if not player_id:
            return None
        return self.sessions.get(player_id)

    def record_interaction(
        self, player_id: Optional[str], prompt: str, response: str, category: Optional[str], paged: Optional[PagedResult] = None
    ):
        session = self.get_or_create_session(player_id)
        session.record_turn(prompt, response, category, paged)

    def get_page(self, player_id: Optional[str], page_number: int) -> Optional[PagedResult]:
        session = self.get_session(player_id)
        if not session:
            return None
        return session.get_page(page_number)

    def clear_session(self, player_id: Optional[str]):
        if player_id and player_id in self.sessions:
            self.sessions[player_id].clear()
            del self.sessions[player_id]

    def cleanup_expired_sessions(self) -> int:
        now = int(time.time() * 1000)
        expired = [pid for pid, s in self.sessions.items() if s.is_expired(self.session_ttl_ms, now)]
        for pid in expired:
            del self.sessions[pid]
        return len(expired)

    @property
    def active_session_count(self) -> int:
        return len(self.sessions)
