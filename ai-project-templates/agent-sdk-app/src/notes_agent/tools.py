"""Custom tools that run inside your process, exposed to the agent as an SDK MCP server."""
from claude_agent_sdk import create_sdk_mcp_server, tool


def count_words(text: str) -> int:  # pure logic, easy to unit-test
    return len(text.split())


@tool("word_count", "Count the words in a piece of text.", {"text": str})
async def word_count(args: dict) -> dict:
    return {"content": [{"type": "text", "text": str(count_words(args["text"]))}]}


local_server = create_sdk_mcp_server(name="local", version="0.1.0", tools=[word_count])
