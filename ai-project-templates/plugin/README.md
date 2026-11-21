# Plugin template

A **Claude Code plugin** is an installable bundle. It's how you ship skills,
subagents, slash commands, hooks, and MCP servers together, so a teammate can
install them all with one command.

**Structure is defined by the spec**: Claude Code finds each component by its
folder name at the plugin root. Only `plugin.json` goes inside `.claude-plugin/`.

## Structure

```
plugin/
├── .claude-plugin/
│   ├── plugin.json          ← REQUIRED. Manifest: name, version, description, author
│   └── marketplace.json     ← optional. Makes this repo a "marketplace" others can add
├── skills/                  ← Agent Skills (same format as ../skill)
│   └── meeting-notes/SKILL.md
├── agents/                  ← subagents (same format as ../subagent)
│   └── notes-analyst.md
├── commands/                ← slash commands: file name = command name
│   └── minutes.md           →  /minutes
├── hooks/
│   ├── hooks.json           ← event → shell command (deterministic automation)
│   └── scripts/log_tool.sh
├── .mcp.json                ← MCP servers that start when the plugin is enabled
└── servers/                 ← optional: bundled MCP server code (or point to a package)
```

### The components at a glance
| Component | Triggered by | Good for |
|---|---|---|
| Skill | Claude, when the description matches the task | Procedures, know-how |
| Subagent | Claude delegating, or you asking for it | Focused tasks with their own context |
| Command | You typing `/name args` | Prompts you reuse often |
| Hook | Events (`PreToolUse`, `PostToolUse`, `Stop`…) | Rules that must always run: lint, block, log |
| MCP server | Claude calling a tool | Access to external systems and data |

## Use it locally

```bash
claude --plugin-dir ./ai-project-templates/plugin
```

Or, via the marketplace file:
```
/plugin marketplace add ./ai-project-templates/plugin
/plugin install notes-toolkit@techbros-templates
```

## Extend it
- Bump `version` in `plugin.json` whenever you change it.
- Use `${CLAUDE_PLUGIN_ROOT}` in `.mcp.json` and `hooks.json`. Plugins are
  copied to a cache folder when installed, so relative paths from your
  current directory will break.
- Keep hooks fast and safe. They run on every matching event.

## Referencing other product types
- **Plugin → MCP server**: `.mcp.json` here starts the server from
  [`../mcp-server`](../mcp-server/README.md). You can also bundle the server
  code under `servers/` and point to it with `${CLAUDE_PLUGIN_ROOT}/servers/...`.
- **Plugin → skill / subagent**: copy them into `skills/` and `agents/`. The
  formats are identical to [`../skill`](../skill/README.md) and [`../subagent`](../subagent/README.md).
- **Command → subagent / skill**: a command body can say "use the
  notes-analyst agent to…", and Claude follows it.
- **Agent SDK → plugin**: `ClaudeAgentOptions(plugins=[{"type": "local", "path": "./plugin"}])`.

## Docs
- https://docs.claude.com/en/docs/claude-code/plugins
- https://docs.claude.com/en/docs/claude-code/plugins-reference
- https://docs.claude.com/en/docs/claude-code/hooks
