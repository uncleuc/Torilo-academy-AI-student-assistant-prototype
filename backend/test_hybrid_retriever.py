from rag.hybrid_retriever import HybridRetriever


def main():
    retriever = HybridRetriever()

    query = "What courses does Torilo Academy offer?"

    print("=" * 70)
    print("VECTOR ONLY")
    print("=" * 70)

    vector_results = retriever.retriever.search(
        query=query,
        top_k=5
    )

    for result in vector_results:
        print(
            f"{result['document_id']} | "
            f"similarity={result['similarity']:.4f}"
        )

    print("\n" + "=" * 70)
    print("HYBRID RETRIEVAL")
    print("=" * 70)

    hybrid_results = retriever.search(
        query=query,
        top_k=5,
        document_type="Course Catalogue"
    )

    for result in hybrid_results:
        print(
            f"{result['document_id']} | "
            f"similarity={result['similarity']:.4f} | "
            f"retrieval_score={result['retrieval_score']:.4f}"
        )


if __name__ == "__main__":
    main()