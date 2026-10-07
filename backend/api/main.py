"""FastAPI application factory and Group 3 service wiring."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker

from backend.api.errors import register_error_handlers
from backend.api.health import router as health_router
from backend.api.routes import router as api_router
from backend.database.database import create_database_engine, create_session_factory
from backend.tools import build_database_tools

AssistantRunnerFactory = Callable[..., Mapping[str, Any]]
AssistantInitializer = Callable[
	[sessionmaker[Session], Mapping[str, Callable[..., Any]]], None
]


def initialize_group_services(
	session_factory: sessionmaker[Session],
	database_tools: Mapping[str, Callable[..., Any]],
) -> None:
	"""Wire Group 1 retrieval and Group 3 tools into the Group 2 assistant."""
	from backend.agents.graph import configure_assistant
	from backend.ai.llm import create_chat_model
	from backend.rag.ingestion import ingest_documents

	repository_root = Path(__file__).resolve().parents[2]
	retriever = ingest_documents(repository_root / "knowledge_base")
	configure_assistant(
		retriever=retriever,
		database_tools=database_tools,
		llm=create_chat_model(),
	)


def _load_assistant_runner() -> AssistantRunnerFactory:
	from backend.agents.graph import run_student_assistant

	return run_student_assistant


def create_app(
	*,
	assistant_runner: AssistantRunnerFactory | None = None,
	database_tools: Mapping[str, Callable[..., Any]] | None = None,
	session_factory: sessionmaker[Session] | None = None,
	assistant_initializer: AssistantInitializer | None = None,
	allowed_origins: list[str] | None = None,
) -> FastAPI:
	"""Create an API with lazy production setup and injectable test services."""
	repository_root = Path(__file__).resolve().parents[2]
	load_dotenv(repository_root / ".env", override=False)
	provided_session_factory = session_factory
	provided_tools = database_tools
	provided_runner = assistant_runner

	@asynccontextmanager
	async def lifespan(app: FastAPI):
		engine = None
		active_session_factory = provided_session_factory
		if active_session_factory is None:
			engine = create_database_engine()
			active_session_factory = create_session_factory(engine)
		try:
			active_tools = (
				provided_tools
				if provided_tools is not None
				else build_database_tools(active_session_factory)
			)
			active_runner = provided_runner
			initializer = assistant_initializer
			if active_runner is None:
				(initializer or initialize_group_services)(active_session_factory, active_tools)
				active_runner = _load_assistant_runner()
			app.state.assistant_runner = active_runner
			app.state.database_tools = active_tools
			app.state.session_factory = active_session_factory
			app.state.engine = engine
			yield
		finally:
			if engine is not None:
				engine.dispose()

	app = FastAPI(
		title="Torilo Academy AI Student Assistant API",
		version="0.1.0",
		lifespan=lifespan,
	)
	origins = allowed_origins
	if origins is None:
		origins = [
			origin.strip()
			for origin in os.getenv("FRONTEND_URL", "").split(",")
			if origin.strip()
		]
	if origins:
		app.add_middleware(
			CORSMiddleware,
			allow_origins=origins,
			allow_credentials=False,
			allow_methods=["GET", "POST"],
			allow_headers=["Content-Type", "Authorization"],
		)
	app.include_router(health_router)
	app.include_router(api_router)
	register_error_handlers(app)
	return app


app = create_app()