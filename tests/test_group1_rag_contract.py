from __future__ import annotations

import json

from backend.rag.document_loader import load_documents
from backend.rag.embeddings import EmbeddingModel
from backend.rag.ingestion import ingest_documents


class FakeEmbeddingClient:
	def __init__(self):
		self.documents = []
		self.queries = []

	def embed_documents(self, texts):
		self.documents.extend(texts)
		return [[0.1, 0.2, 0.3] for _ in texts]

	def embed_query(self, text):
		self.queries.append(text)
		return [0.1, 0.2, 0.3]


class FakeCollection:
	def __init__(self, store):
		self.store = store

	def query(self, **kwargs):
		chunk = self.store.chunks[0]
		return {
			"documents": [[chunk.content]],
			"metadatas": [
				[
					{
						"document_id": chunk.metadata.document_id,
						"document_type": chunk.metadata.document_type,
						"source": chunk.source,
						"source_type": chunk.metadata.source_type,
						"title": chunk.metadata.title,
						"category": chunk.metadata.category,
						"approved": chunk.metadata.approved,
						"chunk_index": chunk.chunk_index,
					}
				]
			],
			"distances": [[0.1]],
		}

	def get(self, **kwargs):
		return {"ids": [], "documents": [], "metadatas": []}


class FakeVectorStore:
	def __init__(self):
		self.chunks = []
		self.collection = FakeCollection(self)

	def add_chunks(self, chunks, embeddings):
		self.chunks.extend(chunks)
		return len(chunks)


def test_embedding_adapter_uses_configured_model(monkeypatch):
	monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
	client = FakeEmbeddingClient()
	model = EmbeddingModel(embeddings=client)

	assert model.model_name == "text-embedding-3-small"
	assert model.encode(["test text"]) == [[0.1, 0.2, 0.3]]
	assert client.documents == ["test text"]


def test_registry_approves_all_current_documents():
	from pathlib import Path

	project_root = Path(__file__).resolve().parents[1]
	entries = json.loads((project_root / "knowledge_base" / "index.json").read_text(encoding="utf-8"))
	loaded = load_documents(project_root / "knowledge_base")

	assert len(entries) == 30
	assert all(entry["approved"] is True for entry in entries)
	assert len(loaded) == len(entries)


def test_ingestion_returns_canonical_approved_context(tmp_path):
	knowledge_base = tmp_path / "knowledge_base"
	knowledge_base.mkdir()
	(knowledge_base / "attendance.md").write_text(
		"# Attendance Policy\n\n"
		"## Document Information\n"
		"- Document ID: attendance_test\n"
		"- Document Type: Attendance and Participation Policy\n"
		"- Source Type: Test Policy\n"
		"- Organization: Torilo Academy\n\n"
		"Students should attend the scheduled learning activities.",
		encoding="utf-8",
	)
	(knowledge_base / "index.json").write_text(
		json.dumps(
			[
				{
					"document": "attendance.md",
					"title": "Attendance Policy",
					"category": "policies",
					"source_type": "policy",
					"approved": True,
				}
			]
		),
		encoding="utf-8",
	)
	model = EmbeddingModel(embeddings=FakeEmbeddingClient())
	store = FakeVectorStore()

	pipeline = ingest_documents(
		knowledge_base,
		embedding_model=model,
		vector_store=store,
	)
	result = pipeline.retrieve_documents("a general retrieval question")

	assert len(store.chunks) == 1
	assert store.chunks[0].metadata.approved is True
	assert len(model.model.documents) == 1
	assert model.model.queries == ["a general retrieval question"]
	assert result["context"][0]["content"].startswith("# Attendance Policy")
	assert result["context"][0]["metadata"]["approved"] is True
	assert result["sources"][0]["document"] == "attendance.md"