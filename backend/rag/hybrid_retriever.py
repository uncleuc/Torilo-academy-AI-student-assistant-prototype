from rag.retriever import Retriever
from rag.metadata_filter import MetadataFilter


class HybridRetriever:
    def __init__(
        self,
        retriever=None,
        metadata_filter=None
    ):
        self.retriever = (
            retriever
            if retriever
            else Retriever()
        )

        self.metadata_filter = (
            metadata_filter
            if metadata_filter
            else MetadataFilter()
        )

    def search(
        self,
        query,
        top_k=5,
        document_type=None,
        metadata_boost=0.20
    ):
        # 1. Semantic/vector search
        candidate_k = max(top_k * 4, 20)

        vector_results = self.retriever.search(
            query=query,
            top_k=candidate_k
        )

        # Store vector results by chunk identity.
        combined_results = {}

        for result in vector_results:
            key = (
                result["document_id"],
                result["chunk_index"]
            )

            result["retrieval_score"] = result["similarity"]

            combined_results[key] = result

        # 2. Metadata search
        if document_type:
            metadata_data = (
                self.metadata_filter
                .vector_store
                .collection
                .get(
                    where={
                        "document_type": document_type
                    }
                )
            )

            for document, metadata in zip(
                metadata_data["documents"],
                metadata_data["metadatas"]
            ):
                key = (
                    metadata.get("document_id"),
                    metadata.get("chunk_index")
                )

                # If this chunk was already found by
                # vector search, boost its existing score.
                if key in combined_results:
                    combined_results[key]["retrieval_score"] = (
                        combined_results[key]["similarity"]
                        + metadata_boost
                    )

                # If vector search did not find it,
                # give it a neutral base score plus
                # the metadata boost.
                else:
                    combined_results[key] = {
                        "content": document,
                        "source": metadata.get("source"),
                        "document_id": metadata.get(
                            "document_id"
                        ),
                        "document_type": metadata.get(
                            "document_type"
                        ),
                        "source_type": metadata.get(
                            "source_type"
                        ),
                        "chunk_index": metadata.get(
                            "chunk_index"
                        ),
                        "similarity": 0.0,
                        "retrieval_score": metadata_boost,
                    }

        # 3. Rank by the final retrieval score.
        ranked_results = sorted(
            combined_results.values(),
            key=lambda result: result["retrieval_score"],
            reverse=True
        )

        return ranked_results[:top_k]