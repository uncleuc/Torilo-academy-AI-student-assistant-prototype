import hashlib
import json
import re
from pathlib import Path

from backend.config import Settings, get_settings
from backend.rag.chunker import chunk_text
from backend.rag.cleaner import clean_text
from backend.rag.document_loader import load_documents
from backend.rag.document_schema import Document, DocumentChunk, DocumentMetadata
from backend.rag.embeddings import EmbeddingModel
from backend.rag.hybrid_retriever import HybridRetriever
from backend.rag.metadata_filter import MetadataFilter
from backend.rag.rag_pipeline import RAGPipeline
from backend.rag.rag_retriever import RAGRetriever
from backend.rag.retriever import Retriever
from backend.rag.vector_store import VectorStore


def ingest_documents(
    knowledge_base_path,
    *,
    embedding_model=None,
    vector_store=None,
    settings: Settings | None = None,
):
    """Build a persistent, approved-document retriever for Group 2/API use."""
    active_settings = settings or get_settings()
    model = embedding_model or EmbeddingModel()
    model_name = getattr(model, "model_name", None) or active_settings.embedding_model or "default"
    collection_suffix = re.sub(r"[^a-zA-Z0-9_-]", "_", model_name.lower())[:40]
    store = vector_store or VectorStore(
        persist_directory=str(active_settings.chroma_persist_directory),
        collection_name=f"{active_settings.chroma_collection_name}_{collection_suffix}",
    )

    raw_documents = load_documents(knowledge_base_path)
    fingerprint_builder = hashlib.sha256(model_name.encode("utf-8"))
    for raw_document in raw_documents:
        fingerprint_builder.update(raw_document["source"].encode("utf-8"))
        fingerprint_builder.update(raw_document["content"].encode("utf-8"))
        fingerprint_builder.update(
            json.dumps(raw_document["registry"], sort_keys=True).encode("utf-8")
        )
    fingerprint = fingerprint_builder.hexdigest()

    chunks = []
    for raw_document in raw_documents:
        registry = raw_document["registry"]
        content = clean_text(raw_document["content"])
        metadata_values = {
            "document_id": "",
            "document_type": "",
            "source_type": registry["source_type"],
            "organization": "Torilo Academy",
            "approved": registry["approved"],
            "title": registry["title"],
            "category": registry["category"],
        }
        for line in content.splitlines():
            match = re.match(r"^-\s*Document ID:\s*(.+)$", line, re.IGNORECASE)
            if match:
                metadata_values["document_id"] = match.group(1).strip()
            match = re.match(r"^-\s*Document Type:\s*(.+)$", line, re.IGNORECASE)
            if match:
                metadata_values["document_type"] = match.group(1).strip()
        if not metadata_values["document_type"]:
            metadata_values["document_type"] = registry["title"]
        if not metadata_values["document_id"]:
            metadata_values["document_id"] = Path(raw_document["source"]).stem

        document = Document(
            content=content,
            source=raw_document["source"],
            metadata=DocumentMetadata(**metadata_values),
        )
        for index, chunk_content in enumerate(chunk_text(document.content)):
            chunks.append(
                DocumentChunk(
                    content=chunk_content,
                    source=document.source,
                    metadata=document.metadata,
                    chunk_index=index,
                )
            )

    index_is_current = (
        hasattr(store, "has_ingestion_fingerprint")
        and store.has_ingestion_fingerprint(fingerprint)
        and store.count() == len(chunks)
    )
    if chunks and not index_is_current:
        embeddings = model.encode([chunk.content for chunk in chunks])
        store.add_chunks(chunks, embeddings)
    if hasattr(store, "set_ingestion_fingerprint"):
        store.set_ingestion_fingerprint(fingerprint)

    retriever = Retriever(vector_store=store, embedding_model=model)
    hybrid = HybridRetriever(retriever=retriever, metadata_filter=MetadataFilter(store))
    return RAGPipeline(RAGRetriever(hybrid))