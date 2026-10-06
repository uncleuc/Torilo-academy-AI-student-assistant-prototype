from rag.retriever import Retriever
from rag.rag_retriever import RAGRetriever


EVALUATION_DATASET = [
    # ------------------------------------------------------------------
    # COURSE CATALOGUE
    # ------------------------------------------------------------------
    {
        "query": "What courses does Torilo Academy offer?",
        "expected_documents": {"course_courses_catalog"},
    },
    {
        "query": "List all the courses available at Torilo Academy.",
        "expected_documents": {"course_courses_catalog"},
    },
    {
        "query": "What training programmes does Torilo Academy have?",
        "expected_documents": {"course_courses_catalog"},
    },

    # ------------------------------------------------------------------
    # INDIVIDUAL COURSES
    # ------------------------------------------------------------------
    {
        "query": "What is the AI Engineering programme about?",
        "expected_documents": {"course_ai_engineering"},
    },
    {
        "query": "Tell me about the Generative AI course.",
        "expected_documents": {"course_generative_ai"},
    },
    {
        "query": "What does the Data Analysis programme cover?",
        "expected_documents": {"course_data_analysis"},
    },
    {
        "query": "What is covered in Cybersecurity and Ethical Hacking?",
        "expected_documents": {
            "course_cybersecurity_ethical_hacking"
        },
    },
    {
        "query": "What is the Software Development course about?",
        "expected_documents": {"course_software_development"},
    },

    # ------------------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------------------
    {
        "query": "What are the admission requirements?",
        "expected_documents": {"enrollment_requirements"},
    },
    {
        "query": "How do I apply to Torilo Academy?",
        "expected_documents": {
            "admissions_registration"
        },
    },
    {
        "query": "How do I register for a course?",
        "expected_documents": {
            "admissions_registration",
            "policy_enrollment",
        },
    },

    # ------------------------------------------------------------------
    # FEES & PAYMENT
    # ------------------------------------------------------------------
    {
        "query": "What happens if I don't pay my fees?",
        "expected_documents": {
            "policy_fees_payment"
        },
    },
    {
        "query": "What happens if my payment is late?",
        "expected_documents": {
            "policy_fees_payment"
        },
    },
    {
        "query": "When do I need to pay my fees?",
        "expected_documents": {
            "policy_fees_payment"
        },
    },

    # ------------------------------------------------------------------
    # REFUNDS
    # ------------------------------------------------------------------
    {
        "query": "Can I get a refund after withdrawing?",
        "expected_documents": {"policy_refund"},
    },
    {
        "query": "How long does a refund take?",
        "expected_documents": {"policy_refund"},
    },
    {
        "query": "What is the refund policy?",
        "expected_documents": {"policy_refund"},
    },

    # ------------------------------------------------------------------
    # ATTENDANCE
    # ------------------------------------------------------------------
    {
        "query": "What happens if I miss classes?",
        "expected_documents": {
            "policy_attendance_participation"
        },
    },
    {
        "query": "What are the attendance requirements?",
        "expected_documents": {
            "policy_attendance_participation"
        },
    },
    {
        "query": "What happens if I am absent from class?",
        "expected_documents": {
            "policy_attendance_participation"
        },
    },

    # ------------------------------------------------------------------
    # CERTIFICATION / COMPLETION
    # ------------------------------------------------------------------
    {
        "query": "What do I need to complete my course?",
        "expected_documents": {
            "policy_certification",
            "policy_enrollment",
        },
    },
    {
        "query": "How do I get my certificate?",
        "expected_documents": {
            "policy_certification"
        },
    },
    {
        "query": "What are the requirements for certification?",
        "expected_documents": {
            "policy_certification"
        },
    },

    # ------------------------------------------------------------------
    # STUDENT SUPPORT
    # ------------------------------------------------------------------
    {
        "query": "How do I contact Student Support?",
        "expected_documents": {
            "academy_student_support",
            "support-faq",
        },
    },
    {
        "query": "Who can I contact if I need help?",
        "expected_documents": {
            "academy_student_support",
            "support-faq",
        },
    },
    {
        "query": "Where can I get help as a student?",
        "expected_documents": {
            "academy_student_support",
            "support-faq",
        },
    },

    # ------------------------------------------------------------------
    # STUDENT CONDUCT
    # ------------------------------------------------------------------
    {
        "query": "What are the student conduct rules?",
        "expected_documents": {
            "policy_student_conduct"
        },
    },
    {
        "query": "What happens if a student violates the rules?",
        "expected_documents": {
            "policy_student_conduct"
        },
    },

    # ------------------------------------------------------------------
    # GENERAL ACADEMY
    # ------------------------------------------------------------------
    {
        "query": "Tell me about Torilo Academy.",
        "expected_documents": {
            "academy_academy_overview"
        },
    },
    {
        "query": "Where is Torilo Academy located?",
        "expected_documents": {
            "academy_campuses_contact"
        },
    },
    {
        "query": "How can I contact Torilo Academy?",
        "expected_documents": {
            "academy_campuses_contact",
            "academy_student_support",
        },
    },
]

