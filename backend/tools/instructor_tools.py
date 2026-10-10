"""Read-only instructor lookup by an active course identifier."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Course, Instructor


def make_get_course_instructor(
	session_factory: sessionmaker[Session],
) -> Callable[[str], dict[str, Any] | None]:
	"""Create the course-instructor callable expected by the assistant."""
	def get_course_instructor(course_id: str) -> dict[str, Any] | None:
		try:
			parsed_id = int(course_id)
		except (TypeError, ValueError):
			return None
		if parsed_id <= 0:
			return None
		with session_factory() as session:
			row = session.execute(
				select(Course.id, Course.name, Instructor.full_name)
				.join(Instructor, Course.instructor_id == Instructor.id)
				.where(
					Course.id == parsed_id,
					Course.is_active.is_(True),
					Instructor.is_active.is_(True),
				)
			).one_or_none()
			if row is None:
				return None
			return {
				"course_id": str(row.id),
				"course_name": row.name,
				"instructor_name": row.full_name,
				"data_status": (
					"synthetic_demo"
					if row.full_name.startswith("Demo ")
					else "verified_live"
				),
			}

	return get_course_instructor