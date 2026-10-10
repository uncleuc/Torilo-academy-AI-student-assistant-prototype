"""Factory functions for the safety, retrieval, database, and answer nodes."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from backend.agents.classifier import (
	QueryClassification,
	classify_message,
	route_classification,
)
from backend.agents.router import (
	build_contextual_database_query,
	build_contextual_rag_query,
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
from backend.rag.query_expansion import expand_query_variants

logger = logging.getLogger(__name__)


class RetrieverLike(Protocol):
	def retrieve_documents(self, query: str) -> Mapping[str, Any]: ...


class RAGPipelineLike(Protocol):
	def search(self, query: str) -> Mapping[str, Any]: ...


RetrieverDependency = Callable[[str], Mapping[str, Any]] | RetrieverLike | RAGPipelineLike
DatabaseTool = Callable[..., Any]
_INSTRUCTOR_ASSIGNMENT = re.compile(
	r"\b(?:instructor|teacher)(?:\s+(?:for|of)\s+[^:\n]{1,80})?\s*(?:is|:|-)\s+"
	r"[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){1,2}\b"
)


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


def make_classifier_node(llm: ChatModel):
	def classifier_node(state: AssistantState) -> dict[str, Any]:
		classification = classify_message(
			llm,
			state["message"],
			state.get("chat_history", []),
		)
		return {"classification": classification.model_dump()}

	return classifier_node


def make_router_node(database_tools: Mapping[str, DatabaseTool] | None = None):
	def router_node(state: AssistantState) -> dict[str, Any]:
		history = state.get("chat_history", [])
		classification = QueryClassification.model_validate(state.get("classification", {}))
		route, tool_name = route_classification(
			classification,
			set(database_tools or {}),
		)
		entities = classification.entities
		course_query = entities.course or ""
		return {
			"route": route,
			"database_tool": tool_name,
			"clarification_question": classification.clarification_question or "",
			"retrieval_query": build_contextual_rag_query(state["message"], history),
			"database_query": (
				course_query
				if tool_name == "search_classes"
				else build_contextual_database_query(state["message"], history, tool_name)
			),
		}

	return router_node


def make_rag_node(retriever: RetrieverDependency):
	def rag_node(state: AssistantState) -> dict[str, Any]:
		try:
			original_query = state["message"]
			contextual_query = state.get("retrieval_query") or original_query
			query_variants = expand_query_variants(original_query, max_variants=2)
			if contextual_query.casefold() not in {item.casefold() for item in query_variants}:
				query_variants.append(contextual_query)
			combined_context: dict[tuple[str, str], Mapping[str, Any]] = {}
			combined_sources: dict[tuple[str, str], Mapping[str, Any]] = {}
			for variant in query_variants[:3]:
				result = _retrieve(retriever, variant)
				context = result.get("context", [])
				sources = result.get("sources", [])
				if not isinstance(context, list) or not isinstance(sources, list):
					raise TypeError("RAG result requires list context and sources")
				for item in context:
					if not isinstance(item, Mapping) or not isinstance(item.get("content"), str):
						continue
					metadata = item.get("metadata", {})
					if not isinstance(metadata, Mapping) or metadata.get("approved", True) is not True:
						continue
					identity = (
						str(metadata.get("document", "")),
						item["content"],
					)
					existing = combined_context.get(identity)
					if existing is None or _evidence_score(item) > _evidence_score(existing):
						combined_context[identity] = item
				for source in sources:
					if not isinstance(source, Mapping) or source.get("approved", True) is not True:
						continue
					normalized_source = {
						**source,
						"document": source.get("document") or source.get("source", ""),
						"title": source.get("title") or source.get("document_type", ""),
					}
					identity = (
						str(normalized_source["document"]),
						str(normalized_source["title"]),
					)
					combined_sources[identity] = normalized_source
			approved_context = sorted(
				combined_context.values(), key=_evidence_score, reverse=True
			)[:8]
			approved_source_ids = {
				(str(item.get("metadata", {}).get("document", "")), str(item.get("metadata", {}).get("title", "")))
				for item in approved_context
				if isinstance(item.get("metadata"), Mapping)
			}
			sources = [
				source
				for identity, source in combined_sources.items()
				if identity in approved_source_ids
			]
			return {
				"retrieved_documents": approved_context,
				"sources": sources,
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


def make_rag_fallback_node(database_tools: Mapping[str, DatabaseTool]):
	"""Use the instructor database only when approved KB text has no assignment."""
	def rag_fallback_node(state: AssistantState) -> dict[str, Any]:
		classification = QueryClassification.model_validate(state.get("classification", {}))
		if classification.intent != "course_instructor":
			return {}

		course_name = classification.entities.course or ""
		for item in state.get("retrieved_documents", []):
			content = item.get("content", "")
			metadata = item.get("metadata", {})
			if (
				isinstance(content, str)
				and isinstance(metadata, Mapping)
				and metadata.get("approved", True) is True
				and course_name.casefold() in content.casefold()
				and _INSTRUCTOR_ASSIGNMENT.search(content)
			):
				return {}

		if "search_courses" in database_tools and "get_course_instructor" in database_tools:
			return {
				"route": "DATABASE",
				"database_tool": "get_course_instructor",
				"database_query": course_name,
			}
		return {"route": "UNAVAILABLE"}

	return rag_fallback_node


def _evidence_score(item: Mapping[str, Any]) -> float:
	score = item.get("score")
	return float(score) if isinstance(score, (int, float)) else 0.0


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
			elif tool_name in {"search_courses", "search_classes"}:
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


def make_clarification_node():
	def clarification_node(state: AssistantState) -> dict[str, Any]:
		question = state.get("clarification_question", "").strip()
		return {
			"answer": question or "Could you clarify what information you need?",
			"sources": [],
		}

	return clarification_node


def make_unavailable_node():
	def unavailable_node(state: AssistantState) -> dict[str, Any]:
		return {
			"answer": (
				"I can't verify current or account-specific information from an authorized live record. "
				"Please contact Student Support at student-support@torilo.ng or +234 701 570 8674."
			),
			"sources": [],
		}

	return unavailable_node


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
			return {
				"answer": (
					"I couldn't verify a current matching class or instructor record. "
					"Please contact Student Support at student-support@torilo.ng or +234 701 570 8674."
				),
				"sources": [],
			}

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
