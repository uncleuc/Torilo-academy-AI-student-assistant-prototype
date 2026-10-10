"""Read-only course lookup tools for Group 2 orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Course, Instructor


def _course_record(course: Course, instructor_name: str | None = None) -> dict[str, Any]:
	return {
		"course_id": str(course.id),
		"course_name": course.name,
		"description": course.description,
		"level": course.level,
		"duration_weeks": course.duration_weeks,
		"instructor_name": instructor_name,
		"data_status": (
			"synthetic_demo"
			if course.description.startswith("DEMO DB RECORD")
			else "verified_live"
		),
	}


def make_get_available_courses(
	session_factory: sessionmaker[Session],
) -> Callable[[], list[dict[str, Any]]]:
	"""Create the active-course callable expected by the assistant."""
	def get_available_courses() -> list[dict[str, Any]]:
		with session_factory() as session:
			rows = session.execute(
				select(Course, Instructor.full_name)
				.outerjoin(Instructor, Course.instructor_id == Instructor.id)
				.where(Course.is_active.is_(True))
				.order_by(Course.name, Course.id)
			).all()
			return [_course_record(course, name) for course, name in rows]

	return get_available_courses


def make_get_course_details(
	session_factory: sessionmaker[Session],
) -> Callable[[str], dict[str, Any] | None]:
	"""Create the active-course detail callable expected by the assistant."""
	def get_course_details(course_id: str) -> dict[str, Any] | None:
		try:
			parsed_id = int(course_id)
		except (TypeError, ValueError):
			return None
		if parsed_id <= 0:
			return None
		with session_factory() as session:
			row = session.execute(
				select(Course, Instructor.full_name)
				.outerjoin(Instructor, Course.instructor_id == Instructor.id)
				.where(Course.id == parsed_id, Course.is_active.is_(True))
			).one_or_none()
			if row is None:
				return None
			course, instructor_name = row
			return _course_record(course, instructor_name)

	return get_course_details