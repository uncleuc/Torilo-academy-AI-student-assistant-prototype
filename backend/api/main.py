"""FastAPI application factory and Group 3 service wiring."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from backend.api.errors import register_error_handlers
from backend.api.health import router as health_router
from backend.api.routes import router as api_router
from backend.config import configure_logging, get_settings
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
	retriever = ingest_documents(
		repository_root / "knowledge_base",
		settings=get_settings(),
	)
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
	database_data_verified: bool | None = None,
	database_demo_mode: bool | None = None,
) -> FastAPI:
	"""Create an API with lazy production setup and injectable test services."""
	settings = get_settings()
	configure_logging(settings.log_level)
	provided_session_factory = session_factory
	provided_tools = database_tools
	provided_runner = assistant_runner
	verified_database = (
		settings.database_data_verified
		if database_data_verified is None
		else database_data_verified
	)
	demo_database_setting = (
		settings.database_demo_mode
		if database_demo_mode is None
		else database_demo_mode
	)
	demo_database = demo_database_setting and settings.environment == "development"

	@asynccontextmanager
	async def lifespan(app: FastAPI):
		engine = None
		active_session_factory = provided_session_factory
		if active_session_factory is None:
			engine = create_database_engine()
			active_session_factory = create_session_factory(engine)
		try:
			configured_tools = (
				provided_tools
				if provided_tools is not None
				else build_database_tools(active_session_factory)
			)
			active_tools = configured_tools if verified_database or demo_database else {}
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
		origins = list(settings.frontend_origins)
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
	frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
	if frontend_dist.is_dir():
		app.mount(
			"/",
			StaticFiles(directory=frontend_dist, html=True),
			name="frontend",
		)
	return app


app = create_app()
