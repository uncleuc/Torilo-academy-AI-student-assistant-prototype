"""Generate student-facing text from route-specific evidence."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import ChatMessage, Route
from backend.ai.grounding import UNKNOWN_RESPONSE, answer_is_usable
from backend.ai.prompts import (
	DATABASE_PROMPT,
	GENERAL_PROMPT,
	RAG_PROMPT,
	SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class ChatModel(Protocol):
	def invoke(self, messages: Sequence[Any]) -> Any: ...


def _json_for_prompt(value: Any) -> str:
	return json.dumps(value, ensure_ascii=False, default=str)


def _message_text(result: Any) -> str:
	content = getattr(result, "content", result)
	if isinstance(content, str):
		return content.strip()
	if isinstance(content, list):
		parts = [part.get("text", "") for part in content if isinstance(part, dict)]
		return "".join(parts).strip()
	return str(content).strip()


def _history_for_prompt(history: Sequence[ChatMessage]) -> list[dict[str, str]]:
	return [
		{"role": item["role"], "content": item["content"]}
		for item in history[-12:]
		if item.get("role") in {"user", "assistant"}
	]


def generate_grounded_answer(
	*,
	llm: ChatModel,
	route: Route,
	question: str,
	history: Sequence[ChatMessage],
	context: Sequence[Mapping[str, Any]] = (),
	database_results: Any = None,
) -> str:
	"""Invoke the model with only the evidence appropriate to the selected route."""
	history_json = _json_for_prompt(_history_for_prompt(history))
	if route == "RAG":
		route_prompt = RAG_PROMPT.format(
			history_json=history_json,
			context_json=_json_for_prompt(list(context)),
			question=question,
		)
	elif route == "DATABASE":
		route_prompt = DATABASE_PROMPT.format(
			history_json=history_json,
			database_json=_json_for_prompt(database_results),
			question=question,
		)
	elif route == "GENERAL":
		route_prompt = GENERAL_PROMPT.format(question=question)
	else:
		return UNKNOWN_RESPONSE

	try:
		result = llm.invoke(
			[
				SystemMessage(content=SYSTEM_PROMPT),
				HumanMessage(content=route_prompt),
			]
		)
	except Exception:  # noqa: BLE001 - LLM providers expose different exception hierarchies.
		# Do not log exception strings or tracebacks: provider errors can include request data.
		logger.error("llm_response_generation_failed")
		return UNKNOWN_RESPONSE

	answer = _message_text(result)
	return answer if answer_is_usable(answer) else UNKNOWN_RESPONSE
