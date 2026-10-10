"""Build and invoke the Group 2 LangGraph assistant."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.conversation import (
	load_conversation_history,
	normalize_message,
	resolve_conversation_id,
	save_conversation_turn,
)
from backend.agents.memory import ConversationMemory, InMemoryConversationMemory
from backend.agents.nodes import (
	DatabaseTool,
	RetrieverDependency,
	make_clarification_node,
	make_classifier_node,
	make_database_node,
	make_rag_fallback_node,
	make_rag_node,
	make_response_node,
	make_router_node,
	make_safety_node,
	make_safety_response_node,
	make_unavailable_node,
	make_unknown_node,
)
from backend.agents.state import AssistantState, validate_initial_state
from backend.ai.llm import create_chat_model
from backend.ai.response_generator import ChatModel

_assistant_graph: Any | None = None
_conversation_memory: ConversationMemory = InMemoryConversationMemory()


def build_assistant_graph(
	*,
	retriever: RetrieverDependency,
	database_tools: Mapping[str, DatabaseTool],
	llm: ChatModel,
) -> Any:
	"""Build a compiled graph with all external services supplied by the caller."""
	builder = StateGraph(AssistantState)
	builder.add_node("safety_check", make_safety_node())
	builder.add_node("classifier", make_classifier_node(llm))
	builder.add_node("router", make_router_node(database_tools))
	builder.add_node("rag", make_rag_node(retriever))
	builder.add_node("rag_fallback", make_rag_fallback_node(database_tools))
	builder.add_node("database", make_database_node(database_tools))
	builder.add_node("general", make_response_node(llm))
	builder.add_node("response", make_response_node(llm))
	builder.add_node("unknown", make_unknown_node())
	builder.add_node("clarify", make_clarification_node())
	builder.add_node("unavailable", make_unavailable_node())
	builder.add_node("safety_response", make_safety_response_node())

	builder.add_edge(START, "safety_check")
	builder.add_conditional_edges(
		"safety_check",
		lambda state: "SAFETY" if state.get("safety_blocked") else "CONTINUE",
		{"SAFETY": "safety_response", "CONTINUE": "classifier"},
	)
	builder.add_edge("classifier", "router")
	builder.add_conditional_edges(
		"router",
		lambda state: state["route"],
		{
			"SAFETY": "safety_response",
			"RAG": "rag",
			"DATABASE": "database",
			"GENERAL": "general",
			"CLARIFY": "clarify",
			"UNAVAILABLE": "unavailable",
			"UNKNOWN": "unknown",
		},
	)
	builder.add_edge("rag", "rag_fallback")
	builder.add_conditional_edges(
		"rag_fallback",
		lambda state: state.get("route", "RAG"),
		{
			"RAG": "response",
			"DATABASE": "database",
			"UNAVAILABLE": "unavailable",
		},
	)
	builder.add_edge("database", "response")
	builder.add_edge("response", END)
	builder.add_edge("general", END)
	builder.add_edge("unknown", END)
	builder.add_edge("clarify", END)
	builder.add_edge("unavailable", END)
	builder.add_edge("safety_response", END)
	return builder.compile()


def configure_assistant(
	*,
	retriever: RetrieverDependency,
	database_tools: Mapping[str, DatabaseTool],
	llm: ChatModel | None = None,
	memory: ConversationMemory | None = None,
) -> None:
	"""Configure process-level assistant services during application startup."""
	global _assistant_graph, _conversation_memory
	selected_llm = llm if llm is not None else create_chat_model()
	_assistant_graph = build_assistant_graph(
		retriever=retriever,
		database_tools=database_tools,
		llm=selected_llm,
	)
	if memory is not None:
		_conversation_memory = memory


def run_student_assistant(
	message: str,
	conversation_id: str | None = None,
) -> dict[str, Any]:
	"""Run one turn and return the stable API handoff shape.

	Application startup must call configure_assistant() once with Group 1's
	retriever, Group 3's authorized tools, and an initialized model. The
	conversation ID is generated when the caller does not supply one.
	 """
	if _assistant_graph is None:
		raise RuntimeError("Assistant services have not been configured")
	clean_message = normalize_message(message)
	active_id = resolve_conversation_id(conversation_id)
	history = load_conversation_history(_conversation_memory, active_id)
	input_state: AssistantState = {
		"message": clean_message,
		"conversation_id": active_id,
		"chat_history": history,
	}
	validate_initial_state(input_state)
	output = _assistant_graph.invoke(input_state)
	answer = output.get("answer")
	if not isinstance(answer, str) or not answer.strip():
		answer = "I don't have enough verified information to answer that question."
	sources = output.get("sources", [])
	if not isinstance(sources, list):
		sources = []
	save_conversation_turn(_conversation_memory, active_id, clean_message, answer)
	return {
		"answer": answer,
		"sources": sources,
		"conversation_id": active_id,
	}
