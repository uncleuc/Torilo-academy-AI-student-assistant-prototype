from rag.query_intent import detect_intent


def main():
    test_queries = [
        "What courses does Torilo Academy offer?",
        "Can I get a refund after withdrawing?",
        "What happens if I don't pay my fees?",
        "What happens if I miss classes?",
        "What do I need to complete my course?",
        "How do I contact Student Support?",
        "What are the admission requirements?",
        "Tell me about Torilo Academy.",
    ]

    for query in test_queries:
        result = detect_intent(query)

        print("\nQuery:", query)
        print("Intent:", result)


if __name__ == "__main__":
    main()