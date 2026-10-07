from rag.document_loader import load_documents
from rag.cleaner import clean_text
from rag.chunker import chunk_text


documents = load_documents("knowledge_base")

total_chunks = 0

for document in documents:
    cleaned_content = clean_text(document["content"])
    
    chunks = chunk_text(cleaned_content, chunk_size=1000, overlap=150)
    
    total_chunks += len(chunks)

    print(f"Source: {document['source']}")
    print(f"Chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):
        print(f"Chunk {i}: {len(chunk)} characters")  # Print the length of each chunk for brevity

    print("-" * 50)


print(f"\nTotal documents: {len(documents)}")
print(f"Total chunks: {total_chunks}")

