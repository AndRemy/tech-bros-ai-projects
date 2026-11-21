"""All agent configuration in one place."""
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions

from notes_agent.tools import local_server

PROJECT_DIR = Path(__file__).parents[2]


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=os.getenv("MODEL", "claude-sonnet-5-5"),
        system_prompt="You are a careful file-analysis assistant.",
        cwd=str(PROJECT_DIR),
        setting_sources=["project"],  # loads CLAUDE.md + .claude/skills + .claude/agents
        mcp_servers={
            "local": local_server,
            # External server from ../mcp-server:
            # "notes": {"command": "uv", "args": ["run", "--directory", str(PROJECT_DIR.parent / "mcp-server"), "notes-mcp"]},
        },
        allowed_tools=["Read", "Grep", "Glob", "Skill", "Task", "mcp__local__word_count"],
        permission_mode="default",
        max_turns=15,
    )
