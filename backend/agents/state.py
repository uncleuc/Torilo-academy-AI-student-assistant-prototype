"""Typed graph state and route definitions for student conversations."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

Route = Literal[
	"SAFETY",
	"RAG",
	"DATABASE",
	"GENERAL",
	"CLARIFY",
	"UNAVAILABLE",
	"UNKNOWN",
]
MessageRole = Literal["user", "assistant"]


class ChatMessage(TypedDict):
	role: MessageRole
	content: str


class RetrievedDocument(TypedDict, total=False):
	id: str
	content: str
	metadata: dict[str, Any]
	score: float


class AssistantState(TypedDict, total=False):
	"""Only request-scoped, serializable values are stored in graph state."""

	message: str
	conversation_id: str
	chat_history: list[ChatMessage]
	classification: dict[str, Any]
	route: Route
	retrieval_query: str
	database_query: str
	safety_blocked: bool
	safety_reason: str
	retrieved_documents: list[RetrievedDocument]
	database_results: Any
	database_tool: str | None
	sources: list[dict[str, Any]]
	answer: str
	retrieval_error: bool
	database_error: bool
	response_error: bool
	clarification_question: str


REQUIRED_INITIAL_STATE_KEYS = frozenset({"message", "conversation_id", "chat_history"})


def validate_initial_state(state: AssistantState) -> None:
	"""Fail early on malformed graph calls without disclosing user content."""
	missing = REQUIRED_INITIAL_STATE_KEYS.difference(state)
	if missing:
		raise ValueError(f"Missing graph state fields: {', '.join(sorted(missing))}")
	if not isinstance(state["message"], str) or not state["message"].strip():
		raise ValueError("message must be a non-empty string")
	if not isinstance(state["conversation_id"], str) or not state["conversation_id"].strip():
		raise ValueError("conversation_id must be a non-empty string")
	if not isinstance(state["chat_history"], list):
		raise TypeError("chat_history must be a list")
