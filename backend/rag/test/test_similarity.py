from backend.rag.embeddings import EmbeddingModel
from sklearn.metrics.pairwise import cosine_similarity


embedding_model = EmbeddingModel()

texts = [
    "Students may request a refund according to the academy's refund policy.",
    "Torilo Academy offers courses in artificial intelligence and machine learning.",
    "Approved refunds are processed according to the applicable refund procedure."
]

query = "Can I get my money back if I withdraw from my course?"

text_embeddings = embedding_model.encode(texts)
query_embedding = embedding_model.encode([query])

similarities = cosine_similarity(
    query_embedding,
    text_embeddings
)[0]

for text, score in zip(texts, similarities):
    print(f"{score:.4f} -> {text}")