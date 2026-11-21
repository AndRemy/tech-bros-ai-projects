# Skill template

A **Skill** is a folder of instructions, scripts, and resources that Claude
loads only when they're relevant. It's how you package know-how, like "how we
write meeting notes" or "how to build our quarterly report", so you don't
repeat it in every prompt.

**Structure is defined by the spec**: Claude looks for `SKILL.md` with YAML
frontmatter. Everything else is a recommended convention.

## Structure

```
skill/
├── meeting-notes/            ← the skill itself (folder name = skill name)
│   ├── SKILL.md              ← REQUIRED. Frontmatter + instructions
│   ├── scripts/              ← code Claude runs instead of writing it each time
│   │   └── extract_actions.py
│   ├── reference/            ← long docs loaded only if SKILL.md points to them
│   │   └── style-guide.md
│   └── assets/               ← templates and files used in the output
│       └── template.md
└── evals/
    └── cases.jsonl           ← prompts that SHOULD / SHOULD NOT trigger the skill
```

### How loading works (progressive disclosure)
1. **Always loaded**: only `name` + `description` from the frontmatter (a few tokens).
2. **When the description matches the task**: the body of `SKILL.md`.
3. **Only when needed**: files in `reference/`, `scripts/`, `assets/` that the body mentions.

So: **the `description` is the most important line you'll write.** Say what
the skill does *and when to use it*.

## Use it

Install it for Claude Code by copying or symlinking the skill folder:

```bash
mkdir -p ~/.claude/skills && cp -r meeting-notes ~/.claude/skills/
```

Or per project: `<repo>/.claude/skills/meeting-notes/`. Then ask Claude Code
to "turn these notes into meeting minutes", and it picks up the skill.

## Extend it
- Keep `SKILL.md` short (under ~500 lines). Move detail into `reference/`.
- Use a script for anything deterministic (parsing, formatting, validating).
- Add cases to `evals/cases.jsonl` whenever the skill triggers wrongly.

## Referencing other product types
- **Skill → MCP tool**: write the tool name in the instructions, e.g. *"Save
  the result with the `mcp__notes__save_note` tool."* It works when that MCP
  server is connected (see [`../mcp-server`](../mcp-server/README.md)).
- **Skill → script**: `python scripts/extract_actions.py <file>`, using a path relative to the skill folder.
- **Plugin → skill**: put the folder in `plugin/skills/` ([`../plugin`](../plugin/README.md)).
- **Subagent → skill**: list it under `skills:` in the agent's frontmatter ([`../subagent`](../subagent/README.md)).
- **Agent SDK → skill**: put it in `.claude/skills/` and use `setting_sources=["project"]` ([`../agent-sdk-app`](../agent-sdk-app/README.md)).

## Docs
- https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- https://github.com/anthropics/skills (official examples)
