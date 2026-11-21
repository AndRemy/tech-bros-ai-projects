"""Answer a question using retrieved chunks as cited context."""
import os
import sys

import anthropic
from dotenv import load_dotenv

from rag_app.retrieve import retrieve

load_dotenv()


def answer(question: str) -> str:
    hits = retrieve(question)
    context = "\n".join(f"[{c['id']}] {c['text']}" for c in hits) or "(no relevant documents)"
    prompt = (
        f"<documents>\n{context}\n</documents>\n\n"
        f"Answer using only the documents. Cite ids like [handbook.md#0]. "
        f"If the answer isn't there, say so.\n\nQuestion: {question}"
    )
    response = anthropic.Anthropic().messages.create(
        model=os.getenv("MODEL", "claude-sonnet-5-5"),
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    print(answer(" ".join(sys.argv[1:]) or "How many vacation days do I get?"))
