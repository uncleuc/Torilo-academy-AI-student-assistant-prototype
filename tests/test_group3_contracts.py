from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.main import create_app
from backend.database.models import Base, Class, Course, Enrollment, Instructor, Student
from backend.database.seed import seed_database
from backend.tools import build_database_tools


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
	engine = create_engine(
		"sqlite+pysqlite:///:memory:",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	Base.metadata.create_all(engine)
	factory = sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False)
	try:
		yield factory
	finally:
		engine.dispose()


def test_seed_is_idempotent_and_tools_return_public_records(session_factory):
	seed_database(session_factory)
	seed_database(session_factory)

	with session_factory() as session:
		assert session.scalar(select(func.count()).select_from(Instructor)) == 2
		assert session.scalar(select(func.count()).select_from(Student)) == 1
		assert session.scalar(select(func.count()).select_from(Course)) == 2
		assert session.scalar(select(func.count()).select_from(Class)) == 1
		assert session.scalar(select(func.count()).select_from(Enrollment)) == 1

	tools = build_database_tools(session_factory)
	courses = tools["get_available_courses"]()
	assert [record["course_name"] for record in courses] == [
		"Synthetic Data Course",
		"Synthetic Python Course",
	]
	assert tools["get_course_details"]("1")["course_name"] == "Synthetic Python Course"
	assert tools["get_course_instructor"]("1")["instructor_name"] == "Sample Instructor One"
	assert tools["search_courses"]("Python")[0]["course_id"] == "1"
	assert tools["get_course_details"]("invalid") is None
	assert tools["get_active_classes"]() == []
	assert all("email" not in record for record in courses)


def test_chat_delegates_to_injected_runner_and_returns_its_response(session_factory):
	calls = []

	def runner(message, conversation_id=None):
		calls.append((message, conversation_id))
		return {
			"answer": "Answer supplied by injected assistant.",
			"sources": [],
			"conversation_id": "conversation-from-runner",
		}

	app = create_app(
		assistant_runner=runner,
		database_tools=build_database_tools(session_factory),
		session_factory=session_factory,
	)
	with TestClient(app) as client:
		response = client.post(
			"/api/chat",
			json={"message": "  hello  ", "conversation_id": "  client-conversation  "},
		)

	assert response.status_code == 200
	assert response.json() == {
		"answer": "Answer supplied by injected assistant.",
		"sources": [],
		"conversation_id": "conversation-from-runner",
	}
	assert calls == [("hello", "client-conversation")]


def test_invalid_chat_request_does_not_call_assistant(session_factory):
	calls = []
	app = create_app(
		assistant_runner=lambda *args: calls.append(args),
		database_tools={},
		session_factory=session_factory,
	)
	with TestClient(app) as client:
		response = client.post("/api/chat", json={"message": "   "})

	assert response.status_code == 422
	assert calls == []


def test_health_and_course_endpoints_use_injected_services(session_factory):
	seed_database(session_factory)
	app = create_app(
		assistant_runner=lambda *_: {},
		database_tools=build_database_tools(session_factory),
		session_factory=session_factory,
	)
	with TestClient(app) as client:
		health = client.get("/api/health")
		courses = client.get("/api/courses")
		course = client.get("/api/courses/1")
		missing = client.get("/api/courses/999")

	assert health.status_code == 200
	assert health.json() == {"status": "healthy", "database": "healthy"}
	assert courses.status_code == 200
	assert len(courses.json()) == 2
	assert courses.json()[0]["course_id"] == "2"
	assert courses.json()[0]["course_name"] == "Synthetic Data Course"
	assert course.status_code == 200
	assert course.json()["course_name"] == "Synthetic Python Course"
	assert missing.status_code == 404