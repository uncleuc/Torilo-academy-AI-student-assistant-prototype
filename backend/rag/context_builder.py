# Context Builder for RAG System
"""
context builder that:
1. Removes duplicate chunks.
2. Orders results by retrieval score.
3. Limits the number of chunks.
4. Combines their content.
5. Preserves source metadata.
6. Gives Group 2 a clean structured response.
"""

def build_context(results, max_chunks=5):
    """
    Build a clean context string from retrieved RAG results.

    Parameters:
        results: List of retrieved result dictionaries.
        max_chunks: Maximum number of chunks to include.

    Returns:
        A formatted context string.
    """

    if not results:
        return ""

    # Sort by retrieval score when available.
    ranked_results = sorted(
        results,
        key=lambda result: result.get(
            "retrieval_score",
            result.get("similarity", 0)
        ),
        reverse=True
    )

    selected_results = []
    seen_chunks = set()

    for result in ranked_results:
        chunk_key = (
            result.get("document_id"),
            result.get("chunk_index")
        )

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)
        selected_results.append(result)

        if len(selected_results) >= max_chunks:
            break

    context_parts = []

    for index, result in enumerate(
        selected_results,
        start=1
    ):
        context_parts.append(
            f"[Source {index}]\n"
            f"Document: {result.get('document_id')}\n"
            f"Document Type: {result.get('document_type')}\n"
            f"Source: {result.get('source')}\n\n"
            f"{result.get('content', '')}"
        )

    return "\n\n---\n\n".join(context_parts)