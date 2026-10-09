from backend.rag.vector_store import VectorStore


class MetadataFilter:
    def __init__(self, vector_store=None):
        self.vector_store = (
            vector_store
            if vector_store
            else VectorStore()
        )

    def get_by_document_type(self, document_type):
        results = self.vector_store.collection.get(
            where={
                "document_type": document_type
            }
        )

        return results