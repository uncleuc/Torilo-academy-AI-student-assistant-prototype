import json
from pathlib import Path


def load_documents(knowledge_base_path, index_path=None):
    """Load Markdown documents explicitly approved in the knowledge-base index."""
    knowledge_base = Path(knowledge_base_path).resolve()
    registry_path = Path(index_path) if index_path else knowledge_base / "index.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, list):
        raise TypeError("Knowledge-base index must contain a JSON array")

    documents = []
    for entry in registry:
        if not isinstance(entry, dict):
            raise TypeError("Knowledge-base index entries must be objects")
        if "approved" not in entry or not isinstance(entry["approved"], bool):
            raise ValueError("Every knowledge-base entry must have a boolean 'approved' field")
        if entry["approved"] is not True:
            continue
        for field in ("title", "category", "source_type"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"Approved knowledge-base entries must include '{field}'")
        document = entry.get("document")
        if not isinstance(document, str) or not document.strip():
            raise ValueError("Approved knowledge-base entries must include a document path")

        file_path = (knowledge_base / document).resolve()
        if knowledge_base not in file_path.parents:
            raise ValueError(f"Registry path escapes knowledge base: {document}")
        if file_path.suffix.lower() != ".md":
            raise ValueError(f"Unsupported knowledge-base document type: {file_path.suffix}")
        if not file_path.is_file():
            raise FileNotFoundError(f"Approved knowledge-base document does not exist: {document}")

        documents.append(
            {
                "content": file_path.read_text(encoding="utf-8"),
                "source": file_path.relative_to(knowledge_base).as_posix(),
                "registry": entry,
            }
        )

    return documents