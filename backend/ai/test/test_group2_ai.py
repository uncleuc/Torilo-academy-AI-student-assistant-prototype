"""Offline tests for Group 2 grounding and source formatting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from backend.ai.grounding import (
	UNKNOWN_RESPONSE,
	answer_is_usable,
	has_approved_rag_evidence,
	has_database_evidence,
)
from backend.ai.response_generator import generate_grounded_answer
from backend.ai.source_formatter import format_sources


@dataclass
class FakeAIMessage:
	content: str


class RecordingModel:
	def __init__(self, result: Any = "The supplied evidence supports this.") -> None:
		self.result = result
		self.calls: list[Any] = []

	def invoke(self, messages):
		self.calls.append(messages)
		return self.result


def test_approved_rag_evidence_requires_nonempty_text() -> None:
	assert has_approved_rag_evidence(
		[{"content": "excerpt", "metadata": {"approved": True}}]
	)
	assert not has_approved_rag_evidence(
		[{"content": "  ", "metadata": {"approved": True}}]
	)
	assert not has_approved_rag_evidence(
		[{"content": "excerpt", "metadata": {"approved": False}}]
	)


@pytest.mark.parametrize("results", [None, [], {}, ""])
def test_empty_database_values_are_not_evidence(results: Any) -> None:
	assert not has_database_evidence(results)


def test_nonempty_database_records_are_evidence() -> None:
	assert has_database_evidence([{"course_name": "Synthetic course"}])


def test_sources_drop_internal_and_unapproved_fields() -> None:
	formatted = format_sources(
		[
			{
				"document": "test/source.pdf",
				"title": "Synthetic source",
				"page": 2,
				"approved": True,
				"score": 0.97,
				"embedding": [0.1, 0.2],
				"content": "private chunk text",
			},
			{
				"document": "not-approved.pdf",
				"title": "Unapproved source",
				"approved": False,
			},
		]
	)
	assert formatted == [
		{
			"document": "test/source.pdf",
			"title": "Synthetic source",
			"page": 2,
		}
	]


def test_sources_reject_unapproved_nested_metadata() -> None:
	assert format_sources(
		[
			{
				"metadata": {
					"document": "unapproved.pdf",
					"title": "Unapproved",
					"approved": False,
				}
			}
		]
	) == []


def test_sources_accept_nested_approved_metadata_without_leaking_flag() -> None:
	assert format_sources(
		[
			{
				"metadata": {
					"document": "approved.pdf",
					"title": "Approved test source",
					"approved": True,
				}
			}
		]
	) == [{"document": "approved.pdf", "title": "Approved test source"}]


def test_response_generator_uses_route_evidence_and_returns_text() -> None:
	model = RecordingModel(FakeAIMessage("Supported test response."))
	answer = generate_grounded_answer(
		llm=model,
		route="RAG",
		question="Test question",
		history=[],
		context=[
			{
				"content": "Synthetic excerpt",
				"metadata": {"approved": True},
			}
		],
	)
	assert answer == "Supported test response."
	assert len(model.calls) == 1


def test_unknown_route_does_not_invoke_model() -> None:
	model = RecordingModel()
	answer = generate_grounded_answer(
		llm=model,
		route="UNKNOWN",
		question="Unsupported academy question",
		history=[],
	)
	assert answer == UNKNOWN_RESPONSE
	assert model.calls == []


def test_blank_model_response_is_not_usable() -> None:
	model = RecordingModel(FakeAIMessage("   "))
	answer = generate_grounded_answer(
		llm=model,
		route="GENERAL",
		question="Hello",
		history=[],
	)
	assert answer == UNKNOWN_RESPONSE
	assert not answer_is_usable("  ")


def test_model_exception_is_not_leaked_to_response_or_logs(caplog) -> None:
	class BrokenModel(RecordingModel):
		def invoke(self, messages):
			raise RuntimeError("provider-secret-sentinel")

	answer = generate_grounded_answer(
		llm=BrokenModel(),
		route="GENERAL",
		question="Hello",
		history=[],
	)

	assert answer == UNKNOWN_RESPONSE
	assert "provider-secret-sentinel" not in answer
	assert "provider-secret-sentinel" not in caplog.text
