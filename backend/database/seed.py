"""Load deterministic synthetic development data into PostgreSQL."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import Settings, get_settings
from backend.database.database import create_database_engine, create_session_factory
from backend.database.models import (
	Base,
	Class,
	Course,
	Enrollment,
	Instructor,
	Student,
)

SEED_DIR = Path(__file__).resolve().parent / "seed_data"

def _read_records(filename: str, *, optional: bool = False) -> list[dict[str, Any]]:
	path = SEED_DIR / filename
	if optional and not path.is_file():
		return []
	try:
		value = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError as exc:
		raise ValueError(f"Invalid JSON seed file: {filename}") from exc
	if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
		raise ValueError(f"Seed file must contain a JSON array of objects: {filename}")
	return value


def _parse_datetime(value: str | datetime | None) -> datetime | None:
	if value is None or isinstance(value, datetime):
		return value
	parsed = datetime.fromisoformat(value)
	if parsed.tzinfo is None:
		raise ValueError("Seed datetimes must include a timezone offset")
	return parsed


def _merge_rows(
	session: Session,
	model: type[Base],
	records: list[dict[str, Any]],
) -> None:
	for record in records:
		values = dict(record)
		for field in ("starts_at", "ends_at", "enrolled_at"):
			if field in values:
				values[field] = _parse_datetime(values[field])
		session.merge(model(**values))


def seed_database(session_factory: sessionmaker[Session]) -> None:
	"""Idempotently merge seed rows in dependency order and one transaction."""
	with session_factory() as session:
		try:
			_merge_rows(session, Instructor, _read_records("instructors.json"))
			_merge_rows(session, Student, _read_records("students.json", optional=True))
			_merge_rows(session, Course, _read_records("courses.json"))
			_merge_rows(session, Class, _read_records("classes.json"))
			_merge_rows(session, Enrollment, _read_records("enrollments.json", optional=True))
			session.commit()
		except Exception:
			session.rollback()
			raise


def _demo_seed_is_complete(session: Session) -> bool:
	courses = _read_records("courses.json")
	instructors = _read_records("instructors.json")
	classes = _read_records("classes.json")
	for record in courses:
		course = session.get(Course, record["id"])
		if course is None or course.name != record["name"]:
			return False
		if record["is_active"] and not course.description.startswith("DEMO DB RECORD"):
			return False
	for record in instructors:
		instructor = session.get(Instructor, record["id"])
		if instructor is None or instructor.full_name != record["full_name"]:
			return False
	for record in classes:
		class_row = session.get(Class, record["id"])
		if class_row is None or class_row.course_id != record["course_id"]:
			return False
		if record["id"] != 1 and not (class_row.location or "").startswith("DEMO ONLY"):
			return False
	return True


def _assert_demo_seed_will_not_overwrite(session: Session) -> None:
	expected_courses = {
		record["id"]: record["name"] for record in _read_records("courses.json")
	}
	expected_instructors = {
		record["id"]: record["full_name"] for record in _read_records("instructors.json")
	}
	expected_classes = {
		record["id"]: record["course_id"] for record in _read_records("classes.json")
	}
	legacy_courses = {1: "Synthetic Python Course", 2: "Synthetic Data Course"}
	legacy_instructors = {1: "Sample Instructor One", 2: "Sample Instructor Two"}
	for course in session.scalars(select(Course)):
		if course.id not in expected_courses or course.name not in {
			expected_courses.get(course.id), legacy_courses.get(course.id)
		}:
			raise RuntimeError(
				"Demo setup found an unrecognized course record and will not overwrite it. "
				"Use a dedicated empty development database."
			)
	for instructor in session.scalars(select(Instructor)):
		if instructor.id not in expected_instructors or instructor.full_name not in {
			expected_instructors.get(instructor.id), legacy_instructors.get(instructor.id)
		}:
			raise RuntimeError(
				"Demo setup found an unrecognized instructor record and will not overwrite it. "
				"Use a dedicated empty development database."
			)
	for class_row in session.scalars(select(Class)):
		if class_row.id not in expected_classes or class_row.course_id != expected_classes.get(class_row.id):
			raise RuntimeError(
				"Demo setup found an unrecognized class record and will not overwrite it. "
				"Use a dedicated empty development database."
			)


def seed_demo_database_once(
	session_factory: sessionmaker[Session],
	*,
	settings: Settings,
	engine: Engine,
) -> bool:
	"""Seed local demo fixtures only when absent; never overwrite unknown records."""
	if settings.environment.lower() != "development" or not settings.database_demo_mode:
		print("Demo database seed skipped; enable DATABASE_DEMO_MODE in development to seed locally.")
		return False
	if settings.database_data_verified:
		raise RuntimeError(
			"Demo seed is disabled while DATABASE_DATA_VERIFIED=true. "
			"Use DATABASE_DEMO_MODE with verified data disabled."
		)

	Base.metadata.create_all(engine)
	with session_factory() as session:
		if _demo_seed_is_complete(session):
			print("Demo database seed already present; no seed rows changed.")
			return False
		_assert_demo_seed_will_not_overwrite(session)

	if engine.dialect.name == "postgresql":
		migration_path = Path(__file__).resolve().parent / "migrations" / "001_course_duration_nullable.sql"
		with engine.begin() as connection:
			for statement in migration_path.read_text(encoding="utf-8").split(";"):
				if statement.strip():
					connection.exec_driver_sql(statement)

	seed_database(session_factory)
	if engine.dialect.name == "postgresql":
		with engine.begin() as connection:
			for table in ("courses", "instructors", "classes"):
				connection.execute(
					text(
						f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
						f"COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
					)
				)
	print("Demo database seed completed for local development.")
	return True


def main() -> None:
	"""Initialize the local demo database once when demo mode is enabled."""
	settings = get_settings()
	if settings.environment.lower() != "development" or not settings.database_demo_mode:
		print("Demo database seed skipped; enable DATABASE_DEMO_MODE in development to seed locally.")
		return
	if not settings.database_url:
		raise RuntimeError("DATABASE_URL is required when DATABASE_DEMO_MODE=true.")
	engine = create_database_engine()
	try:
		seed_demo_database_once(
			create_session_factory(engine),
			settings=settings,
			engine=engine,
		)
	finally:
		engine.dispose()


if __name__ == "__main__":
	main()