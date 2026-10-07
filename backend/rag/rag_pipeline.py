from rag.rag_retriever import RAGRetriever
from rag.context_builder import build_context
from rag.source_builder import build_sources


class RAGPipeline:
    """
    Final integration interface for the Torilo Academy RAG system.

    Group 2 provides a student's question and receives:
    - intent
    - retrieval method
    - retrieved results
    - grounded context
    - source information
    """

    def __init__(self, rag_retriever=None):
        self.rag_retriever = (
            rag_retriever
            if rag_retriever
            else RAGRetriever()
        )

    def search(
        self,
        query,
        top_k=5,
        max_context_chunks=3
    ):
        retrieval_response = self.rag_retriever.search(
            query=query,
            top_k=top_k
        )

        results = retrieval_response["results"]
        intent = retrieval_response["intent"]

        # Course catalogue questions may require
        # multiple chunks to provide the complete list.
        context_limit = max_context_chunks

        if intent and intent["intent"] == "course_catalogue":
            context_limit = 5

        selected_results = results[:context_limit]

        context = build_context(
            selected_results,
            max_chunks=context_limit
        )

        sources = build_sources(
            selected_results
        )

        return {
            "query": query,
            "intent": intent,
            "retrieval_method": retrieval_response[
                "retrieval_method"
            ],
            "results": selected_results,
            "context": context,
            "sources": sources,
        }