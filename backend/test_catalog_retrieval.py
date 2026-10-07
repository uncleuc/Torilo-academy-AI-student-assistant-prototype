from rag.retriever import Retriever


def main():
    retriever = Retriever()

    queries = [
        "What courses are available at Torilo Academy?",
        "List all courses offered by Torilo Academy.",
        "Torilo Academy course catalogue",
        "AI Engineering Generative AI Data Analysis Cybersecurity",
        "What training programmes does Torilo Academy offer?",
    ]

    for query in queries:
        print("\n" + "=" * 70)
        print("QUERY:", query)
        print("=" * 70)

        results = retriever.search(
            query=query,
            top_k=5,
        )

        seen = set()

        for result in results:
            document_id = result["document_id"]

            if document_id in seen:
                continue

            seen.add(document_id)

            print(
                f"{document_id} | "
                f"similarity={result['similarity']:.4f}"
            )


if __name__ == "__main__":
    main()