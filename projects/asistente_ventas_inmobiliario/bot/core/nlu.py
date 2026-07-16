from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import anthropic
from pydantic import BaseModel, ValidationError

from .exceptions import InvalidFiltersError, LLMProviderError, NLUExtractionError
from .models import SearchFilters, SortOption
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
    Nunca produce SQL; el QueryBuilder es el único responsable de eso."""

    @abstractmethod
    async def extract(self, text: str, session: ConversationSession | None) -> ExtractedIntent: ...


_EXTRACT_TOOL = {
    "name": "extract_search_intent",
    "description": (
        "Extrae la intención y los filtros de búsqueda de departamentos a partir del "
        "mensaje del usuario y, si existe, de la búsqueda activa en la sesión."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": [i.value for i in Intent]},
            "filters": {
                "type": "object",
                "properties": {
                    "zona": {"type": ["string", "null"]},
                    "operacion": {"type": ["string", "null"], "enum": ["alquiler", "venta", None]},
                    "tipo": {"type": ["string", "null"], "enum": ["departamento", "casa", None]},
                    "precio_min": {"type": ["number", "null"]},
                    "precio_max": {"type": ["number", "null"]},
                    "habitaciones": {"type": ["integer", "null"]},
                    "banos": {"type": ["integer", "null"]},
                    "area_min_m2": {"type": ["number", "null"]},
                    "amenities": {"type": "array", "items": {"type": "string"}},
                    "sort": {"type": "string", "enum": [s.value for s in SortOption]},
                },
            },
            "clarification_question": {"type": ["string", "null"]},
        },
        "required": ["intent"],
    },
}


class AnthropicIntentExtractor(IntentExtractor):
    def __init__(self, client: anthropic.AsyncAnthropic, model: str = "claude-sonnet-5") -> None:
        self._client = client
        self._model = model

    async def extract(self, text: str, session: ConversationSession | None) -> ExtractedIntent:
        context = ""
        if session is not None and session.filters is not None:
            context = f"\nBúsqueda activa en la sesión: {session.filters.model_dump_json()}"

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                tools=[_EXTRACT_TOOL],
                tool_choice={"type": "tool", "name": _EXTRACT_TOOL["name"]},
                messages=[{"role": "user", "content": f"{text}{context}"}],
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(str(exc)) from exc

        tool_use = next((block for block in response.content if block.type == "tool_use"), None)
        if tool_use is None:
            raise NLUExtractionError("El LLM no devolvió una extracción estructurada")

        try:
            return ExtractedIntent.model_validate(tool_use.input)
        except ValidationError as exc:
            raise InvalidFiltersError(str(exc)) from exc
