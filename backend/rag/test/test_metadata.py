from backend.rag.document_loader import load_documents
from backend.rag.cleaner import clean_text
from backend.rag.metadata import extract_metadata

documents = load_documents("knowledge_base")

for document in documents:
    cleaned_content  = clean_text(document["content"])

    metadata = extract_metadata(cleaned_content, document["source"])

    print(f"Source: {document['source']}")
    print(metadata)
    print("-" * 60)

