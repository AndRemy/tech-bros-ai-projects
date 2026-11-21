from notes_mcp.store import NoteStore


def test_save_and_search(tmp_path):
    store = NoteStore(str(tmp_path / "notes.json"))
    note_id = store.save("Standup", "Decided to ship Friday")
    assert store.get(note_id)["title"] == "Standup"
    assert store.search("ship")[0]["id"] == note_id
