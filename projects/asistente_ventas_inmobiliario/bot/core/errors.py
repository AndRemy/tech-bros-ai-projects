from __future__ import annotations

from .exceptions import (
    BotError,
    DatabaseUnavailableError,
    InvalidFiltersError,
    LLMProviderError,
    NLUExtractionError,
)

_FRIENDLY_MESSAGES: dict[type[BotError], str] = {
    NLUExtractionError: "No logré entender tu pregunta, ¿puedes reformularla?",
    InvalidFiltersError: (
        "No logré entender bien lo que buscas. ¿Puedes darme más detalle "
        "(zona, precio, número de habitaciones)?"
    ),
    DatabaseUnavailableError: (
        "Estamos teniendo problemas para consultar la disponibilidad en este "
        "momento. Intenta de nuevo en unos minutos."
    ),
    LLMProviderError: "Estoy recibiendo muchas solicitudes en este momento, intenta de nuevo en un momento.",
}

_DEFAULT_MESSAGE = "Algo salió mal de mi lado. Intenta de nuevo en un momento."


def to_user_friendly_message(error: Exception) -> str:
    """Traduce una excepción a un mensaje seguro para el usuario. El error real
    se loguea aparte (con stack trace / correlation id) y nunca se reenvía tal cual."""
    return _FRIENDLY_MESSAGES.get(type(error), _DEFAULT_MESSAGE)
