# This file will become the orchestrator for the ingestion process.
# It won't contain the individual logic for loading,
# cleaning, chunking, metadata, or embeddings.
# Instead, it will call the components you've already built.


from pathlib import Path

from rag.document_loader import load_documents
from rag.cleaner import clean_text
from rag.chunker import chunk_text
from rag.embeddings import EmbeddingModel
from rag.metadata import extract_metadata
from rag.document_schema import (
    DocumentMetadata,
    Document,
    DocumentChunk,
)


def ingest_documents(knowledge_base_path):
    """
    Load, clean, validate and chunk all knowledge base documents
    """

    raw_documents = load_documents(knowledge_base_path)

    documents = []

    for raw_document in raw_documents:
        source = raw_document["source"]

        # Clean the document content
        cleaned_content = clean_text(raw_document["content"])

        # Extract metadata from the document
        metadata_dict = extract_metadata(cleaned_content, source)

        metadata = DocumentMetadata(
            document_id=metadata_dict.get("document_id", ""),
            document_type=metadata_dict.get("document_type", ""),
            source_type=metadata_dict.get("source_type", ""),
            organization=metadata_dict.get("organization", ""),
            original_source=metadata_dict.get("original_source"),
            last_verified=metadata_dict.get("last_verified"),
            status=metadata_dict.get("status", "Active"),
        )

        document = Document(
            content=cleaned_content,
            source=source,
            metadata=metadata,
        )

        documents.append(document)

    # Chunk the documents

    chunks = []

    for document in documents:
        text_chunks = chunk_text(document.content)

        for index, content in enumerate(text_chunks):
            chunk = DocumentChunk(
                content=content,
                source=document.source,
                metadata=document.metadata,
                chunk_index=index,
            )
            chunks.append(chunk)

    return chunks

def generate_chunk_embeddings(chunks):
    """
    Generate embeddings for each document chunk.
    """

    embedding_model = EmbeddingModel()

    texts = [chunk.content for chunk in chunks]

    embeddings = embedding_model.encode(texts)

    return embeddings