"""FastAPI dependency accessors for injected application services."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import Any, Protocol

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker


class AssistantRunner(Protocol):
	"""The Group 2 assistant interface consumed by the chat API."""

	def __call__(
		self,
		message: str,
		conversation_id: str | None = None,
	) -> Mapping[str, Any]: ...


def get_assistant_runner(request: Request) -> AssistantRunner:
	runner = getattr(request.app.state, "assistant_runner", None)
	if runner is None:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Assistant service is unavailable",
		)
	return runner


def get_database_tools(request: Request) -> Mapping[str, Callable[..., Any]]:
	tools = getattr(request.app.state, "database_tools", None)
	if tools is None:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Database tools are unavailable",
		)
	return tools


def get_session_factory(request: Request) -> sessionmaker[Session]:
	factory = getattr(request.app.state, "session_factory", None)
	if factory is None:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Database is unavailable",
		)
	return factory


def get_db_session(request: Request) -> Iterator[Session]:
	session = get_session_factory(request)()
	try:
		yield session
	finally:
		session.close()