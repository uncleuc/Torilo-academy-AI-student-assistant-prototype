from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-V2" # You can change this to any other model from the Sentence Transformers library


class EmbeddingModel:
    def __init__(self, model_name=MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts, normalize_embeddings=True)

