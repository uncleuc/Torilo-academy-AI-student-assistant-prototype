"""Load deterministic synthetic development data into PostgreSQL."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

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

def _read_records(filename: str) -> list[dict[str, Any]]:
	path = SEED_DIR / filename
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
			_merge_rows(session, Student, _read_records("students.json"))
			_merge_rows(session, Course, _read_records("courses.json"))
			_merge_rows(session, Class, _read_records("classes.json"))
			_merge_rows(session, Enrollment, _read_records("enrollments.json"))
			session.commit()
		except Exception:
			session.rollback()
			raise


def main() -> None:
	"""Initialize a local development database and load synthetic fixtures."""
	engine = create_database_engine()
	try:
		Base.metadata.create_all(engine)
		seed_database(create_session_factory(engine))
		print("Synthetic development seed completed.")
	finally:
		engine.dispose()


if __name__ == "__main__":
	main()