from __future__ import annotations

from abc import ABC, abstractmethod

import anthropic

from .exceptions import LLMProviderError
from .models import RankedResult

_SYSTEM_PROMPT = (
    "Eres un asistente de ventas inmobiliario. Recibes una lista de departamentos "
    "y debes redactar, para cada uno, una descripción de 2 a 3 oraciones en "
    "español, en tono cercano y profesional, resaltando lo que mejor calce con lo "
    "que pidió el usuario. No inventes datos que no estén en la lista."
)


class ResponseGenerator(ABC):
    """Puerto: resultados ya rankeados -> texto en lenguaje natural para el usuario."""

    @abstractmethod
    async def generate(self, query_text: str, results: list[RankedResult], has_more: bool) -> str: ...


class AnthropicResponseGenerator(ResponseGenerator):
    def __init__(self, client: anthropic.AsyncAnthropic, model: str = "claude-sonnet-5") -> None:
        self._client = client
        self._model = model

    async def generate(self, query_text: str, results: list[RankedResult], has_more: bool) -> str:
        if not results:
            return (
                "No encontramos departamentos que coincidan con esos criterios. "
                "¿Quieres ajustar el rango de precio o la zona?"
            )

        listing = "\n".join(
            f"- {r.apartment.zona}, {r.apartment.habitaciones} hab, {r.apartment.banos} baños, "
            f"{r.apartment.area_m2} m2, ${r.apartment.precio}, "
            f"amenities: {', '.join(r.apartment.amenities) or 'ninguna'}, "
            f"publicado: {r.apartment.fecha_publicacion.date()}, "
            f"descripción original: {r.apartment.descripcion}"
            for r in results
        )
        prompt = f"Pregunta del usuario: {query_text}\n\nDepartamentos encontrados:\n{listing}"
        if has_more:
            prompt += "\n\nHay más resultados disponibles; termina invitando al usuario a pedir la siguiente página."

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(str(exc)) from exc

        return "".join(block.text for block in response.content if block.type == "text")
