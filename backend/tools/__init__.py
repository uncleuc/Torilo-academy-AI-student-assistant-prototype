"""Dependency-injected database tools exposed to the assistant graph."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from backend.tools.class_tools import make_get_active_classes, make_search_classes
from backend.tools.course_tools import (
	make_get_available_courses,
	make_get_course_details,
)
from backend.tools.instructor_tools import make_get_course_instructor
from backend.tools.search_tools import make_search_courses


def build_database_tools(
	session_factory: sessionmaker[Session],
) -> dict[str, Callable[..., Any]]:
	"""Build the stable read-only tool allowlist without opening a connection."""
	return {
		"get_available_courses": make_get_available_courses(session_factory),
		"get_course_details": make_get_course_details(session_factory),
		"get_course_instructor": make_get_course_instructor(session_factory),
		"get_active_classes": make_get_active_classes(session_factory),
		"search_classes": make_search_classes(session_factory),
		"search_courses": make_search_courses(session_factory),
	}