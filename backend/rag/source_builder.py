def build_sources(results):
    """
    Build a clean list of unique sources from the
    results that were actually selected for context.

    Multiple chunks can come from the same document,
    but each document should only appear once.
    """

    if not results:
        return []

    sources = []
    seen_documents = set()

    for result in results:
        document_id = result.get("document_id")

        if not document_id:
            continue

        if document_id in seen_documents:
            continue

        seen_documents.add(document_id)

        sources.append({
            "document_id": document_id,
            "document_type": result.get("document_type"),
            "source": result.get("source"),
            "source_type": result.get("source_type"),
        })

    return sources