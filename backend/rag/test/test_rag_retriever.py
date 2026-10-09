from backend.rag.rag_retriever import RAGRetriever


def main():
    rag = RAGRetriever()

    queries = [
        "What courses does Torilo Academy offer?",
        "Can I get a refund after withdrawing?",
        "What happens if I don't pay my fees?",
        "How do I contact Student Support?",
        "Tell me about Torilo Academy.",
    ]

    for query in queries:
        print("\n" + "=" * 70)
        print("QUERY:", query)
        print("=" * 70)

        response = rag.search(
            query=query,
            top_k=5,
        )

        print("Intent:", response["intent"])
        print("Retrieval method:", response["retrieval_method"])

        print("\nResults:")

        seen = set()

        for result in response["results"]:
            document_id = result["document_id"]

            if document_id in seen:
                continue

            seen.add(document_id)

            print(
                f"{document_id} | "
                f"similarity={result['similarity']:.4f} | "
                f"retrieval_score="
                f"{result.get('retrieval_score', result['similarity']):.4f}"
            )


if __name__ == "__main__":
    main()