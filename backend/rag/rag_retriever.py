from backend.rag.hybrid_retriever import HybridRetriever
from backend.rag.query_intent import detect_intent


class RAGRetriever:
    def __init__(self, hybrid_retriever=None):
        self.hybrid_retriever = (
            hybrid_retriever
            if hybrid_retriever
            else HybridRetriever()
        )

    def search(self, query, top_k=5):
        intent_result = detect_intent(query)

        # If an intent was detected, use hybrid retrieval.
        if intent_result:
            results = self.hybrid_retriever.search(
                query=query,
                top_k=top_k,
                document_type=intent_result["document_type"],
            )

            retrieval_method = "hybrid"

        # Otherwise, fall back to semantic retrieval.
        else:
            results = (
                self.hybrid_retriever
                .retriever
                .search(
                    query=query,
                    top_k=top_k,
                )
            )

            retrieval_method = "vector"

        return {
            "query": query,
            "intent": intent_result,
            "retrieval_method": retrieval_method,
            "results": results,
        }