from backend.agents.router import route_message
from backend.rag.query_intent import detect_intent

KB_BACKED_QUESTIONS = (
	"what happens if i miss class",
	"what happens if i missed class",
	"what happens if i missed a class",
	"what happens if i miss classes?",
	"what is the AI engineering course overview",
	"what is torilo academy AI engineering course overview",
	"How can i gain admission to torilo academy",
)


def test_available_knowledge_base_questions_route_to_rag():
	for question in KB_BACKED_QUESTIONS:
		assert route_message(question) == ("RAG", None)


def test_specific_course_overview_does_not_become_academy_overview_intent():
	intent = detect_intent("what is torilo academy AI engineering course overview")
	assert intent is None


def test_admissions_query_uses_admissions_document_intent():
	intent = detect_intent("How can i gain admission to torilo academy")
	assert intent == {
		"intent": "admissions",
		"document_type": "Admissions and Registration",
	}