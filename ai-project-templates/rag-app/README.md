# RAG app template

**Retrieval-Augmented Generation**: before answering, find the passages of
*your* documents that are relevant and put them in the prompt. The model then
answers from your data, with citations, instead of from memory.

**Structure is convention**. Almost every RAG codebase splits into the same
pipeline stages, and this template keeps one module per stage:

```
 data/raw ──ingest──▶ data/processed/chunks.json ──retrieve──▶ top-k chunks ──answer──▶ cited answer
```

## Structure

```
rag-app/
├── data/
│   ├── raw/                  ← source docs (md, txt; add PDF parsing as needed)
│   └── processed/            ← generated chunks / index (git-ignored)
├── src/rag_app/
│   ├── ingest.py             ← load → split into chunks → save
│   ├── retrieve.py           ← score chunks against a query, return top-k
│   └── answer.py             ← build prompt with sources, call Claude, cite
└── tests/test_retrieve.py
```

## Quickstart
```bash
cd ai-project-templates/rag-app
uv sync && cp .env.example .env
uv run python -m rag_app.ingest
uv run python -m rag_app.answer "How many vacation days do I get?"
uv run pytest
```

## Extend it (typical upgrade path)
1. **Better chunking**: split by headings and add overlap between chunks.
2. **Embeddings + vector store**: replace `retrieve.score` with embedding
   similarity (Voyage, etc.) stored in Chroma, pgvector, or similar.
3. **Hybrid search + reranking**: combine keyword (BM25) and vector scores.
4. **Contextual retrieval**: prepend a short document-level summary to each chunk before embedding it.
5. Measure every change with [`../evals`](../evals/README.md). RAG quality is impossible to judge by eye.

## Referencing other product types
- **→ MCP server**: expose `retrieve()` as a `search_docs` tool in
  [`../mcp-server`](../mcp-server/README.md). Then Claude Code, Desktop, or your
  agent can search the docs on its own ("agentic RAG").
- **→ skill**: a skill can tell Claude *when* and *how* to search the docs and how to cite them.
- **→ evals**: `answer()` is the target. Grade correctness and whether it cites sources.

## Docs
- https://docs.claude.com/en/docs/build-with-claude/embeddings
- https://www.anthropic.com/news/contextual-retrieval
