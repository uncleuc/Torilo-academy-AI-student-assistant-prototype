from backend.rag.rag_pipeline import RAGPipeline


def print_response(response):
    print("=" * 70)
    print("QUERY")
    print("=" * 70)
    print(response["query"])

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
    print(response["context"])

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in response["sources"]:
        print(source)


def main():
    rag = RAGPipeline()

    queries = [
        "Can I get a refund after withdrawing?",
        "What do I need to do to complete my course and receive my certificate?",
        "What courses does Torilo Academy offer?",
        "Where is Torilo Academy located?",
    ]

    for query in queries:
        response = rag.search(
            query=query,
            top_k=5,
            max_context_chunks=3
        )

        print_response(response)
        print("\n\n")


if __name__ == "__main__":
    main()