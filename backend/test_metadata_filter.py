from rag.metadata_filter import MetadataFilter


def main():
    metadata_filter = MetadataFilter()

    results = metadata_filter.get_by_document_type(
        "Course Catalogue"
    )

    print("=" * 70)
    print("COURSE CATALOGUE METADATA FILTER")
    print("=" * 70)

    print("Chunks found:", len(results["ids"]))

    for document_id, metadata in zip(
        results["ids"],
        results["metadatas"],
    ):
        print(
            f"{document_id} | "
            f"{metadata['document_type']} | "
            f"chunk={metadata['chunk_index']}"
        )


if __name__ == "__main__":
    main()