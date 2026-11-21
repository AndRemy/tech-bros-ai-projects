from mcp.server.fastmcp import FastMCP

from notes_mcp.store import NoteStore


def register(mcp: FastMCP, store: NoteStore) -> None:
    @mcp.tool()
    def save_note(title: str, body: str) -> str:
        """Save a meeting note. Returns the new note's ID."""
        return store.save(title, body)

    @mcp.tool()
    def search_notes(query: str) -> list[dict]:
        """Search saved notes by keyword in the title or body."""
        return store.search(query)
