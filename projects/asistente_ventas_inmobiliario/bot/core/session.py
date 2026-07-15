from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .models import SearchFilters


@dataclass
class ConversationSession:
    channel: str
    user_id: str
    filters: SearchFilters | None = None
    offset: int = 0
    last_active_at: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        self.last_active_at = time.monotonic()


class SessionStore(ABC):
    """Puerto para persistir el estado de conversación entre turnos de un mismo
    usuario/canal, identificado por (channel, user_id)."""

    @abstractmethod
    def get(self, channel: str, user_id: str) -> ConversationSession | None: ...

    @abstractmethod
    def save(self, session: ConversationSession) -> None: ...

    @abstractmethod
    def clear(self, channel: str, user_id: str) -> None: ...


class InMemorySessionStore(SessionStore):
    """Implementación de referencia para una sola instancia del bot. Sesiones
    inactivas por más de `ttl_seconds` se tratan como expiradas."""

    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[tuple[str, str], ConversationSession] = {}

    def get(self, channel: str, user_id: str) -> ConversationSession | None:
        key = (channel, user_id)
        session = self._sessions.get(key)
        if session is None:
            return None
        if time.monotonic() - session.last_active_at > self._ttl_seconds:
            del self._sessions[key]
            return None
        return session

    def save(self, session: ConversationSession) -> None:
        session.touch()
        self._sessions[(session.channel, session.user_id)] = session

    def clear(self, channel: str, user_id: str) -> None:
        self._sessions.pop((channel, user_id), None)
