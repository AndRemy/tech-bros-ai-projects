"""Manual tool-use loop on the Claude Messages API."""
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from tool_app.tools import HANDLERS, TOOLS

load_dotenv()
MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
SYSTEM = (Path(__file__).parents[2] / "prompts" / "system.md").read_text()
MAX_TURNS = 10


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    try:
        return HANDLERS[name](**args), False
    except Exception as e:  # report errors back to the model
        return f"Error: {e}", True


def answer(question: str) -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output, is_error = run_tool(block.name, block.input)
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": is_error}
                )
        messages.append({"role": "user", "content": results})
    return "Stopped: too many tool calls."


if __name__ == "__main__":
    print(answer(" ".join(sys.argv[1:]) or "What is 12 * 7?"))
