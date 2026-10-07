"""HTTP endpoints for chat and public course catalogue reads."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
	AssistantRunner,
	get_assistant_runner,
	get_database_tools,
)
from backend.api.schemas import ChatRequest, ChatResponse, CourseResponse

router = APIRouter(prefix="/api", tags=["assistant"])

@router.post("/chat", response_model=ChatResponse)
def chat(
	payload: ChatRequest,
	assistant_runner: Annotated[AssistantRunner, Depends(get_assistant_runner)],
) -> ChatResponse:
	try:
		result = assistant_runner(payload.message, payload.conversation_id)
	except (ValueError, TypeError) as exc:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail="The chat request could not be processed",
		) from exc
	except RuntimeError as exc:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Assistant service is unavailable",
		) from exc

	if not isinstance(result, Mapping):
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail="Assistant returned an invalid response",
		)
	answer = result.get("answer")
	sources = result.get("sources", [])
	conversation_id = result.get("conversation_id")
	if (
		not isinstance(answer, str)
		or not answer.strip()
		or not isinstance(sources, list)
		or any(not isinstance(source, dict) for source in sources)
		or not isinstance(conversation_id, str)
		or not conversation_id.strip()
		or len(conversation_id) > 128
	):
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail="Assistant returned an invalid response",
		)
	return ChatResponse(
		answer=answer,
		sources=sources,
		conversation_id=conversation_id,
	)


@router.get("/courses", response_model=list[CourseResponse])
def list_courses(
	database_tools: Annotated[
		Mapping[str, Callable[..., Any]], Depends(get_database_tools)
	],
) -> list[CourseResponse]:
	tool = database_tools.get("get_available_courses")
	if tool is None:
		raise HTTPException(status_code=503, detail="Course service is unavailable")
	records = tool()
	if not isinstance(records, list):
		raise HTTPException(status_code=502, detail="Course service returned invalid data")
	try:
		return [CourseResponse.model_validate(record) for record in records]
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Course service returned invalid data") from exc


@router.get("/courses/{course_id}", response_model=CourseResponse)
def course_details(
	course_id: str,
	database_tools: Annotated[
		Mapping[str, Callable[..., Any]], Depends(get_database_tools)
	],
) -> CourseResponse:
	tool = database_tools.get("get_course_details")
	if tool is None:
		raise HTTPException(status_code=503, detail="Course service is unavailable")
	record = tool(course_id)
	if record is None:
		raise HTTPException(status_code=404, detail="Course not found")
	try:
		return CourseResponse.model_validate(record)
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Course service returned invalid data") from exc