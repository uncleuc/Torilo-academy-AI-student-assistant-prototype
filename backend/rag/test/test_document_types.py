from backend.rag.vector_store import VectorStore


def main():
    vector_store = VectorStore()

    results = vector_store.collection.get()

    document_types = sorted(
        set(
            metadata.get("document_type")
            for metadata in results["metadatas"]
        )
    )

    print("=" * 70)
    print("DOCUMENT TYPES IN VECTOR STORE")
    print("=" * 70)

    for document_type in document_types:
        print(document_type)


if __name__ == "__main__":
    main()