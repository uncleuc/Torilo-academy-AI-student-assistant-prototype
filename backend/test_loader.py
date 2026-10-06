from rag.document_loader import load_documents

documents = load_documents("knowledge_base")

print(f"Loaded {len(documents)} documents from the knowledge base.")

for doc in documents:
    print(f"Source: {doc['source']}")
    print(f"Content: {doc['content'][:100]}...")  # Print the first 100 characters of the content for brevity
    print("-" * 40)  # Separator for readability
