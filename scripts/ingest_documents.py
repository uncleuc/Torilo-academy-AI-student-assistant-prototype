"""Index explicitly approved knowledge-base documents into local ChromaDB."""

from pathlib import Path

from backend.rag.ingestion import ingest_documents


def main() -> None:
	repository_root = Path(__file__).resolve().parents[1]
	ingest_documents(repository_root / "knowledge_base")
	print("Approved knowledge-base documents indexed for retrieval.")

if __name__ == "__main__":
	main()