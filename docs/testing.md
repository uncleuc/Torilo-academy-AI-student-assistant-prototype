# Testing

## Automated Suites

Run from the repository root:

```powershell
python -m pytest -q
python -m ruff check backend tests scripts
python -m compileall -q backend scripts
```

On Linux/WSL, `bash scripts/run_tests.sh` runs pytest. Frontend checks:

```powershell
Set-Location frontend
npm test
npm run build
```

The Python suite includes offline graph tests, config validation, Group 1 ingestion/retrieval contracts, Group 3 SQLite/API contracts, and the roadmap scenario catalogs. Frontend tests mock the HTTP boundary and verify conversation IDs, sources, and retry behavior.

## Scenario Catalogs

The JSON files in `tests/` are executable acceptance data consumed by `tests/test_roadmap_scenarios.py`:

| File | Expected validation |
| --- | --- |
| `rag_questions.json` | RAG route and approved document/source exists. |
| `database_questions.json` | Database route, expected tool, normalized search phrase. |
| `conversation_tests.json` | Follow-up route/tool and contextual query. |
| `injection_tests.json` | Safety block before retriever, database or LLM call. |
| `unknown_questions.json` | Fixed unknown response, empty sources, no evidence-service/model calls. |

Generated prose is intentionally not compared to exact text in unit tests. The model may paraphrase; tests assert routing, evidence availability, source identity, API shape, and forbidden service calls.

## Isolated Services

- Group 2 graph tests use a recording fake LLM and fake retriever/tools; no network or credentials are needed.
- Group 3 tests use an isolated in-memory SQLite database. They do not connect to the developer or Railway PostgreSQL database.
- Group 1 tests use injected fake embeddings and a fake Chroma boundary for unit tests. `scripts/ingest_documents.py` uses the actual configured OpenAI embeddings and persistent Chroma index.
- Live API/browser checks require PostgreSQL, `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`, `EMBEDDING_MODEL`, an approved knowledge registry and a built frontend.

## End-to-End Acceptance

With the production-like local services configured, verify:

1. An attendance-policy query returns the attendance citation.
2. An AI Engineering overview returns the course document citation.
3. An admission question returns the admissions document citation.
4. A database question uses the matching read-only tool and returns only current database evidence.
5. A follow-up reuses the conversation ID and retrieves fresh evidence.
6. Unsupported questions return the fixed unknown answer with no citations.
7. Injection attempts make no retriever, tool or model calls.
8. The browser uses the same-origin `/api` path, and `/api/health` is healthy.

Never run synthetic seed data or destructive schema setup against production data.