# MCP server template

An **MCP server** exposes capabilities to any AI client that speaks the
[Model Context Protocol](https://modelcontextprotocol.io): Claude Code,
Claude Desktop, the Agent SDK, IDEs, and others. You write the integration
once and every client can use it.

**The protocol defines the concepts. The folder layout is convention**: a
standard Python package with one module per MCP concept, which mirrors the
official SDK examples.

## The three MCP primitives
| Primitive | Who decides to use it | Example here |
|---|---|---|
| **Tool** | The model calls it | `save_note`, `search_notes` |
| **Resource** | The app/user attaches it as context (read-only data) | `notes://{note_id}` |
| **Prompt** | The user picks it (it shows up as a slash command in clients) | `summarize_notes` |

## Structure

```
mcp-server/
├── pyproject.toml              ← deps + console script `notes-mcp`
├── .env.example                ← config through env vars, never hard-coded
├── .mcp.json.example           ← how a client registers this server
├── src/notes_mcp/
│   ├── server.py               ← ENTRYPOINT: creates FastMCP, registers modules, runs
│   ├── store.py                ← business logic / data access (no MCP code here)
│   ├── tools/notes.py          ← @mcp.tool functions
│   ├── resources/notes.py      ← @mcp.resource functions
│   └── prompts/summarize.py    ← @mcp.prompt functions
└── tests/test_tools.py         ← tests the logic without a client
```

Key practice: **keep MCP wiring thin and logic in plain modules** (`store.py`).
That way you can test it with pytest and reuse it outside MCP.

## Quickstart

```bash
cd ai-project-templates/mcp-server
uv sync                      # or: pip install -e ".[dev]"
uv run pytest
uv run mcp dev src/notes_mcp/server.py   # opens the MCP Inspector to try tools
```

Register it in Claude Code:
```bash
claude mcp add notes -- uv run --directory "$PWD" notes-mcp
```

## Extend it
- New tool: add a function in `tools/` with a clear docstring. The docstring
  becomes the tool description the model reads, and type hints become its input schema.
- Return small, structured results. Paginate big ones.
- Transports: `stdio` (default, local) or `streamable-http` for a remote
  server: `mcp.run(transport="streamable-http")`.

## Referencing other product types
- **Plugin → this server**: `plugin/.mcp.json` ([`../plugin`](../plugin/README.md)).
- **Subagent → its tools**: `tools: mcp__notes__save_note` ([`../subagent`](../subagent/README.md)).
  The naming pattern is `mcp__<server name>__<tool name>`.
- **Skill → its tools**: name the tool in `SKILL.md` ([`../skill`](../skill/README.md)).
- **Agent SDK → this server**: `mcp_servers={"notes": {"command": "uv", "args": [...]}}` ([`../agent-sdk-app`](../agent-sdk-app/README.md)).

## Docs
- https://modelcontextprotocol.io/docs
- https://github.com/modelcontextprotocol/python-sdk
