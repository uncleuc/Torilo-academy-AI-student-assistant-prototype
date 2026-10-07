"""Evidence checks and deterministic no-evidence answer policies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

UNKNOWN_RESPONSE = (
	"I don't have enough verified information to answer that question. "
	"Please check an official Torilo Academy source or contact the appropriate support team."
)


def has_approved_rag_evidence(
	context: Sequence[Mapping[str, Any]],
) -> bool:
	for item in context:
		metadata = item.get("metadata", {})
		if not isinstance(metadata, Mapping):
			continue
		approved = metadata.get("approved", True)
		if approved is True and isinstance(item.get("content"), str) and item["content"].strip():
			return True
	return False


def has_database_evidence(results: Any) -> bool:
	"""Consider only non-empty returned records evidence; exceptions are not evidence."""
	if results is None:
		return False
	if isinstance(results, (list, tuple, set, dict, str)):
		return len(results) > 0
	return True


def answer_is_usable(answer: str | None) -> bool:
	return isinstance(answer, str) and bool(answer.strip())


def grounded_fallback() -> str:
	return UNKNOWN_RESPONSE
