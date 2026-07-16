from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

from .models import SearchFilters
from .session import ConversationSession


class Intent(str, Enum):
    NEW_SEARCH = "new_search"
    NEXT_PAGE = "next_page"
    CHANGE_SORT = "change_sort"
    CLARIFICATION_NEEDED = "clarification_needed"
    OUT_OF_SCOPE = "out_of_scope"


class ExtractedIntent(BaseModel):
    intent: Intent
    filters: SearchFilters | None = None
    clarification_question: str | None = None


class IntentExtractor(ABC):
    """Puerto: texto libre del usuario -> intención + filtros estructurados.
    Nunca produce SQL; el QueryBuilder es el único responsable de eso.
    Las implementaciones concretas (una por proveedor de LLM) viven en bot/llm/."""

    @abstractmethod
    async def extract(self, text: str, session: ConversationSession | None) -> ExtractedIntent: ...


EXTRACT_TOOL_NAME = "extract_search_intent"
EXTRACT_TOOL_DESCRIPTION = (
    "Extrae la intención y los filtros de búsqueda de departamentos a partir del "
    "mensaje del usuario y, si existe, de la búsqueda activa en la sesión."
)


def build_session_context(session: ConversationSession | None) -> str:
    if session is None or session.filters is None:
        return ""
    return f"\nBúsqueda activa en la sesión: {session.filters.model_dump_json()}"