def get_unique_document_ids(results):
    document_ids = []

    for result in results:
        document_id = result["document_id"]

        if document_id not in document_ids:
            document_ids.append(document_id)

    return document_ids


def evaluate_hit(retrieved_ids, expected_documents, k):
    return any(
        document_id in expected_documents
        for document_id in retrieved_ids[:k]
    )


def evaluate_systems(dataset):
    vector_retriever = Retriever()
    rag_retriever = RAGRetriever()

    results = []

    for item in dataset:
        query = item["query"]
        expected = item["expected_documents"]

        # -----------------------------
        # Vector-only retrieval
        # -----------------------------
        vector_results = vector_retriever.search(
            query=query,
            top_k=20,
        )

        vector_ids = get_unique_document_ids(
            vector_results
        )

        # -----------------------------
        # Hybrid/intent retrieval
        # -----------------------------
        rag_response = rag_retriever.search(
            query=query,
            top_k=5,
        )

        hybrid_ids = get_unique_document_ids(
            rag_response["results"]
        )

        results.append({
            "query": query,
            "expected": expected,
            "vector_ids": vector_ids,
            "hybrid_ids": hybrid_ids,
            "intent": rag_response["intent"],
            "method": rag_response["retrieval_method"],
            "vector_top_1": evaluate_hit(
                vector_ids,
                expected,
                1,
            ),
            "vector_top_3": evaluate_hit(
                vector_ids,
                expected,
                3,
            ),
            "vector_top_5": evaluate_hit(
                vector_ids,
                expected,
                5,
            ),
            "hybrid_top_1": evaluate_hit(
                hybrid_ids,
                expected,
                1,
            ),
            "hybrid_top_3": evaluate_hit(
                hybrid_ids,
                expected,
                3,
            ),
            "hybrid_top_5": evaluate_hit(
                hybrid_ids,
                expected,
                5,
            ),
        })

    return results

def calculate_accuracy(results, metric):
    if not results:
        return 0

    correct = sum(
        1
        for result in results
        if result[metric]
    )

    return correct / len(results)


def print_summary(results):
    print("\n" + "=" * 70)
    print("VECTOR VS HYBRID RETRIEVAL")
    print("=" * 70)

    print(f"Total queries: {len(results)}")

    print("\nVECTOR ONLY")
    print(
        f"Top-1: "
        f"{calculate_accuracy(results, 'vector_top_1'):.2%}"
    )
    print(
        f"Top-3: "
        f"{calculate_accuracy(results, 'vector_top_3'):.2%}"
    )
    print(
        f"Top-5: "
        f"{calculate_accuracy(results, 'vector_top_5'):.2%}"
    )

    print("\nHYBRID")
    print(
        f"Top-1: "
        f"{calculate_accuracy(results, 'hybrid_top_1'):.2%}"
    )
    print(
        f"Top-3: "
        f"{calculate_accuracy(results, 'hybrid_top_3'):.2%}"
    )
    print(
        f"Top-5: "
        f"{calculate_accuracy(results, 'hybrid_top_5'):.2%}"
    )

    print("\n" + "=" * 70)


def print_failures(results):
    print("\n" + "=" * 70)
    print("HYBRID RETRIEVAL FAILURES")
    print("=" * 70)

    for result in results:
        if not result["hybrid_top_3"]:
            print("\nQuery:", result["query"])
            print("Expected:", result["expected"])
            print("Intent:", result["intent"])
            print("Method:", result["method"])
            print("Retrieved:", result["hybrid_ids"])


def main():
    results = evaluate_systems(
        EVALUATION_DATASET
    )

    print_summary(results)
    print_failures(results)


if __name__ == "__main__":
    main()