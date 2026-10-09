from pathlib import Path

from backend.rag.ingestion import (
    ingest_documents,
    generate_chunk_embeddings,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"


print("Starting document ingestion...")

chunks = ingest_documents(KNOWLEDGE_BASE)

print("\nDocuments successfully converted into chunks.")
print(f"Total chunks: {len(chunks)}")


print("\nFirst chunk:")
print("----------------------------------------")
print("Source:", chunks[0].source)
print("Chunk index:", chunks[0].chunk_index)
print("Document ID:", chunks[0].metadata.document_id)
print("Document type:", chunks[0].metadata.document_type)
print("Content:")
print(chunks[0].content[:500])
print("----------------------------------------")


print("\nGenerating embeddings...")

embeddings = generate_chunk_embeddings(chunks)

print(f"Number of embeddings: {len(embeddings)}")
print(f"Embedding dimension: {len(embeddings[0])}")


print("\nPipeline test complete.")