# AI Project Templates

One starter project per kind of AI product. Each folder is a **template**:
copy it, rename it, and start building. Each folder's `README.md` explains its
structure, how to run it, and how it connects to the other product types.

## The product types and how they stack

```
                 ┌──────────────────────────────────────────────┐
  Distribution   │  plugin/   (bundles skills + agents + hooks  │
                 │             + commands + MCP servers)        │
                 └───────────────┬──────────────────────────────┘
                                 │ contains / references
         ┌───────────────┬───────┴───────┬────────────────┐
 Claude  │ skill/        │ subagent/     │ hooks/commands │  (inside plugin/)
 Code    │ know-how      │ specialist    │ automation     │
 layer   └──────┬────────┴──────┬────────┴────────────────┘
                │ call tools via │
                ▼                ▼
 Tool    ┌───────────────────────────────┐
 layer   │ mcp-server/  (tools, resources│  ← usable by ANY MCP client
         │              and prompts)     │
         └───────────────────────────────┘
                ▲
 Your own app   │ mcp_servers=..., setting_sources=["project"]
         ┌──────┴────────────┐   ┌────────────────────┐   ┌─────────┐
         │ agent-sdk-app/    │   │ api-tool-use-app/  │   │ rag-app/│
         │ (Claude Code's    │   │ (raw Messages API, │   │ (search │
         │  loop, as a lib)  │   │  your own loop)    │   │ + LLM)  │
         └───────────────────┘   └────────────────────┘   └─────────┘
                         ▲  measured by  ▲
                         └──── evals/ ───┘
```

| Folder | What you build | Pick it when… | Structure is… |
|---|---|---|---|
| [`api-tool-use-app/`](api-tool-use-app/README.md) | App calling the Claude API with tools, your own loop | You want full control, or are learning the fundamentals | Convention |
| [`mcp-server/`](mcp-server/README.md) | A server exposing tools/data via the Model Context Protocol | You want one integration reusable by Claude Code, Claude Desktop, the SDK, other clients | Protocol + convention |
| [`skill/`](skill/README.md) | `SKILL.md` + scripts that teach Claude a procedure | You keep repeating the same instructions or workflow | **Spec (required)** |
| [`subagent/`](subagent/README.md) | A specialized Claude Code agent with its own prompt and tools | A task benefits from focus and a separate context | **Spec (required)** |
| [`plugin/`](plugin/README.md) | An installable bundle of skills, agents, commands, hooks, MCP | You want to share a set of these with a team or the public | **Spec (required)** |
| [`agent-sdk-app/`](agent-sdk-app/README.md) | A standalone agent product built on the Claude Agent SDK | You want Claude Code's agent loop in your own program or service | Convention + SDK paths |
| [`rag-app/`](rag-app/README.md) | Retrieval-augmented question answering over your documents | Answers must come from your data | Convention |
| [`evals/`](evals/README.md) | A harness that measures quality of any of the above | Always, once something works and you want to change it safely | Convention |

**"Spec (required)"** means the host program (Claude Code) only finds your files
if they're in those exact places. **"Convention"** means it's widely used good
practice that you can adapt.

## Suggested learning order

1. `api-tool-use-app` — how tool use actually works under the hood.
2. `mcp-server` — move those tools into a reusable server.
3. `skill` and `subagent` — teach Claude Code to use them well.
4. `plugin` — package everything for others.
5. `agent-sdk-app` — ship your own agent product.
6. `rag-app` and `evals` — ground it in data and measure it.

## How types reference each other (cheat sheet)

| From → To | How |
|---|---|
| plugin → MCP server | `.mcp.json` at plugin root, using `${CLAUDE_PLUGIN_ROOT}` |
| plugin → skill / subagent / command / hook | Put them in `skills/`, `agents/`, `commands/`, `hooks/hooks.json` |
| subagent → MCP tool | `tools: mcp__<server>__<tool>` in the frontmatter |
| subagent → skill | `skills:` in frontmatter, or just name the skill in its prompt |
| skill → MCP tool | Mention the tool by name in `SKILL.md`; Claude calls it if it's connected |
| skill → script | `scripts/foo.py` run by Claude via Bash; reference it by relative path |
| Agent SDK app → MCP server | `ClaudeAgentOptions(mcp_servers={...})` |
| Agent SDK app → skills / subagents / CLAUDE.md | `setting_sources=["project"]` loads `.claude/` from `cwd` |
| API app → MCP server | Use an MCP client library, or the API's MCP connector |
| evals → any app | Import the app's entry function and call it per dataset row |

## Other kinds of AI projects to be aware of

- **Hooks and slash commands**: deterministic automation and saved prompts for Claude Code. They're covered inside `plugin/`, but also work standalone in `.claude/settings.json` and `.claude/commands/`.
- **Output styles**: change Claude Code's voice and format (for example a "teaching" mode).
- **Computer-use / browser agents**: agents that operate a GUI from screenshots.
- **Multi-agent orchestration**: an orchestrator that hands work to several subagents. You can build it with the Agent SDK.
- **Managed Agents / hosted agents**: Anthropic runs the agent loop and sandbox for you.
- **Fine-tuning / embeddings models**: rarely needed; try prompting, RAG and evals first.
- **A2A (agent-to-agent) protocols**: emerging standards for agents from different vendors to talk to each other.
