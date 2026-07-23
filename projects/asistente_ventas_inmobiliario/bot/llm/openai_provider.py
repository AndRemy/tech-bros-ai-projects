from __future__ import annotations

import json
import os

import openai
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
    "type": "function",
    "function": {
        "name": FEATURES_TOOL_NAME,
        "description": FEATURES_TOOL_DESCRIPTION,
        "parameters": FEATURES_PARAMETERS_SCHEMA,
    },
}

_EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": EXTRACT_TOOL_NAME,
        "description": EXTRACT_TOOL_DESCRIPTION,
        "parameters": {
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
    },
}


class OpenAIIntentExtractor(IntentExtractor):
    def __init__(self, client: openai.AsyncOpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    async def extract(self, text: str, session: ConversationSession | None) -> ExtractedIntent:
        context = build_session_context(session)

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": f"{text}{context}"}],
                tools=[_EXTRACT_TOOL],
                tool_choice={"type": "function", "function": {"name": EXTRACT_TOOL_NAME}},
            )
        except openai.OpenAIError as exc:
            raise LLMProviderError(str(exc)) from exc

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise NLUExtractionError("El LLM no devolvió una extracción estructurada")

        try:
            arguments = json.loads(tool_calls[0].function.arguments)
        except json.JSONDecodeError as exc:
            raise InvalidFiltersError(str(exc)) from exc

        try:
            return ExtractedIntent.model_validate(arguments)
        except ValidationError as exc:
            raise InvalidFiltersError(str(exc)) from exc


class OpenAIFeatureExtractor(FeatureExtractor):
    def __init__(self, client: openai.AsyncOpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    async def extract(self, descriptions: list[str]) -> list[list[str]]:
        prompt = build_features_prompt(descriptions)
        if prompt is None:
            return [[] for _ in descriptions]

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": FEATURES_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                tools=[_FEATURES_TOOL],
                tool_choice={"type": "function", "function": {"name": FEATURES_TOOL_NAME}},
            )
        except openai.OpenAIError as exc:
            raise LLMProviderError(str(exc)) from exc

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return [[] for _ in descriptions]
        try:
            arguments = json.loads(tool_calls[0].function.arguments)
        except json.JSONDecodeError:
            return [[] for _ in descriptions]
        return align_features(arguments, len(descriptions))


def create_intent_extractor_from_env() -> OpenAIIntentExtractor:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurado en .env")
    return OpenAIIntentExtractor(openai.AsyncOpenAI(api_key=api_key))


def create_feature_extractor_from_env() -> OpenAIFeatureExtractor:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurado en .env")
    return OpenAIFeatureExtractor(openai.AsyncOpenAI(api_key=api_key))
