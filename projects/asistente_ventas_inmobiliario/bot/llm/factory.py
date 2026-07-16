from __future__ import annotations

from typing import Callable

from ..core.nlu import IntentExtractor
from ..core.responder import ResponseGenerator
from . import anthropic_provider, gemini_provider, openai_provider

# Un proveedor nuevo se agrega acá y en su propio archivo (anthropic_provider.py,
# openai_provider.py, gemini_provider.py, ...); nada más del bot necesita cambiar.
_PROVIDERS: dict[str, tuple[Callable[[], IntentExtractor], Callable[[], ResponseGenerator]]] = {
    "anthropic": (anthropic_provider.create_intent_extractor_from_env, anthropic_provider.create_response_generator_from_env),
    "openai": (openai_provider.create_intent_extractor_from_env, openai_provider.create_response_generator_from_env),
    "gemini": (gemini_provider.create_intent_extractor_from_env, gemini_provider.create_response_generator_from_env),
}


def create_llm_provider(provider_name: str) -> tuple[IntentExtractor, ResponseGenerator]:
    """LLM_PROVIDER (.env) -> (IntentExtractor, ResponseGenerator) del proveedor
    elegido, para que el resto del bot solo dependa de esas dos interfaces."""
    factories = _PROVIDERS.get(provider_name)
    if factories is None:
        disponibles = ", ".join(sorted(_PROVIDERS))
        raise ValueError(f"Proveedor de LLM desconocido: '{provider_name}'. Disponibles: {disponibles}")
    create_extractor, create_responder = factories
    return create_extractor(), create_responder()
