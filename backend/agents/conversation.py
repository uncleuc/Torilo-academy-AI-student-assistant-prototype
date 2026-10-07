"""Validate student turns and provide stable conversation identifiers."""

from __future__ import annotations

from uuid import uuid4

from backend.agents.memory import ConversationMemory, copy_history
from backend.agents.state import ChatMessage

MAX_MESSAGE_LENGTH = 8_000


def normalize_message(message: str) -> str:
	"""Validate and normalize a message without changing its meaning."""
	if not isinstance(message, str):
		raise TypeError("message must be a string")
	normalized = message.strip()
	if not normalized:
		raise ValueError("message must not be empty")
	if len(normalized) > MAX_MESSAGE_LENGTH:
		raise ValueError(f"message must be no longer than {MAX_MESSAGE_LENGTH} characters")
	return normalized


def resolve_conversation_id(conversation_id: str | None) -> str:
	"""Use a supplied non-empty identifier or generate a random UUID."""
	if conversation_id is None or not conversation_id.strip():
		return str(uuid4())
	resolved = conversation_id.strip()
	if len(resolved) > 128:
		raise ValueError("conversation_id must be no longer than 128 characters")
	return resolved


def load_conversation_history(
	memory: ConversationMemory,
	conversation_id: str,
) -> list[ChatMessage]:
	return copy_history(memory.get_history(conversation_id))


def save_conversation_turn(
	memory: ConversationMemory,
	conversation_id: str,
	user_message: str,
	assistant_message: str,
) -> None:
	memory.append_turn(conversation_id, user_message, assistant_message)
