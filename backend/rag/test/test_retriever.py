from backend.rag.retriever import Retriever


retriever = Retriever()


queries = [
    "Can I get a refund if I withdraw from my course?",
    "What courses does Torilo Academy offer?",
    "How can I contact student support?",
    "What are the requirements for completing my course?",
]


for query in queries:
    print("\n")
    print("=" * 70)
    print("QUERY:", query)
    print("=" * 70)

    results = retriever.search(
        query,
        top_k=3
    )

    if not results:
        print("No relevant results found.")
        continue

    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("-" * 50)

        print("Similarity:", round(
            result["similarity"],
            4
        ))

        print("Document ID:", result["document_id"])

        print("Document Type:", result["document_type"])

        print("Source:", result["source"])

        print("Chunk Index:", result["chunk_index"])

        print("\nContent:")
        print(result["content"][:500])