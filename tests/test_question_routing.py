from backend.agents.classifier import (
	classify_message,
	deterministic_classification,
	route_classification,
)
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
	"what is torilo Academy",
	"what courses does torilo academy offer",
	"how long is the AI engineering mastery program",
	"What topics are covered in the AI engineering program",
	"where are torilo academy campuses located",
	"if i cant attend class what should i do?",
	"can i study at torilo remotely or do i have to attend physically",
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


def test_classified_public_facts_route_to_rag_and_not_database():
	for question in KB_BACKED_QUESTIONS:
		classification = deterministic_classification(question)
		route, tool = route_message(question)
		assert route == "RAG", (question, classification.model_dump())
		assert tool is None, question


def test_live_class_schedule_is_time_sensitive_and_selects_live_tool():
	classification = deterministic_classification("what class is the python class holding")

	assert classification.intent == "class_schedule"
	assert classification.entities.course == "Python"
	assert classification.time_sensitive is True
	assert route_message("what class is the python class holding") == (
		"DATABASE", "search_classes"
	)


def test_backend_instructor_question_is_classified_and_sent_to_kb_first():
	classification = deterministic_classification("Which instructor teaches the backend course?")

	assert classification.intent == "course_instructor"
	assert classification.entities.course == "Backend Development"
	assert route_message("Which instructor teaches the backend course?") == ("RAG", None)


def test_vague_academy_request_requires_clarification():
	classification = deterministic_classification("Tell me more about it")

	assert classification.clarification_needed is True
	assert classification.clarification_question


def test_structured_classifier_validates_model_decision():
	class FakeStructuredModel:
		def with_structured_output(self, schema):
			assert schema.__name__ == "QueryClassification"
			return self

		def invoke(self, messages):
			assert "AI Engineering" in messages[-1].content
			return {
				"intent": "course_information",
				"entities": {"course": "AI Engineering", "campus": None, "topic": "duration"},
				"time_sensitive": False,
				"confidence": 0.98,
				"clarification_needed": False,
				"clarification_question": None,
			}

	classification = classify_message(FakeStructuredModel(), "How long is AI Engineering?")

	assert classification.intent == "course_information"
	assert classification.entities.course == "AI Engineering"
	assert route_classification(classification) == ("RAG", None)


def test_live_intent_is_unavailable_without_verified_tool():
	classification = deterministic_classification("What is the current Python class schedule?")

	assert route_classification(classification) == ("UNAVAILABLE", None)
