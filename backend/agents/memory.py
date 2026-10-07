"""Conversation-history interface and thread-safe development store."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Sequence
from threading import RLock
from typing import Protocol

from backend.agents.state import ChatMessage


class ConversationMemory(Protocol):
	def get_history(self, conversation_id: str) -> list[ChatMessage]: ...

	def append_turn(
		self,
		conversation_id: str,
		user_message: str,
		assistant_message: str,
	) -> None: ...


class InMemoryConversationMemory:
	"""Bounded process-local memory for tests and early development only."""

	def __init__(self, max_messages: int = 20) -> None:
		if max_messages < 2:
			raise ValueError("max_messages must be at least 2")
		self._max_messages = max_messages
		self._histories: dict[str, deque[ChatMessage]] = defaultdict(
			lambda: deque(maxlen=self._max_messages)
		)
		self._lock = RLock()

	def get_history(self, conversation_id: str) -> list[ChatMessage]:
		with self._lock:
			return [dict(message) for message in self._histories[conversation_id]]

	def append_turn(
		self,
		conversation_id: str,
		user_message: str,
		assistant_message: str,
	) -> None:
		with self._lock:
			history = self._histories[conversation_id]
			history.append({"role": "user", "content": user_message})
			history.append({"role": "assistant", "content": assistant_message})

	def clear(self, conversation_id: str) -> None:
		with self._lock:
			self._histories.pop(conversation_id, None)


def copy_history(history: Sequence[ChatMessage]) -> list[ChatMessage]:
	"""Return a shallow, role/content-only copy suitable for graph state."""
	return [
		{"role": item["role"], "content": item["content"]}
		for item in history
		if item.get("role") in {"user", "assistant"}
	]
