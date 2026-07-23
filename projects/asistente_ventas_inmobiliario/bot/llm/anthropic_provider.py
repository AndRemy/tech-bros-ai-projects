from __future__ import annotations

import os

import anthropic
from pydantic import ValidationError

from ..core.exceptions import InvalidFiltersError, LLMProviderError, NLUExtractionError
from ..core.features import (
    FEATURES_PARAMETERS_SCHEMA,
    FEATURES_SYSTEM_PROMPT,
    FEATURES_TOOL_DESCRIPTION,
    FEATURES_TOOL_NAME,
    FeatureExtractor,
    align_features,
    build_features_prompt,
)
from ..core.models import SortOption
from ..core.nlu import (
    EXTRACT_TOOL_DESCRIPTION,
    EXTRACT_TOOL_NAME,
    ExtractedIntent,
    Intent,
    IntentExtractor,
    build_session_context,
)
from ..core.session import ConversationSession

_FEATURES_TOOL = {
    "name": FEATURES_TOOL_NAME,
    "description": FEATURES_TOOL_DESCRIPTION,
    "input_schema": FEATURES_PARAMETERS_SCHEMA,
}

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
                    "zonas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Una o más zonas/distritos; cualquiera de ellas es un match válido (OR).",
                    },
                    "operacion": {"type": ["string", "null"], "enum": ["alquiler", "venta", None]},
                    "tipo": {"type": ["string", "null"], "enum": ["departamento", "casa", None]},
                    "precio_min": {"type": ["number", "null"]},
                    "precio_max": {"type": ["number", "null"]},
                    "habitaciones": {"type": ["integer", "null"]},
                    "banos": {"type": ["integer", "null"]},
                    "area_min_m2": {"type": ["number", "null"]},
                    "amenities": {"type": "array", "items": {"type": "string"}},
                    "direccion": {
                        "type": ["string", "null"],
                        "description": "Calle, avenida o dirección mencionada por el usuario, si la hay.",
                    },
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


class AnthropicFeatureExtractor(FeatureExtractor):
    def __init__(self, client: anthropic.AsyncAnthropic, model: str = "claude-sonnet-5") -> None:
        self._client = client
        self._model = model

    async def extract(self, descriptions: list[str]) -> list[list[str]]:
        prompt = build_features_prompt(descriptions)
        if prompt is None:
            return [[] for _ in descriptions]

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=FEATURES_SYSTEM_PROMPT,
                tools=[_FEATURES_TOOL],
                tool_choice={"type": "tool", "name": FEATURES_TOOL_NAME},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(str(exc)) from exc

        tool_use = next((block for block in response.content if block.type == "tool_use"), None)
        if tool_use is None:
            return [[] for _ in descriptions]
        return align_features(tool_use.input, len(descriptions))


def create_intent_extractor_from_env() -> AnthropicIntentExtractor:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurado en .env")
    return AnthropicIntentExtractor(anthropic.AsyncAnthropic(api_key=api_key))


def create_feature_extractor_from_env() -> AnthropicFeatureExtractor:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurado en .env")
    return AnthropicFeatureExtractor(anthropic.AsyncAnthropic(api_key=api_key))
