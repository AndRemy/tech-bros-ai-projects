from __future__ import annotations

import os

import anthropic
from pydantic import ValidationError

from ..core.exceptions import InvalidFiltersError, LLMProviderError, NLUExtractionError
from ..core.models import RankedResult, SortOption
from ..core.nlu import (
    EXTRACT_TOOL_DESCRIPTION,
    EXTRACT_TOOL_NAME,
    ExtractedIntent,
    Intent,
    IntentExtractor,
    build_session_context,
)
from ..core.responder import NO_RESULTS_MESSAGE, SYSTEM_PROMPT, ResponseGenerator, build_prompt
from ..core.session import ConversationSession

_EXTRACT_TOOL = {
    "name": EXTRACT_TOOL_NAME,
    "description": EXTRACT_TOOL_DESCRIPTION,
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
        context = build_session_context(session)

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                tools=[_EXTRACT_TOOL],
                tool_choice={"type": "tool", "name": EXTRACT_TOOL_NAME},
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


class AnthropicResponseGenerator(ResponseGenerator):
    def __init__(self, client: anthropic.AsyncAnthropic, model: str = "claude-sonnet-5") -> None:
        self._client = client
        self._model = model

    async def generate(self, query_text: str, results: list[RankedResult], has_more: bool) -> str:
        prompt = build_prompt(query_text, results, has_more)
        if prompt is None:
            return NO_RESULTS_MESSAGE

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(str(exc)) from exc

        return "".join(block.text for block in response.content if block.type == "text")


def create_intent_extractor_from_env() -> AnthropicIntentExtractor:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurado en .env")
    return AnthropicIntentExtractor(anthropic.AsyncAnthropic(api_key=api_key))


def create_response_generator_from_env() -> AnthropicResponseGenerator:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurado en .env")
    return AnthropicResponseGenerator(anthropic.AsyncAnthropic(api_key=api_key))
