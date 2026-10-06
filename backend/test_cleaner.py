from document_loader import load_documents
from cleaner import clean_text

documents = load_documents("knowledge_base")

print(f"loaded {len(documents)} documents")

for document in documents:

    cleaned_content = clean_text(document["content"])

    print(f"Source: {document['source']}")
    print(f"Original Length: {len(document['content'])}")
    print(f"Cleaned Length: {len(cleaned_content)}")
    print("-" * 50)
