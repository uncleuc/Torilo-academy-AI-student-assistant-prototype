from backend.rag.document_loader import load_documents
from backend.rag.cleaner import clean_text
from backend.rag.chunker import chunk_text


def main():
    documents = load_documents("knowledge_base")

    for document in documents:
        if "courses_catalog" not in document["source"]:
            continue

        cleaned_text = clean_text(document["content"])
        chunks = chunk_text(cleaned_text)

        print("=" * 70)
        print("SOURCE:", document["source"])
        print("NUMBER OF CHUNKS:", len(chunks))
        print("=" * 70)

        for index, chunk in enumerate(chunks):
            print(f"\n--- CHUNK {index} ---")
            print(chunk)


if __name__ == "__main__":
    main()