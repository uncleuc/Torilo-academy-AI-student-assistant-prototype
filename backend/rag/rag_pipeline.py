from backend.rag.context_builder import build_context
from backend.rag.rag_retriever import RAGRetriever
from backend.rag.source_builder import build_sources


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

    def retrieve_documents(self, query):
        """Return the canonical Group 2 evidence and citation contract."""
        response = self.search(query=query)
        context = []
        sources = []
        seen_sources = set()

        for result in response["results"]:
            if result.get("approved") is not True:
                continue
            metadata = {
                "document": result.get("source"),
                "title": result.get("title") or result.get("document_type"),
                "section": result.get("section"),
                "page": result.get("page"),
                "source_type": result.get("source_type"),
                "category": result.get("category"),
                "approved": True,
            }
            context.append(
                {
                    "content": result.get("content", ""),
                    "metadata": metadata,
                    "score": result.get("retrieval_score", result.get("similarity")),
                }
            )
            source_key = (metadata["document"], metadata["title"])
            if source_key not in seen_sources:
                sources.append(metadata)
                seen_sources.add(source_key)

        return {"context": context, "sources": sources}