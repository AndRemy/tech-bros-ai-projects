class BotError(Exception):
    """Base para errores de dominio del bot."""


class NLUExtractionError(BotError):
    """El LLM no pudo interpretar el mensaje del usuario (timeout, respuesta
    inválida, etc.)."""


class InvalidFiltersError(BotError):
    """Los filtros extraídos por el NLU no pasan la validación del schema."""


class DatabaseUnavailableError(BotError):
    """No se pudo consultar la base de datos de departamentos."""


class LLMProviderError(BotError):
    """El proveedor de LLM falló o devolvió un error (rate limit, timeout, etc.)."""
