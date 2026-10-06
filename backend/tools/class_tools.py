"""Read-only retrieval of active class records."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
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
				}
				for class_row, course_name, instructor_name in rows
			]

	return get_active_classes