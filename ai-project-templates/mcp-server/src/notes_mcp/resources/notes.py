import json

from mcp.server.fastmcp import FastMCP

from notes_mcp.store import NoteStore


def register(mcp: FastMCP, store: NoteStore) -> None:
    @mcp.resource("notes://{note_id}")
    def get_note(note_id: str) -> str:
        """A single note as JSON."""
        return json.dumps(store.get(note_id) or {})
