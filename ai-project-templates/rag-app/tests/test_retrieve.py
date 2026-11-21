from rag_app.ingest import chunk
from rag_app.retrieve import retrieve


def test_retrieve_finds_relevant_chunk():
    chunks = chunk("Vacation: 20 days.\nExpenses: 30 days.", "h.md")
    assert retrieve("vacation days", chunks, k=1)[0]["text"].startswith("Vacation")
