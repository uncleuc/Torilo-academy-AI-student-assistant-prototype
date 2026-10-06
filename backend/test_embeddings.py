from rag.embeddings import EmbeddingModel

embedding_model = EmbeddingModel() # runs __init__, loads the model once

texts = [
    "Students may request a refund according to the academy's refund policy.",
    "Torilo Academy offers courses in artificial intelligence and machine learning."
]

embeddings = embedding_model.encode(texts)

print("Number of embeddings generated:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))
print("First 10 embedding values:")
print(embeddings[0][:10]) 