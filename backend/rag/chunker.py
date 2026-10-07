import re


def split_large_text(text, chunk_size=1000, overlap=150):
    """
    Split a large section into overlapping chunks.
    """

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def merge_small_chunks(chunks, min_chunk_size=200):
    """
    Merge very small chunks with a neighboring chunk.

    Small chunks at the beginning are merged into the next chunk.
    Small chunks elsewhere are merged into the previous chunk.
    """

    if not chunks:
        return []

    merged = []
    i = 0

    while i < len(chunks):

        chunk = chunks[i]

        # If the first chunk is too small, merge it with the next chunk.
        if len(chunk) < min_chunk_size and i == 0 and len(chunks) > 1:
            merged.append(chunk + "\n\n" + chunks[i + 1])
            i += 2
            continue

        # If a later chunk is too small, merge it with the previous chunk.
        if len(chunk) < min_chunk_size and merged:
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)

        i += 1

    return merged


def chunk_text(text, chunk_size=1000, overlap=150):
    """
    Split Markdown text into retrieval-friendly chunks.

    Markdown sections are preserved where possible.
    Oversized sections are split with overlap.
    Very small chunks are merged with the previous chunk.
    """

    sections = re.split(
        r"(?=^#{1,6}\s+)",
        text,
        flags=re.MULTILINE
    )

    sections = [
        section.strip()
        for section in sections
        if section.strip()
    ]

    chunks = []
    current_chunk = ""

    for section in sections:

        if len(current_chunk) + len(section) + 2 <= chunk_size:

            if current_chunk:
                current_chunk += "\n\n" + section
            else:
                current_chunk = section

        else:

            if current_chunk:
                chunks.append(current_chunk.strip())

            if len(section) > chunk_size:

                large_chunks = split_large_text(
                    section,
                    chunk_size,
                    overlap
                )

                chunks.extend(large_chunks)

                current_chunk = ""

            else:
                current_chunk = section

    if current_chunk:
        chunks.append(current_chunk.strip())

    return merge_small_chunks(chunks)