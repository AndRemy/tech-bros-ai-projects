# Subagent template

A **subagent** is a specialized assistant that Claude Code can hand a task
to. It has its own system prompt, its own tool permissions, and, most
importantly, **its own context window**. The main conversation only gets the
subagent's final answer back, not all the files it read along the way.

**Structure is defined by the spec**: one Markdown file per agent, with YAML
frontmatter, in `.claude/agents/`.

## Structure

```
subagent/
└── .claude/
    └── agents/
        ├── code-reviewer.md     ← read-only reviewer, restricted tools
        └── data-analyst.md      ← uses an MCP tool + a skill
```

| Location | Scope |
|---|---|
| `<repo>/.claude/agents/` | This project only (commit it for the team) |
| `~/.claude/agents/` | All your projects |
| `<plugin>/agents/` | Anyone who installs the plugin |

### Frontmatter fields
| Field | Purpose |
|---|---|
| `name` | Identifier (lowercase-hyphens) |
| `description` | **When** to use it. Claude reads this to decide whether to delegate. Add "use proactively" to encourage it |
| `tools` | Allowlist (comma-separated). Leave it out to inherit all tools. Least privilege is good practice |
| `model` | `sonnet`, `opus`, `haiku`, or `inherit` |
| `skills` | Skills to preload into this agent |

The Markdown body is the agent's **system prompt**.

## Use it
Copy `.claude/agents/*.md` into your repo, then say *"use the code-reviewer
agent on my last change"*, or let Claude delegate on its own based on the
description.

## Extend it
- One job per agent. Write the description so it's obvious when to use it.
- Start with read-only tools (`Read, Grep, Glob`) and add write tools only if needed.
- Tell the agent exactly what to return. That reply is all the main thread sees.

## Referencing other product types
- **Subagent → MCP tool**: `tools: mcp__<server>__<tool>`, e.g.
  `mcp__notes__save_note` from [`../mcp-server`](../mcp-server/README.md).
- **Subagent → skill**: `skills: meeting-notes` ([`../skill`](../skill/README.md)).
- **Plugin → subagent**: put the `.md` in `plugin/agents/` ([`../plugin`](../plugin/README.md)).
- **Agent SDK → subagent**: put it in `.claude/agents/` and load it with
  `setting_sources=["project"]`, or define it in code with `agents={...}` ([`../agent-sdk-app`](../agent-sdk-app/README.md)).

## Docs
- https://docs.claude.com/en/docs/claude-code/sub-agents
