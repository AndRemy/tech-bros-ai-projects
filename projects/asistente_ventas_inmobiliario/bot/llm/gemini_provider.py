from __future__ import annotations

import os

from google import genai
from google.genai import types
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

# Alias que Google mantiene apuntando al modelo flash vigente, en vez de una
# versión fija (gemini-2.0-flash y luego gemini-2.5-flash quedaron
# descontinuadas en el tiempo que duró esta sesión de pruebas).
_MODEL_NAME = "gemini-flash-latest"

# parameters_json_schema acepta JSON Schema estándar (a diferencia de `parameters`,
# que espera el subconjunto OpenAPI propio del SDK) -- mismo shape que usamos para
# Anthropic/OpenAI, incluyendo "type": ["string", "null"] para campos opcionales.
_EXTRACT_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=EXTRACT_TOOL_NAME,
            description=EXTRACT_TOOL_DESCRIPTION,
            parameters_json_schema={
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
        )
    ]
)


class GeminiIntentExtractor(IntentExtractor):
    def __init__(self, client: genai.Client) -> None:
        self._client = client

    async def extract(self, text: str, session: ConversationSession | None) -> ExtractedIntent:
        context = build_session_context(session)

        try:
            response = await self._client.aio.models.generate_content(
                model=_MODEL_NAME,
                contents=f"{text}{context}",
                config=types.GenerateContentConfig(
                    tools=[_EXTRACT_TOOL],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="ANY", allowed_function_names=[EXTRACT_TOOL_NAME]
                        )
                    ),
                ),
            )
        except Exception as exc:  # google-genai no expone una jerarquía de excepciones propia y estable
            raise LLMProviderError(str(exc)) from exc

        function_calls = response.function_calls
        if not function_calls:
            raise NLUExtractionError("El LLM no devolvió una extracción estructurada")

        try:
            return ExtractedIntent.model_validate(function_calls[0].args)
        except ValidationError as exc:
            raise InvalidFiltersError(str(exc)) from exc


class GeminiResponseGenerator(ResponseGenerator):
    def __init__(self, client: genai.Client) -> None:
        self._client = client

    async def generate(self, query_text: str, results: list[RankedResult], has_more: bool) -> str:
        prompt = build_prompt(query_text, results, has_more)
        if prompt is None:
            return NO_RESULTS_MESSAGE

        try:
            response = await self._client.aio.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
        except Exception as exc:
            raise LLMProviderError(str(exc)) from exc

        return response.text or ""


def create_intent_extractor_from_env() -> GeminiIntentExtractor:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no está configurado en .env")
    return GeminiIntentExtractor(genai.Client(api_key=api_key))


def create_response_generator_from_env() -> GeminiResponseGenerator:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no está configurado en .env")
    return GeminiResponseGenerator(genai.Client(api_key=api_key))
