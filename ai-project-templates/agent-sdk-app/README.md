# Agent SDK app template

The **Claude Agent SDK** is the agent loop that powers Claude Code, available
as a library. You get built-in tools (Read, Write, Bash, Grep, web search…),
context management, permissions, subagents, skills, and MCP support, and you
build **your own agent product** on top: a CLI, a backend service, a Slack bot,
a scheduled job.

**Structure is convention**, plus a few paths the SDK reads: `.claude/` and
`CLAUDE.md` in the agent's working directory, when you pass `setting_sources`.

## Structure

```
agent-sdk-app/
├── pyproject.toml
├── .env.example
├── CLAUDE.md                    ← project memory/instructions loaded into the agent
├── .claude/                     ← SDK-read paths (same format as Claude Code)
│   ├── skills/                  ←   skills (copy ../skill/meeting-notes here)
│   └── agents/                  ←   subagents (copy from ../subagent)
├── src/notes_agent/
│   ├── tools.py                 ← custom in-process tools (@tool → SDK MCP server)
│   ├── config.py                ← ClaudeAgentOptions in one place: model, tools, MCP, permissions
│   └── main.py                  ← entrypoint: runs query() and streams messages
└── tests/test_tools.py
```

Good practice: **all agent configuration lives in `config.py`**. Tools stay
pure functions you can test, and `main.py` only handles input and output.

## Quickstart
```bash
cd ai-project-templates/agent-sdk-app
uv sync && cp .env.example .env
uv run python -m notes_agent.main "Count the words in README.md"
uv run pytest
```
(The Python SDK uses the Claude Code CLI as its runtime. Install it if it's missing.)

## Key options (`config.py`)
| Option | Purpose |
|---|---|
| `system_prompt` | Your agent's role |
| `allowed_tools` | Allowlist (built-ins + `mcp__server__tool`) |
| `permission_mode` | `default`, `acceptEdits`, `plan`, `bypassPermissions` |
| `mcp_servers` | In-process SDK servers and/or external stdio/HTTP servers |
| `setting_sources` | `["project"]` loads `CLAUDE.md`, `.claude/skills`, `.claude/agents` |
| `cwd` | The folder the agent works in |

## Referencing other product types
- **→ MCP server**: `mcp_servers={"notes": {"command": "uv", "args": ["run", "--directory", "../mcp-server", "notes-mcp"]}}` ([`../mcp-server`](../mcp-server/README.md)).
- **→ skills / subagents**: drop them in `.claude/skills` and `.claude/agents` ([`../skill`](../skill/README.md), [`../subagent`](../subagent/README.md)), and allow the `Skill` and `Task` tools.
- **→ plugin**: `plugins=[{"type": "local", "path": "../plugin"}]` ([`../plugin`](../plugin/README.md)).
- **→ evals**: wrap `run()` in a function that returns the final text ([`../evals`](../evals/README.md)).

## Docs
- https://docs.claude.com/en/docs/agent-sdk/overview
- https://github.com/anthropics/claude-agent-sdk-python
