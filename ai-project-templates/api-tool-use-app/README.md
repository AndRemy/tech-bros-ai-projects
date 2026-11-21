# API tool-use app template

The **foundation** under every other template: your code calls the Claude
Messages API, gives it **tool definitions** (JSON Schema), runs whatever tool
the model asks for, sends the result back, and repeats until the model gives
a final answer. MCP servers, skills, and the Agent SDK all automate parts of
this loop.

**Structure is convention**: a normal Python app that keeps three things apart:
prompts, tools, and the loop.

## Structure

```
api-tool-use-app/
├── pyproject.toml
├── .env.example            ← ANTHROPIC_API_KEY, MODEL
├── prompts/
│   └── system.md           ← system prompt kept as a file, so it's easy to review and change
├── src/tool_app/
│   ├── tools.py            ← tool SCHEMAS + their Python implementations, in one registry
│   └── app.py              ← the agent loop + CLI entrypoint
└── tests/test_tools.py     ← tests the tools without calling the API
```

## The loop (what `app.py` does)
1. Send `messages` + `tools` to the API.
2. If `stop_reason == "tool_use"`, run each `tool_use` block and append a
   `tool_result` with the same `tool_use_id`.
3. Repeat until `stop_reason == "end_turn"`. Cap the number of iterations.

## Quickstart
```bash
cd ai-project-templates/api-tool-use-app
uv sync && cp .env.example .env    # add your key
uv run python -m tool_app.app "What's 17% of 2350, and what time is it in UTC?"
uv run pytest
```

## Extend it
- Add a tool: one entry in `TOOLS` (name, description, input_schema) and a
  function in `HANDLERS`. Write the description for the model: say what it
  does and when to use it.
- Return errors as tool results with `is_error: true` instead of crashing,
  so the model can recover.

## Referencing other product types
- **→ MCP server**: rather than defining tools here, connect to
  [`../mcp-server`](../mcp-server/README.md) with the `mcp` client library
  (list its tools and forward calls), or use the API's MCP connector for remote servers.
- **→ Agent SDK**: once you need files, bash, subagents, or skills, switch to
  [`../agent-sdk-app`](../agent-sdk-app/README.md). It runs this loop for you.
- **→ evals**: `answer(question)` is the function [`../evals`](../evals/README.md) calls.

## Docs
- https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
