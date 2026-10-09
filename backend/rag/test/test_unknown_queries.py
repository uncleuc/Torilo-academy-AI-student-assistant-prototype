from backend.rag.rag_pipeline import RAGPipeline


UNKNOWN_QUERIES = [
    "Does Torilo Academy offer scholarships for 2027?",
    "What is the salary for Torilo Academy instructors?",
    "Who is the current CEO of Torilo Academy?",
    "What will the AI Engineering course cost in January 2027?",
    "Does Torilo provide accommodation for students?",
    "What is the acceptance rate for Torilo Academy?",
    "Can I get a student loan from Torilo Academy?",
]


def main():
    rag = RAGPipeline()

    print("=" * 70)
    print("UNKNOWN / OUT-OF-KNOWLEDGE QUERY TEST")
    print("=" * 70)

    for index, query in enumerate(UNKNOWN_QUERIES, start=1):

        # Run the final RAG pipeline
        response = rag.search(
            query=query,
            top_k=5,
            max_context_chunks=3
        )

        # Run the underlying retriever separately so we can
        # inspect the retrieval scores.
        retrieval_response = rag.rag_retriever.search(
            query=query,
            top_k=5
        )

        print("\n" + "-" * 70)
        print(f"TEST {index}")
        print("-" * 70)

        print(f"Query: {query}")

        print(
            f"Intent: "
            f"{response.get('intent')}"
        )

        print(
            f"Retrieval method: "
            f"{response.get('retrieval_method')}"
        )

        print("\nSources:")

        for source in response.get("sources", []):
            print(
                f"- {source.get('document_id')} "
                f"({source.get('document_type')})"
            )

        print("\nRetrieval scores:")

        for result in retrieval_response.get("results", []):
            print(
                f"- {result.get('document_id')} "
                f"| similarity="
                f"{result.get('similarity', 0):.4f} "
                f"| retrieval_score="
                f"{result.get('retrieval_score', 0):.4f}"
            )

        print("\nContext preview:")

        context = response.get("context", "")

        if context:
            print(context[:1000])
        else:
            print("[NO CONTEXT]")


if __name__ == "__main__":
    main()