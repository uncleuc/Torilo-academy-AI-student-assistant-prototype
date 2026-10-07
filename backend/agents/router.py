"""Deterministic intent routing for RAG, database, general, and unknown turns."""

from __future__ import annotations

import re
from collections.abc import Sequence

from backend.agents.state import ChatMessage, Route

_GREETING = re.compile(
	r"^(hi|hello|hey|good morning|good afternoon|good evening|thanks|thank you)"
	r"[.!?, ]*$",
	re.IGNORECASE,
)
_DATABASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
	(re.compile(r"\b(available courses|list courses|courses available|what courses)\b", re.IGNORECASE), "get_available_courses"),
	(re.compile(r"\b(active classes|current classes|which classes)\b", re.IGNORECASE), "get_active_classes"),
	(re.compile(r"\b(who teaches|course instructor|instructor for|teacher for)\b", re.IGNORECASE), "get_course_instructor"),
	(re.compile(r"\b(course details|details of the course|tell me about the course)\b", re.IGNORECASE), "get_course_details"),
	(re.compile(r"\b(search courses|find courses|search for courses)\b", re.IGNORECASE), "search_courses"),
)
_RAG_TERMS = re.compile(
	r"\b(attendance|absence|miss a class|missed a class|assessment|exam|refund|payment|"
	r"conduct|handbook|student procedure|support procedure|faq|policy|policies)\b",
	re.IGNORECASE,
)
_ACADEMY_MARKERS = re.compile(
	r"\b(torilo|academy|student|students|course|courses|class|classes|instructor|"
	r"tuition|fee|fees|refund|attendance|assessment|programme|program)\b",
	re.IGNORECASE,
)
_FOLLOW_UP = re.compile(
	r"^(what about|what if|and if|why|how about|does that|is that|can i|what then|"
	r"in that case|they|it|that)\b",
	re.IGNORECASE,
)


def choose_database_tool(message: str) -> str | None:
	"""Return the stable Group 3 tool name or None when intent is ambiguous."""
	for pattern, tool_name in _DATABASE_PATTERNS:
		if pattern.search(message):
			return tool_name
	return None


def _previous_database_tool(history: Sequence[ChatMessage]) -> str | None:
	"""Return the most recent explicit database tool intent."""
	for item in reversed(history):
		if item.get("role") != "user":
			continue
		tool_name = choose_database_tool(item.get("content", ""))
		if tool_name:
			return tool_name
	return None


_COURSE_QUERY_PATTERNS = (
	(re.compile(r"^\s*who teaches\s+(?:the\s+)?(.+?)\s*[?.!]*$", re.IGNORECASE), "get_course_instructor"),
	(re.compile(r"^\s*(?:course instructor|instructor for|teacher for)\s+(?:the\s+)?(.+?)\s*[?.!]*$", re.IGNORECASE), "get_course_instructor"),
	(re.compile(r"^\s*(?:course details|details of the course|tell me about the course)\s+(?:for|about|on)?\s*(.+?)\s*[?.!]*$", re.IGNORECASE), "get_course_details"),
	(re.compile(r"^\s*(?:search for|search|find) courses\s+(?:for|about|named)?\s*(.+?)\s*[?.!]*$", re.IGNORECASE), "search_courses"),
)


def extract_course_search_query(message: str, tool_name: str | None) -> str:
	"""Return the concise course phrase Group 3's name search expects."""
	cleaned = " ".join(message.split()).strip(" ?.!\t")
	for pattern, expected_tool in _COURSE_QUERY_PATTERNS:
		match = pattern.match(cleaned)
		if match and expected_tool == tool_name:
			cleaned = match.group(1).strip(" ?.!\t")
			break
	cleaned = re.sub(r"\s+course$", "", cleaned, flags=re.IGNORECASE).strip()
	return cleaned[:120]


def _previous_academy_route(history: Sequence[ChatMessage]) -> Route | None:
	"""Infer a follow-up route from the most recent prior user turn."""
	for item in reversed(history):
		if item.get("role") != "user":
			continue
		previous = item.get("content", "")
		tool = choose_database_tool(previous)
		if tool:
			return "DATABASE"
		if _RAG_TERMS.search(previous):
			return "RAG"
		if _ACADEMY_MARKERS.search(previous):
			return "UNKNOWN"
	return None


def route_message(message: str, history: Sequence[ChatMessage] = ()) -> tuple[Route, str | None]:
	"""Classify a turn without making any academy-fact claims."""
	clean_message = " ".join(message.split())
	if _GREETING.fullmatch(clean_message):
		return "GENERAL", None

	database_tool = choose_database_tool(clean_message)
	if database_tool is not None:
		return "DATABASE", database_tool

	if _RAG_TERMS.search(clean_message):
		return "RAG", None

	if _FOLLOW_UP.search(clean_message):
		previous_route = _previous_academy_route(history)
		if previous_route is not None:
			tool_name = _previous_database_tool(history) if previous_route == "DATABASE" else None
			return previous_route, tool_name

	if _ACADEMY_MARKERS.search(clean_message):
		return "UNKNOWN", None

	# Do not treat arbitrary requests as harmless small talk: generic general
	# responses are limited to greetings and simple social exchanges.
	if len(clean_message.split()) <= 3 and not clean_message.endswith("?"):
		return "GENERAL", None
	return "UNKNOWN", None


def build_contextual_rag_query(
	message: str,
	history: Sequence[ChatMessage] = (),
) -> str:
	"""Add the last RAG-related user question when the current turn is elliptical."""
	current = " ".join(message.split())
	if not _FOLLOW_UP.search(current):
		return current
	for item in reversed(history):
		if item.get("role") != "user":
			continue
		previous = " ".join(item.get("content", "").split())
		if _RAG_TERMS.search(previous):
			return f"{previous[:400]} {current}"[:500]
		if choose_database_tool(previous):
			break
	return current


def build_contextual_database_query(
	message: str,
	history: Sequence[ChatMessage] = (),
	tool_name: str | None = None,
) -> str:
	"""Reuse the previous course phrase for a fresh lookup on a database follow-up."""
	current = extract_course_search_query(message, tool_name)
	if not _FOLLOW_UP.search(" ".join(message.split())):
		return current
	if tool_name not in {"get_course_details", "get_course_instructor"}:
		return current
	for item in reversed(history):
		if item.get("role") != "user":
			continue
		previous = item.get("content", "")
		previous_tool = choose_database_tool(previous)
		if previous_tool in {"get_course_details", "get_course_instructor", "search_courses"}:
			return extract_course_search_query(previous, previous_tool)
		if previous_tool:
			break
	return current
