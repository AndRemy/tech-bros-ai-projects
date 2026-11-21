"""Keyword retrieval. Swap score() for embedding similarity later."""
import json
import re
from pathlib import Path

CHUNKS = Path(__file__).parents[2] / "data" / "processed" / "chunks.json"


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def score(query: str, text: str) -> float:
    q, t = tokens(query), tokens(text)
    return len(q & t) / (len(q) or 1)


def retrieve(query: str, chunks: list[dict] | None = None, k: int = 3) -> list[dict]:
    chunks = chunks if chunks is not None else json.loads(CHUNKS.read_text())
    ranked = sorted(chunks, key=lambda c: score(query, c["text"]), reverse=True)
    return [c for c in ranked[:k] if score(query, c["text"]) > 0]
