"""Entrypoint: send a prompt to the agent and stream its messages."""
import asyncio
import sys

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query
from dotenv import load_dotenv

from notes_agent.config import build_options


async def run(prompt: str) -> str:
    final = ""
    async for message in query(prompt=prompt, options=build_options()):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            final = message.result or ""
    return final


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run(" ".join(sys.argv[1:]) or "Summarize CLAUDE.md"))
