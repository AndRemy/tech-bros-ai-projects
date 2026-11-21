# Evals template

**Evals** are automated tests for AI behavior. LLM output varies from run to
run, so you score it against a dataset instead of checking for an exact
match. With evals you can change a prompt, a model, or a retrieval step and
**know** whether things got better or worse.

**Structure is convention**. The common pattern, used by OpenAI Evals,
promptfoo, Inspect, and Anthropic's own guidance, is
**dataset → target → graders → report**.

## Structure

```
evals/
├── datasets/
│   └── rag_qa.jsonl        ← one case per line: input + expected / rubric
├── graders/
│   ├── code_graders.py     ← deterministic checks: contains, regex, JSON valid…
│   └── llm_judge.py        ← Claude grades against a rubric (for fuzzy criteria)
├── run_evals.py            ← loads dataset, calls the target, runs graders, writes report
└── reports/                ← timestamped results (git-ignored); compare runs over time
```

## Grader types (best first)
1. **Code-based**: exact match, contains, regex, schema checks. Fast, free, reliable.
2. **LLM-as-judge**: a rubric plus a strong model. Use it for tone, helpfulness, or faithfulness to sources.
3. **Human review**: a small sample, used to check that the LLM judge agrees with people.

## Quickstart
```bash
cd ai-project-templates/evals
cp .env.example .env
# Install the target app into the same environment, e.g.: pip install -e ../rag-app
python run_evals.py --target rag_app.answer:answer --dataset datasets/rag_qa.jsonl
```

## Extend it
- Grow the dataset from real failures. Each bug becomes a case.
- Include edge cases and "should refuse / should say I don't know" cases.
- Track the pass rate per grader across runs, and fail CI if it drops.

## Referencing other product types
`--target module:function` can be any function that takes a string and returns a string:
- [`../rag-app`](../rag-app/README.md): `rag_app.answer:answer`
- [`../api-tool-use-app`](../api-tool-use-app/README.md): `tool_app.app:answer`
- [`../agent-sdk-app`](../agent-sdk-app/README.md): wrap `asyncio.run(run(q))` in a small sync function
- [`../skill`](../skill/README.md): `skill/evals/cases.jsonl` tests whether the skill *triggers*; grade with `claude -p` runs.
- [`../mcp-server`](../mcp-server/README.md): test tools directly with pytest, then use evals to check that the model *picks* the right tool.

## Docs
- https://docs.claude.com/en/docs/test-and-evaluate/develop-tests
