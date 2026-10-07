"""Factory functions for the safety, retrieval, database, and answer nodes."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from backend.agents.router import (
	build_contextual_database_query,
	build_contextual_rag_query,
	route_message,
)
from backend.agents.safety import inspect_user_message, safe_response
from backend.agents.state import AssistantState, Route
from backend.ai.grounding import (
	UNKNOWN_RESPONSE,
	has_approved_rag_evidence,
	has_database_evidence,
)
from backend.ai.response_generator import ChatModel, generate_grounded_answer
from backend.ai.source_formatter import format_sources

logger = logging.getLogger(__name__)


class RetrieverLike(Protocol):
	def retrieve_documents(self, query: str) -> Mapping[str, Any]: ...


class RAGPipelineLike(Protocol):
	def search(self, query: str) -> Mapping[str, Any]: ...


RetrieverDependency = Callable[[str], Mapping[str, Any]] | RetrieverLike | RAGPipelineLike
DatabaseTool = Callable[..., Any]


def resolve_unique_course_id(search_results: Any) -> str | None:
	"""Accept an ID only from exactly one well-formed Group 3 search result."""
	if not isinstance(search_results, list) or len(search_results) != 1:
		return None
	record = search_results[0]
	if not isinstance(record, Mapping):
		return None
	course_id = record.get("course_id")
	if not isinstance(course_id, str):
		return None
	normalized = course_id.strip()
	return normalized or None


def _retrieve(retriever: RetrieverDependency, query: str) -> Mapping[str, Any]:
	if callable(retriever):
		result = retriever(query)
	elif hasattr(retriever, "retrieve_documents"):
		result = retriever.retrieve_documents(query)
	elif hasattr(retriever, "search"):
		result = retriever.search(query)
	else:
		raise TypeError("RAG service must be callable or expose retrieve_documents/search")
	if not isinstance(result, Mapping):
		raise TypeError("RAG retriever must return a mapping")
	if isinstance(result.get("context"), str):
		chunks = result.get("results", [])
		if isinstance(chunks, list) and chunks:
			context = [
				{
					"content": chunk.get("content", ""),
					"metadata": {
						"document": chunk.get("source"),
						"title": chunk.get("document_type") or chunk.get("document_id"),
						"source_type": chunk.get("source_type"),
					},
					"score": chunk.get("retrieval_score", chunk.get("similarity")),
				}
				for chunk in chunks
				if isinstance(chunk, Mapping) and isinstance(chunk.get("content"), str)
			]
		else:
			context = [{"content": result["context"], "metadata": {}}] if result["context"].strip() else []
		return {"context": context, "sources": result.get("sources", [])}
	return result


def make_safety_node():
	def safety_node(state: AssistantState) -> dict[str, Any]:
		decision = inspect_user_message(state["message"])
		return {
			"safety_blocked": decision.blocked,
			"safety_reason": decision.reason or "",
			"route": "SAFETY" if decision.blocked else "UNKNOWN",
		}

	return safety_node


def make_router_node():
	def router_node(state: AssistantState) -> dict[str, Any]:
		history = state.get("chat_history", [])
		route, tool_name = route_message(state["message"], history)
		return {
			"route": route,
			"database_tool": tool_name,
			"retrieval_query": build_contextual_rag_query(state["message"], history),
			"database_query": build_contextual_database_query(
				state["message"], history, tool_name
			),
		}

	return router_node


def make_rag_node(retriever: RetrieverDependency):
	def rag_node(state: AssistantState) -> dict[str, Any]:
		try:
			result = _retrieve(retriever, state.get("retrieval_query") or state["message"])
			context = result.get("context", [])
			sources = result.get("sources", [])
			if not isinstance(context, list) or not isinstance(sources, list):
				raise TypeError("RAG result requires list context and sources")
			approved_context = []
			for item in context:
				if not isinstance(item, Mapping) or not isinstance(item.get("content"), str):
					continue
				metadata = item.get("metadata", {})
				if isinstance(metadata, Mapping) and metadata.get("approved", True) is True:
					approved_context.append(item)
			return {
				"retrieved_documents": approved_context,
				"sources": list(sources),
				"retrieval_error": False,
			}
		except Exception:  # noqa: BLE001 - injected retrievers may raise provider-specific errors.
			logger.error("rag_retrieval_failed")
			return {
				"retrieved_documents": [],
				"sources": [],
				"retrieval_error": True,
			}

	return rag_node


def make_database_node(database_tools: Mapping[str, DatabaseTool]):
	def database_node(state: AssistantState) -> dict[str, Any]:
		tool_name = state.get("database_tool")
		tool = database_tools.get(tool_name or "")
		if tool is None:
			return {
				"database_results": None,
				"database_error": True,
			}
		try:
			if tool_name == "get_available_courses" or tool_name == "get_active_classes":
				results = tool()
			elif tool_name == "search_courses":
				results = tool(state.get("database_query") or state["message"])
			elif tool_name in {"get_course_details", "get_course_instructor"}:
				search_tool = database_tools.get("search_courses")
				if search_tool is None:
					return {"database_results": None, "database_error": True}
				query = state.get("database_query") or state["message"]
				matches = search_tool(query)
				course_id = resolve_unique_course_id(matches)
				if course_id is None:
					return {"database_results": None, "database_error": False}
				results = tool(course_id)
			else:
				return {"database_results": None, "database_error": True}
			return {"database_results": results, "database_error": False}
		except Exception:  # noqa: BLE001 - injected tools may raise provider-specific errors.
			logger.error("database_tool_failed tool=%s", tool_name)
			return {"database_results": None, "database_error": True}

	return database_node


def make_unknown_node():
	def unknown_node(state: AssistantState) -> dict[str, Any]:
		return {
			"answer": UNKNOWN_RESPONSE,
			"sources": [],
		}

	return unknown_node


def make_safety_response_node():
	def safety_response_node(state: AssistantState) -> dict[str, Any]:
		return {"answer": safe_response(), "sources": []}

	return safety_response_node


def make_response_node(llm: ChatModel):
	def response_node(state: AssistantState) -> dict[str, Any]:
		route: Route = state["route"]
		context = state.get("retrieved_documents", [])
		database_results = state.get("database_results")

		if route == "RAG" and not has_approved_rag_evidence(context):
			return {"answer": UNKNOWN_RESPONSE, "sources": []}
		if route == "DATABASE" and not has_database_evidence(database_results):
			return {"answer": UNKNOWN_RESPONSE, "sources": []}

		answer = generate_grounded_answer(
			llm=llm,
			route=route,
			question=state["message"],
			history=state.get("chat_history", []),
			context=context,
			database_results=database_results,
		)
		if answer == UNKNOWN_RESPONSE:
			return {"answer": answer, "sources": []}
		if route == "RAG":
			public_sources = format_sources(state.get("sources", []))
		else:
			public_sources = []
		return {"answer": answer, "sources": public_sources}

	return response_node
