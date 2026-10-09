from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from backend.agents.graph import build_assistant_graph
from backend.agents.router import (
	build_contextual_database_query,
	build_contextual_rag_query,
	extract_course_search_query,
	route_message,
)
from backend.agents.safety import SAFETY_RESPONSE, inspect_user_message
from backend.ai.grounding import UNKNOWN_RESPONSE

ROOT = Path(__file__).resolve().parents[1]
TEST_DATA = ROOT / "tests"


def load_cases(filename: str) -> list[dict[str, Any]]:
	value = json.loads((TEST_DATA / filename).read_text(encoding="utf-8"))
	assert isinstance(value, list)
	return value


def load_approved_registry() -> dict[str, dict[str, Any]]:
	entries = json.loads((ROOT / "knowledge_base" / "index.json").read_text(encoding="utf-8"))
	return {entry["document"]: entry for entry in entries if entry.get("approved") is True}


class RecordingModel:
	def __init__(self) -> None:
		self.calls: list[Any] = []

	def invoke(self, messages: list[Any]) -> Any:
		self.calls.append(messages)
		return type("ModelResponse", (), {"content": "Answer based on supplied approved test evidence."})()


class RecordingRetriever:
	def __init__(self, source: str) -> None:
		self.calls: list[str] = []
		self.source = source

	def retrieve_documents(self, query: str) -> dict[str, list[Any]]:
		self.calls.append(query)
		registry_entry = load_approved_registry()[self.source]
		content = (ROOT / "knowledge_base" / self.source).read_text(encoding="utf-8")
		metadata = {
			"document": self.source,
			"title": registry_entry["title"],
			"source_type": registry_entry["source_type"],
			"approved": True,
		}
		return {
			"context": [{"content": content, "metadata": metadata}],
			"sources": [metadata],
		}


@pytest.fixture(scope="module")
def approved_registry() -> dict[str, dict[str, Any]]:
	return load_approved_registry()


def test_scenario_catalog_ids_are_unique_and_questions_are_present():
	for filename in (
		"rag_questions.json",
		"database_questions.json",
		"conversation_tests.json",
		"injection_tests.json",
		"unknown_questions.json",
	):
		cases = load_cases(filename)
		assert cases, f"{filename} must contain roadmap scenarios"
		assert len({case["id"] for case in cases}) == len(cases)
		assert all(case.get("question") or case.get("messages") for case in cases)


@pytest.mark.parametrize("case", load_cases("rag_questions.json"), ids=lambda case: case["id"])
def test_rag_catalog_cases_route_to_approved_source(case, approved_registry):
	route, tool = route_message(case["question"])
	assert (route, tool) == (case["expected_route"], None)

	source = case["expected_source"]
	assert source in approved_registry
	assert (ROOT / "knowledge_base" / source).is_file()

	model = RecordingModel()
	retriever = RecordingRetriever(source)
	graph = build_assistant_graph(retriever=retriever, database_tools={}, llm=model)
	result = graph.invoke(
		{"message": case["question"], "conversation_id": "scenario", "chat_history": []}
	)

	assert result["answer"] == "Answer based on supplied approved test evidence."
	assert any(item["document"] == source for item in result["sources"])
	assert retriever.calls == [case["question"]]
	assert len(model.calls) == 1


@pytest.mark.parametrize("case", load_cases("database_questions.json"), ids=lambda case: case["id"])
def test_database_catalog_cases_select_expected_tool_and_query(case):
	route, tool = route_message(case["question"])
	assert route == case["expected_route"]
	assert tool == case["expected_tool"]

	if expected_query := case.get("expected_search_query"):
		assert extract_course_search_query(case["question"], tool) == expected_query

	model = RecordingModel()
	retriever = RecordingRetriever("courses/courses_catalog.md")
	calls: list[tuple[str, str | None]] = []

	def selected_tool(argument=None):
		calls.append((tool, argument))
		if tool in {"get_course_instructor", "get_course_details"}:
			return {"course_id": "1", "course_name": "Synthetic Python", "instructor_name": "Test Instructor"}
		if tool == "search_courses":
			return [{"course_id": "1", "course_name": "Synthetic Python"}]
		return [{"course_id": "1", "course_name": "Synthetic Python"}]

	tools = {tool: selected_tool}
	if tool in {"get_course_instructor", "get_course_details"}:
		tools["search_courses"] = lambda query: (
			calls.append(("search_courses", query))
			or [{"course_id": "1", "course_name": "Synthetic Python"}]
		)
	graph = build_assistant_graph(retriever=retriever, database_tools=tools, llm=model)
	result = graph.invoke(
		{"message": case["question"], "conversation_id": "scenario", "chat_history": []}
	)

	assert result["answer"] == "Answer based on supplied approved test evidence."
	assert result["sources"] == []
	assert retriever.calls == []
	assert len(model.calls) == 1
	assert any(call[0] == tool for call in calls)
	if expected_query := case.get("expected_search_query"):
		assert ("search_courses", expected_query) in calls


@pytest.mark.parametrize("case", load_cases("conversation_tests.json"), ids=lambda case: case["id"])
def test_conversation_catalog_cases_reuse_route_and_context(case):
	messages = case["messages"]
	first_route, first_tool = route_message(messages[0])
	second_route, second_tool = route_message(
		messages[1],
		[
			{"role": "user", "content": messages[0]},
			{"role": "assistant", "content": "Prior answer is context, not evidence."},
		],
	)
	assert [first_route, second_route] == case["expected_routes"]

	if first_route == "RAG":
		history = [{"role": "user", "content": messages[0]}]
		assert build_contextual_rag_query(messages[1], history) == case["expected_retrieval_query"]
		assert case["expected_source"] in load_approved_registry()
	else:
		assert [first_tool, second_tool] == case["expected_tools"]
		query = build_contextual_database_query(
			messages[1],
			[{"role": "user", "content": messages[0]}],
			second_tool,
		)
		assert query == case["expected_search_query"]


@pytest.mark.parametrize("case", load_cases("injection_tests.json"), ids=lambda case: case["id"])
def test_injection_catalog_cases_block_all_graph_services(case):
	model = RecordingModel()
	retriever = RecordingRetriever("policies/attendance_and_participation.md")
	database_calls: list[str] = []
	tools = {"get_available_courses": lambda: database_calls.append("called")}
	graph = build_assistant_graph(retriever=retriever, database_tools=tools, llm=model)
	result = graph.invoke(
		{"message": case["question"], "conversation_id": "scenario", "chat_history": []}
	)

	assert inspect_user_message(case["question"]).blocked is case["expected_blocked"]
	assert result["answer"] == SAFETY_RESPONSE
	assert result["sources"] == []
	assert len(retriever.calls) + len(database_calls) + len(model.calls) == case["expected_service_calls"]


@pytest.mark.parametrize("case", load_cases("unknown_questions.json"), ids=lambda case: case["id"])
def test_unknown_catalog_cases_return_fixed_no_evidence_result(case):
	model = RecordingModel()
	retriever = RecordingRetriever("policies/attendance_and_participation.md")
	database_calls: list[str] = []
	graph = build_assistant_graph(
		retriever=retriever,
		database_tools={"get_available_courses": lambda: database_calls.append("called")},
		llm=model,
	)
	result = graph.invoke(
		{"message": case["question"], "conversation_id": "scenario", "chat_history": []}
	)

	assert route_message(case["question"]) == (case["expected_route"], None)
	assert result["answer"] == UNKNOWN_RESPONSE
	assert result["sources"] == case["expected_sources"]
	assert len(model.calls) == case["expected_llm_calls"]
	assert retriever.calls == []
	assert database_calls == []