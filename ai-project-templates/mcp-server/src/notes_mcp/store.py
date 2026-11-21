"""Plain data-access logic. No MCP imports, so it's easy to test."""
import json
import os
import uuid
from pathlib import Path


class NoteStore:
    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("NOTES_PATH", "notes.json"))

    def _load(self) -> dict[str, dict]:
        return json.loads(self.path.read_text()) if self.path.exists() else {}

    def save(self, title: str, body: str) -> str:
        notes = self._load()
        note_id = uuid.uuid4().hex[:8]
        notes[note_id] = {"title": title, "body": body}
        self.path.write_text(json.dumps(notes, indent=2))
        return note_id

    def get(self, note_id: str) -> dict | None:
        return self._load().get(note_id)

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [
            {"id": i, **n}
            for i, n in self._load().items()
            if q in n["title"].lower() or q in n["body"].lower()
        ]
