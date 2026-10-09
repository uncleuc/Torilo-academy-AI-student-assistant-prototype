"""SQLAlchemy engine and session-factory construction."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings


class DatabaseConfigurationError(RuntimeError):
	"""Raised when required database configuration is unavailable."""


def create_database_engine(database_url: str | None = None) -> Engine:
	"""Create an engine without connecting until the first database operation."""
	url = database_url or get_settings().database_url
	if not url:
		raise DatabaseConfigurationError("DATABASE_URL is required")
	if url.startswith("postgres://"):
		url = "postgresql+psycopg://" + url.removeprefix("postgres://")
	elif url.startswith("postgresql://"):
		url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
	return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
	"""Create non-autocommit, non-autoflush sessions bound to this engine."""
	return sessionmaker(
		bind=engine,
		class_=Session,
		autoflush=False,
		expire_on_commit=False,
	)


def get_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
	"""Yield one session and always close it."""
	session = session_factory()
	try:
		yield session
	finally:
		session.close()