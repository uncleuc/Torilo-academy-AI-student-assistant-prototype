from backend.rag.rag_pipeline import RAGPipeline


pipeline = RAGPipeline()

test_queries = [
    "What happens if I miss classes?",
    "Can I get a refund if I withdraw?",
    "What courses does Torilo Academy offer?",
    "Where is Torilo Academy located?",
    "What are the requirements for admission?",
]


for query in test_queries:
    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)

    response = pipeline.search(query)

    print(f"\nIntent: {response['intent']}")
    print(f"Retrieval method: {response['retrieval_method']}")

    print("\nSOURCES:")
    for source in response["sources"]:
        print(
            f"- {source['document_id']} "
            f"({source['document_type']})"
        )

    print("\nCONTEXT:")
    print(response["context"][:1500])