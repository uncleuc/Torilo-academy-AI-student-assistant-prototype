import chromadb

COLLECTION_NAME = "torilo_knowledge_base"

class VectorStore:
    def __init__(self, persist_directory="chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description": "Torilo Academy knowledge base",
            }
        )

    def add_chunks(self, chunks, embeddings):
        """
        Add document chunks and their embeddings to the vector store.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings."
                )

        ids = []
        documents = []
        metadatas = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk_id = (
                f"{chunk.metadata.document_id}"
                f"_chunk_{chunk.chunk_index}"
            )

            ids.append(chunk_id)
            documents.append(chunk.content)

            metadatas.append({
                "document_id": chunk.metadata.document_id,
                "document_type": chunk.metadata.document_type,
                "source": chunk.source,
                "source_type": chunk.metadata.source_type,
                "organization": chunk.metadata.organization,
                "original_source": (
                    chunk.metadata.original_source or ""
                ),
                "last_verified": (
                    chunk.metadata.last_verified or ""
                ),
                "status": chunk.metadata.status,
                "chunk_index": chunk.chunk_index,
            })

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )

        return len(ids)

    def count(self):
        return self.collection.count()