from __future__ import annotations

import unicodedata


def strip_accents(text: str) -> str:
    """Quita tildes/diacríticos. Útil porque el LLM normaliza ortografía
    ("jirón", "Jesús") mientras que el texto scrapeado suele no llevarla
    ("jiron", "Jesus"), y las comparaciones deben ser tolerantes a eso."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
