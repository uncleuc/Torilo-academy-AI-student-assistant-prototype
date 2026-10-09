from backend.rag.rag_retriever import RAGRetriever
from backend.rag.context_builder import build_context


def main():
    rag = RAGRetriever()

    query = "Can I get a refund after withdrawing?"

    response = rag.search(
        query=query,
        top_k=5,
    )

    context = build_context(
        response["results"],
        max_chunks=3,
    )

    print("=" * 70)
    print("QUERY")
    print("=" * 70)
    print(query)

    print("\n" + "=" * 70)
    print("INTENT")
    print("=" * 70)
    print(response["intent"])

    print("\n" + "=" * 70)
    print("RETRIEVAL METHOD")
    print("=" * 70)
    print(response["retrieval_method"])

    print("\n" + "=" * 70)
    print("CONTEXT")
    print("=" * 70)
    print(context)


if __name__ == "__main__":
    main()