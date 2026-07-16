from __future__ import annotations

import asyncio
import logging
import os

import anthropic
from dotenv import load_dotenv

from .adapters.factory import create_channel_adapters
from .core.nlu import AnthropicIntentExtractor
from .core.orchestrator import Orchestrator
from .core.responder import AnthropicResponseGenerator
from .core.session import InMemorySessionStore
from .repository.factory import create_apartments_repository

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    load_dotenv()

    llm_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    repository = create_apartments_repository(os.environ["DATABASE_URL"])
    session_store = InMemorySessionStore(ttl_seconds=int(os.environ.get("SESSION_TTL_SECONDS", 1800)))

    orchestrator = Orchestrator(
        intent_extractor=AnthropicIntentExtractor(llm_client),
        repository=repository,
        responder=AnthropicResponseGenerator(llm_client),
        session_store=session_store,
    )

    enabled_channels = [c.strip() for c in os.environ.get("ENABLED_CHANNELS", "").split(",") if c.strip()]
    if not enabled_channels:
        raise RuntimeError("Configura ENABLED_CHANNELS en .env (ej. 'telegram,discord')")
    adapters = create_channel_adapters(enabled_channels)

    await asyncio.gather(*(adapter.start(orchestrator.handle_message) for adapter in adapters))


if __name__ == "__main__":
    asyncio.run(main())
