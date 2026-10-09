from langchain_openai import OpenAIEmbeddings

from backend.config import get_settings


class EmbeddingModel:
    """OpenAI embedding adapter configured by EMBEDDING_MODEL."""

    def __init__(self, model_name=None, *, embeddings=None):
        selected_model = model_name or get_settings().embedding_model
        if embeddings is None and not selected_model:
            raise RuntimeError("EMBEDDING_MODEL is required to initialize embeddings")
        self.model_name = selected_model
        self.model = embeddings or OpenAIEmbeddings(model=selected_model)

    def encode(self, texts):
        """Return embeddings in the list format expected by ChromaDB."""
        if not texts:
            return []
        return self.model.embed_documents(texts)

    def encode_query(self, text):
        """Embed one search query with the provider's query-specific method."""
        return self.model.embed_query(text)
