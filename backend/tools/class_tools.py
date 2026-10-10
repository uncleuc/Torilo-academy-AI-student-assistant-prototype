"""Read-only retrieval of active class records."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Class, Course, Instructor


def make_get_active_classes(
	session_factory: sessionmaker[Session],
) -> Callable[[], list[dict[str, Any]]]:
	"""Create the active-class callable expected by the assistant."""
	def get_active_classes() -> list[dict[str, Any]]:
		with session_factory() as session:
			rows = session.execute(
				select(Class, Course.name, Instructor.full_name)
				.join(Course, Class.course_id == Course.id)
				.outerjoin(Instructor, Class.instructor_id == Instructor.id)
				.where(Class.status == "active", Course.is_active.is_(True))
				.order_by(Class.starts_at, Class.id)
			).all()
			return [
				{
					"class_id": str(class_row.id),
					"course_id": str(class_row.course_id),
					"course_name": course_name,
					"instructor_name": instructor_name,
					"starts_at": class_row.starts_at.isoformat(),
					"ends_at": class_row.ends_at.isoformat(),
					"location": class_row.location,
					"status": class_row.status,
					"data_status": (
						"synthetic_demo"
						if (class_row.location or "").startswith("Synthetic Room")
						or (class_row.location or "").startswith("DEMO ONLY")
						else "verified_live"
					),
				}
				for class_row, course_name, instructor_name in rows
			]

	return get_active_classes


def make_search_classes(
	session_factory: sessionmaker[Session],
) -> Callable[[str], list[dict[str, Any]]]:
	"""Find planned/upcoming or active classes by course name."""
	def search_classes(query: str) -> list[dict[str, Any]]:
		if not isinstance(query, str):
			return []
		normalized = " ".join(query.split())
		if not normalized or len(normalized) > 120:
			return []
		with session_factory() as session:
			rows = session.execute(
				select(Class, Course.name, Instructor.full_name)
				.join(Course, Class.course_id == Course.id)
				.outerjoin(Instructor, Class.instructor_id == Instructor.id)
				.where(
					Course.is_active.is_(True),
					Course.name.ilike(f"%{normalized}%"),
					Class.status.in_(("planned", "active")),
					Class.ends_at >= func.now(),
				)
				.order_by(Class.starts_at, Class.id)
				.limit(20)
			).all()
			return [
				{
					"class_id": str(class_row.id),
					"course_id": str(class_row.course_id),
					"course_name": course_name,
					"instructor_name": instructor_name,
					"starts_at": class_row.starts_at.isoformat(),
					"ends_at": class_row.ends_at.isoformat(),
					"location": class_row.location,
					"status": class_row.status,
					"data_status": (
						"synthetic_demo"
						if (class_row.location or "").startswith("DEMO ONLY")
						else "verified_live"
					),
				}
				for class_row, course_name, instructor_name in rows
			]

	return search_classes