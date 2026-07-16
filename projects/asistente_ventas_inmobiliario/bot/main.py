from __future__ import annotations

import asyncio
import logging
import os

import anthropic
from dotenv import load_dotenv

from .adapters.base import ChannelAdapter
from .adapters.discord_adapter import DiscordAdapter
from .adapters.telegram_adapter import TelegramAdapter
from .core.nlu import AnthropicIntentExtractor
from .core.orchestrator import Orchestrator
from .core.responder import AnthropicResponseGenerator
from .core.session import InMemorySessionStore
from .repository.apartments_repository import PostgresApartmentsRepository

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    load_dotenv()

    llm_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    repository = PostgresApartmentsRepository(os.environ["DATABASE_URL"])
    session_store = InMemorySessionStore(ttl_seconds=int(os.environ.get("SESSION_TTL_SECONDS", 1800)))

    orchestrator = Orchestrator(
        intent_extractor=AnthropicIntentExtractor(llm_client),
        repository=repository,
        responder=AnthropicResponseGenerator(llm_client),
        session_store=session_store,
    )

    adapters: list[ChannelAdapter] = []
    if telegram_token := os.environ.get("TELEGRAM_BOT_TOKEN"):
        adapters.append(TelegramAdapter(telegram_token))
    if discord_token := os.environ.get("DISCORD_BOT_TOKEN"):
        adapters.append(DiscordAdapter(discord_token))

    if not adapters:
        raise RuntimeError("Configura al menos TELEGRAM_BOT_TOKEN o DISCORD_BOT_TOKEN en .env")

    await asyncio.gather(*(adapter.start(orchestrator.handle_message) for adapter in adapters))


if __name__ == "__main__":
    asyncio.run(main())
