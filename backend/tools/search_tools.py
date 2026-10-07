"""Bounded read-only substring search over active course names."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Course, Instructor

MAX_QUERY_LENGTH = 120
MAX_SEARCH_RESULTS = 20

def make_search_courses(
	session_factory: sessionmaker[Session],
) -> Callable[[str], list[dict[str, Any]]]:
	"""Create case-insensitive active-course search for concise name phrases."""
	def search_courses(query: str) -> list[dict[str, Any]]:
		if not isinstance(query, str):
			return []
		normalized = " ".join(query.split())
		if not normalized or len(normalized) > MAX_QUERY_LENGTH:
			return []
		pattern = f"%{normalized}%"
		with session_factory() as session:
			rows = session.execute(
				select(Course, Instructor.full_name)
				.outerjoin(Instructor, Course.instructor_id == Instructor.id)
				.where(Course.is_active.is_(True), Course.name.ilike(pattern))
				.order_by(Course.name, Course.id)
				.limit(MAX_SEARCH_RESULTS)
			).all()
			return [
				{
					"course_id": str(course.id),
					"course_name": course.name,
					"description": course.description,
					"level": course.level,
					"duration_weeks": course.duration_weeks,
					"instructor_name": instructor_name,
				}
				for course, instructor_name in rows
			]

	return search_courses