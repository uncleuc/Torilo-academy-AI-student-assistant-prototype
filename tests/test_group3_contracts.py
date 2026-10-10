from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.main import create_app
from backend.config import Settings
from backend.database.models import Base, Class, Course, Enrollment, Instructor, Student
from backend.database.seed import seed_database, seed_demo_database_once
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
		assert session.scalar(select(func.count()).select_from(Instructor)) == 5
		assert session.scalar(select(func.count()).select_from(Student)) == 0
		assert session.scalar(select(func.count()).select_from(Course)) == 16
		assert session.scalar(select(func.count()).select_from(Class)) == 5
		assert session.scalar(select(func.count()).select_from(Enrollment)) == 0

	tools = build_database_tools(session_factory)
	courses = tools["get_available_courses"]()
	assert len(courses) == 14
	assert courses[0]["course_name"] == "AI Engineering"
	assert tools["get_course_details"]("3")["course_name"] == "AI Engineering"
	assert tools["get_course_instructor"]("3")["instructor_name"] == "Demo Adaeze Nwosu"
	assert tools["get_course_instructor"]("3")["data_status"] == "synthetic_demo"
	assert tools["search_courses"]("Backend")[0]["course_id"] == "9"
	assert tools["get_course_details"]("invalid") is None
	assert tools["get_active_classes"]() == []
	assert tools["search_classes"]("AI Engineering")[0]["data_status"] == "synthetic_demo"
	assert all("email" not in record for record in courses)


def test_setup_demo_seed_runs_once_and_refuses_unrecognized_course(session_factory):
	settings = Settings.from_env(
		{
			"ENVIRONMENT": "development",
			"DATABASE_DATA_VERIFIED": "false",
			"DATABASE_DEMO_MODE": "true",
		}
	)
	engine = session_factory.kw["bind"]

	assert seed_demo_database_once(session_factory, settings=settings, engine=engine) is True
	assert seed_demo_database_once(session_factory, settings=settings, engine=engine) is False
	with session_factory() as session:
		assert session.scalar(select(func.count()).select_from(Course)) == 16

	conflict_engine = create_engine(
		"sqlite+pysqlite:///:memory:",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	Base.metadata.create_all(conflict_engine)
	conflict_factory = sessionmaker(bind=conflict_engine, class_=Session)
	try:
		with conflict_factory.begin() as session:
			session.add(
				Course(
					id=1,
					name="Actual Academy Course",
					description="Existing data",
					level="unspecified",
					duration_weeks=8,
					is_active=True,
				)
			)
		with pytest.raises(RuntimeError, match="will not overwrite"):
			seed_demo_database_once(
				conflict_factory,
				settings=settings,
				engine=conflict_engine,
			)
	finally:
		conflict_engine.dispose()


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
		database_data_verified=True,
	)
	with TestClient(app) as client:
		health = client.get("/api/health")
		courses = client.get("/api/courses")
		course = client.get("/api/courses/3")
		missing = client.get("/api/courses/999")

	assert health.status_code == 200
	assert health.json() == {"status": "healthy", "database": "healthy"}
	assert courses.status_code == 200
	assert len(courses.json()) == 14
	assert courses.json()[0]["course_id"] == "3"
	assert courses.json()[0]["course_name"] == "AI Engineering"
	assert course.status_code == 200
	assert course.json()["course_name"] == "AI Engineering"
	assert missing.status_code == 404


def test_unverified_database_is_not_exposed_through_public_course_api(session_factory):
	seed_database(session_factory)
	app = create_app(
		assistant_runner=lambda *_: {},
		database_tools=build_database_tools(session_factory),
		session_factory=session_factory,
		database_data_verified=False,
		database_demo_mode=False,
	)
	with TestClient(app) as client:
		courses = client.get("/api/courses")
		course = client.get("/api/courses/1")

	assert courses.status_code == 503
	assert course.status_code == 503


def test_development_demo_mode_exposes_only_marked_seed_records(session_factory):
	seed_database(session_factory)
	app = create_app(
		assistant_runner=lambda *_: {},
		database_tools=build_database_tools(session_factory),
		session_factory=session_factory,
		database_data_verified=False,
		database_demo_mode=True,
	)
	with TestClient(app) as client:
		response = client.get("/api/courses")

	assert response.status_code == 200
	assert len(response.json()) == 14
	assert all(record["data_status"] == "synthetic_demo" for record in response.json())
