from __future__ import annotations

from abc import ABC, abstractmethod

from .models import RankedResult

SYSTEM_PROMPT = (
    "Eres un asistente de ventas inmobiliario. Recibes una lista de departamentos "
    "y debes redactar, para cada uno, una descripción de 2 a 3 oraciones en "
    "español, en tono cercano y profesional, resaltando lo que mejor calce con lo "
    "que pidió el usuario. No inventes datos que no estén en la lista."
)

NO_RESULTS_MESSAGE = (
    "No encontramos departamentos que coincidan con esos criterios. "
    "¿Quieres ajustar el rango de precio o la zona?"
)


class ResponseGenerator(ABC):
    """Puerto: resultados ya rankeados -> texto en lenguaje natural para el usuario.
    Las implementaciones concretas (una por proveedor de LLM) viven en bot/llm/."""

    @abstractmethod
    async def generate(self, query_text: str, results: list[RankedResult], has_more: bool) -> str: ...


def build_prompt(query_text: str, results: list[RankedResult], has_more: bool) -> str | None:
    """Arma el prompt de usuario para el LLM. None si no hay resultados: ahí el
    ResponseGenerator debe devolver NO_RESULTS_MESSAGE directo, sin llamar al LLM."""
    if not results:
        return None

    listing = "\n".join(
        f"- {r.apartment.tipo or 'inmueble'} en {r.apartment.operacion or 'operación no especificada'}, "
        f"{r.apartment.zona}, {r.apartment.habitaciones} hab, {r.apartment.banos} baños, "
        f"{r.apartment.area_m2} m2, ${r.apartment.precio}, "
        f"amenities: {', '.join(r.apartment.amenities) or 'ninguna'}, "
        f"publicado: {r.apartment.fecha_publicacion.date()}, "
        f"descripción original: {r.apartment.descripcion}"
        + (f", link: {r.apartment.url}" if r.apartment.url else "")
        for r in results
    )
    prompt = f"Pregunta del usuario: {query_text}\n\nDepartamentos encontrados:\n{listing}"
    if has_more:
        prompt += "\n\nHay más resultados disponibles; termina invitando al usuario a pedir la siguiente página."
    return prompt
