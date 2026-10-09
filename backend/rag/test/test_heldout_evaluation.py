from backend.rag.rag_pipeline import RAGPipeline


TEST_CASES = [
    {
        "query": "If I decide to leave the academy shortly after paying, what happens?",
        "expected_document_ids": ["policy_refund"],
    },
    {
        "query": "What could prevent me from getting my certificate?",
        "expected_document_ids": ["policy_certification"],
    },
    {
        "query": "Which technology programmes can I study at Torilo?",
        "expected_document_ids": ["course_courses_catalog"],
    },
    {
        "query": "How do I reach the student support team?",
        "expected_document_ids": ["academy_student_support"],
    },
    {
        "query": "What happens if I miss classes?",
        "expected_document_ids": ["policy_attendance_participation"],
    },
    {
        "query": "Does Torilo offer an AI course?",
        "expected_document_ids": [
            "course_courses_catalog",
            "course_ai_engineering",
        ],
    },
    {
        "query": "Where can I find Torilo's Lagos campuses?",
        "expected_document_ids": ["academy_campuses_contact"],
    },
    {
        "query": "Are academy fees refundable?",
        "expected_document_ids": ["policy_refund"],
    },
    {
        "query": "What happens if I haven't paid all my fees before graduation?",
        "expected_document_ids": [
            "policy_certification",
            "policy_fees_payment",
        ],
    },
    {
        "query": "Can I get a certificate that is equivalent to a government qualification?",
        "expected_document_ids": ["policy_certification"],
    },
]


def evaluate():
    rag = RAGPipeline()

    total = len(TEST_CASES)
    top1_correct = 0
    top3_correct = 0
    top5_correct = 0
    intent_detected = 0

    print("=" * 70)
    print("HELD-OUT RAG EVALUATION")
    print("=" * 70)

    for index, test_case in enumerate(TEST_CASES, start=1):
        query = test_case["query"]
        expected_ids = set(
            test_case["expected_document_ids"]
        )

        response = rag.search(
            query=query,
            top_k=5,
            max_context_chunks=5
        )

        results = response.get("context", "")
        sources = response.get("sources", [])

        retrieved_ids = [
            source["document_id"]
            for source in sources
        ]

        top1_match = (
            bool(retrieved_ids)
            and retrieved_ids[0] in expected_ids
        )

        top3_match = any(
            document_id in expected_ids
            for document_id in retrieved_ids[:3]
        )

        top5_match = any(
            document_id in expected_ids
            for document_id in retrieved_ids[:5]
        )

        if top1_match:
            top1_correct += 1

        if top3_match:
            top3_correct += 1

        if top5_match:
            top5_correct += 1

        if response.get("intent"):
            intent_detected += 1

        print("\n" + "-" * 70)
        print(f"TEST {index}")
        print("-" * 70)
        print(f"Query: {query}")
        print(f"Expected: {list(expected_ids)}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"Intent: {response.get('intent')}")
        print(f"Top-1: {'PASS' if top1_match else 'FAIL'}")
        print(f"Top-3: {'PASS' if top3_match else 'FAIL'}")
        print(f"Top-5: {'PASS' if top5_match else 'FAIL'}")

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"Top-1 Accuracy: "
        f"{top1_correct}/{total} "
        f"({top1_correct / total:.2%})"
    )

    print(
        f"Top-3 Accuracy: "
        f"{top3_correct}/{total} "
        f"({top3_correct / total:.2%})"
    )

    print(
        f"Top-5 Accuracy: "
        f"{top5_correct}/{total} "
        f"({top5_correct / total:.2%})"
    )

    print(
        f"Queries with detected intent: "
        f"{intent_detected}/{total}"
    )


if __name__ == "__main__":
    evaluate()