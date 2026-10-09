from backend.rag.rag_retriever import RAGRetriever
from backend.rag.context_builder import build_context
from backend.rag.source_builder import build_sources


def main():
    rag = RAGRetriever()

    query = "What do I need to do to complete my course and receive my certificate?"

    response = rag.search(
        query=query,
        top_k=5
    )

    # Select the same results that will be used for context
    selected_results = response["results"][:3]

    context = build_context(
        selected_results,
        max_chunks=3
    )

    sources = build_sources(
        selected_results
    )

    print("=" * 70)
    print("QUERY")
    print("=" * 70)
    print(query)

    print("\n" + "=" * 70)
    print("CONTEXT")
    print("=" * 70)
    print(context)

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in sources:
        print(source)


if __name__ == "__main__":
    main()