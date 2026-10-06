from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore


class Retriever:
    def __init__(
        self,
        vector_store=None,
        embedding_model=None
    ):
        self.vector_store = (
            vector_store
            if vector_store
            else VectorStore()
        )

        self.embedding_model = (
            embedding_model
            if embedding_model
            else EmbeddingModel()
        )

    def search(
        self,
        query,
        top_k=5,
        min_similarity=0.25
    ):
        """
        Search the knowledge base for chunks
        relevant to the user's query.
        """

        query_embedding = self.embedding_model.encode(
            [query]
        )[0]

        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        retrieved_chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            # ChromaDB is using squared L2 distance.
            # Because our embeddings are normalized:
            #
            # cosine_similarity = 1 - (distance / 2)

            similarity = 1 - (distance / 2)

            if similarity < min_similarity:
                continue

            retrieved_chunks.append({
                "content": document,
                "source": metadata.get("source"),
                "document_id": metadata.get("document_id"),
                "document_type": metadata.get("document_type"),
                "source_type": metadata.get("source_type"),
                "chunk_index": metadata.get("chunk_index"),
                "similarity": similarity,
                "retrieval_score": similarity,
            })

        return retrieved_chunks