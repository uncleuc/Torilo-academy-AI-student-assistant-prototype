"""Validated HTTP request and response schemas for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
	model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

	message: str = Field(min_length=1, max_length=8_000)
	conversation_id: str | None = Field(default=None, max_length=128)

	@field_validator("conversation_id")
	@classmethod
	def empty_conversation_id_becomes_none(cls, value: str | None) -> str | None:
		return value or None


class Source(BaseModel):
	"""Document citation shape while preserving Group 1/2 extension fields."""

	model_config = ConfigDict(extra="allow")

	document: str | None = None
	title: str | None = None
	section: str | None = None
	page: int | None = None
	source_type: str | None = None


class ChatResponse(BaseModel):
	model_config = ConfigDict(extra="forbid")

	answer: str = Field(min_length=1)
	sources: list[dict[str, Any]] = Field(default_factory=list)
	conversation_id: str = Field(min_length=1, max_length=128)


class HealthResponse(BaseModel):
	status: str
	database: str


class ErrorResponse(BaseModel):
	detail: str


class CourseResponse(BaseModel):
	course_id: str
	course_name: str
	description: str
	level: str
	duration_weeks: int
	instructor_name: str | None = None