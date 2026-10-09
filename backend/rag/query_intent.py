
INTENT_RULES = {
    "course_catalogue": {
        "document_type": "Course Catalogue",
        "keywords": [
            "what courses",
            "which courses",
            "courses available",
            "courses offered",
            "courses do you offer",
            "course catalogue",
            "course catalog",
            "course list",

            "what programmes",
            "which programmes",
            "programmes available",
            "programmes offered",
            "what programs",
            "which programs",
            "programs available",
            "programs offered",

            "training programmes",
            "training programs",

            "what can i study",
            "which courses can i study",
            "what can i learn",
            "what do you offer",

            "which technology programmes",
            "which technology programs",
            "technology programmes",
            "technology programs",
        ],
    },

    "refund": {
        "document_type": "Refund Policy",
        "keywords": [
            "refund",
            "money back",
            "get my money back",
            "withdraw and get",
            "withdrawal refund",
        ],
    },

    "fees": {
        "document_type": "Fees and Payment Policy",
        "keywords": [
            "fees",
            "payment",
            "pay my fees",
            "late payment",
            "payment deadline",
            "owe",
            "cost",
        ],
    },

    "attendance": {
        "document_type": "Attendance and Participation Policy",
        "keywords": [
            "attendance",
            "miss class",
            "miss classes",
            "missing class",
            "missing classes",
            "absent",
            "absence",
            "late to class",
            "classes",
        ],
    },

    "certification": {
        "document_type": "Certification and Course Completion Policy",
        "keywords": [
            "certificate",
            "certification",
            "complete my course",
            "completion",
            "graduate",
            "graduation",
        ],
    },

    "student_support": {
        "document_type": "Student Support",
        "keywords": [
            "student support",
            "student support team",
            "contact support",
            "contact student support",
            "support team",
            "help desk",
            "get help",
        ],
    },

    "admission_requirements": {
    "document_type": "Enrollment Requirements",
    "keywords": [
        "admission requirements",
        "admission requirement",
        "requirements for admission",
        "requirements to apply",
        "what do i need to apply",
        "what do i need for admission",
    ],
},

    "academy_overview": {
    "document_type": "Academy Overview",
    "keywords": [
        "tell me about torilo academy",
        "about torilo academy",
        "what is torilo academy",
        "who is torilo academy",
        "overview of torilo academy",
        "general information about torilo academy",
    ],
},

    "academy_location": {
    "document_type": "Contact and Campus Information",
    "keywords": [
        "where is torilo academy",
        "where is torilo",
        "torilo academy location",
        "torilo academy located",
        "campus location",
        "where are your campuses",
        "where is your campus",
    ],
},

    "admissions": {
        "document_type": "Admissions and Registration",
        "keywords": [
            "admission",
            "admissions",
            "apply",
            "application",
            "registration",
            "enrol",
            "enroll",
            "enrollment",
            "requirements",
        ],
    },
}


def detect_intent(query: str) -> dict | None:
    query_lower = query.lower().strip()

    course_specific_overview = (
        any(term in query_lower for term in ("course", "programme", "program"))
        and any(term in query_lower for term in ("overview", "curriculum", "course content"))
    )
    if course_specific_overview:
        return None

    for intent, config in INTENT_RULES.items():
        for keyword in config["keywords"]:
            if keyword in query_lower:
                return {
                    "intent": intent,
                    "document_type": config["document_type"],
                }

    return None