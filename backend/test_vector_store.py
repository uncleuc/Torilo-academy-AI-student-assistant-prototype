from pathlib import Path

from rag.ingestion import (
    ingest_documents,
    generate_chunk_embeddings,
)

from rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"


print("Starting ingestion...")

chunks = ingest_documents(KNOWLEDGE_BASE)

print(f"Chunks created: {len(chunks)}")


print("\nGenerating embeddings...")

embeddings = generate_chunk_embeddings(chunks)

print(f"Embeddings generated: {len(embeddings)}")


print("\nCreating vector store...")

vector_store = VectorStore()

stored_count = vector_store.add_chunks(
    chunks,
    embeddings
)

print(f"Chunks stored: {stored_count}")

print(f"ChromaDB collection count: {vector_store.count()}")

print("\nVector store test complete.")