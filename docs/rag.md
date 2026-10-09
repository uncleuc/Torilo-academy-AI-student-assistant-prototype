# Retrieval-Augmented Generation

## Approval Registry

`knowledge_base/index.json` is the document allowlist. Every included entry must contain a path, title, category, source type and explicit boolean `approved`. Only entries with `approved: true` are loaded. The loader rejects missing approval metadata, paths outside the knowledge-base directory, missing files and unsupported formats.

Do not approve generated or unverified academy claims without the knowledge-base owner reviewing them. The current registry contains the 30 project Markdown files; approval is a content-governance decision, not a technical claim that every statement is official.

## Ingestion and Storage

`scripts/ingest_documents.py` calls `backend.rag.ingestion.ingest_documents()`. The pipeline:

1. Reads approved Markdown documents and preserves registry/source metadata.
2. Cleans text and creates Markdown-aware overlapping chunks.
3. Embeds chunks with the configured OpenAI `EMBEDDING_MODEL` (currently `text-embedding-3-small`).
4. Upserts chunks and metadata into a persistent Chroma collection.
5. Returns a `RAGPipeline` exposing the canonical `retrieve_documents(query)` contract.

Chroma persists under `CHROMA_PERSIST_DIRECTORY` (default `<repository>/chroma_db`). The collection name includes the configured base collection name and sanitized embedding model. A content/model fingerprint avoids re-embedding an unchanged index. In hosted deployments, mount persistent storage at the configured path or the index will need rebuilding after restart/redeploy.

## Group 2 Retrieval Contract

```python
{
	"context": [
		{"content": "...", "metadata": {"document": "...", "approved": True}, "score": 0.8}
	],
	"sources": [
		{"document": "...", "title": "...", "source_type": "...", "approved": True}
	]
}
```

Context carries chunk text for the model. Sources carry citation metadata. Only explicitly approved records reach the graph. Group 2 makes the answer sufficiency decision; retrieval similarity by itself is not proof of support.

## Retrieval Strategy

`RAGRetriever` detects keyword intents (attendance, admissions, fees, course catalogue, etc.). `HybridRetriever` combines vector results with metadata-filtered candidates and ranks them. When no intent matches, it falls back to vector retrieval. The final pipeline returns a bounded number of chunks and deduplicated source cards.

Intent rules are a baseline and require regression coverage when they change. If no approved evidence is returned, Group 2 returns the fixed unknown response without asking the model to guess.

## Commands

From the repository root:

```powershell
python -m scripts.ingest_documents
python -m pytest tests/test_group1_rag_contract.py tests/test_question_routing.py -q
```

The deterministic fake-backed RAG tests do not call OpenAI. Ingestion/querying against the configured embedding provider does require valid credentials and may incur provider usage charges.