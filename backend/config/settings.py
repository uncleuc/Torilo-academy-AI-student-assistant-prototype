"""Typed, centralized application settings loaded from environment/.env."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
	"""Runtime configuration; secret values are deliberately hidden from repr."""

	environment: str = "development"
	log_level: str = "INFO"
	backend_host: str = "0.0.0.0"
	backend_port: int = 8000
	frontend_origins: tuple[str, ...] = ("http://localhost:5173",)
	database_url: str | None = field(default=None, repr=False)
	llm_model: str | None = None
	openai_api_key: str | None = field(default=None, repr=False)
	embedding_model: str | None = None
	chroma_persist_directory: Path = REPOSITORY_ROOT / "chroma_db"
	chroma_collection_name: str = "torilo_knowledge_base"
	vector_store_url: str | None = None
	vector_store_api_key: str | None = field(default=None, repr=False)

	@classmethod
	def from_env(
		cls,
		environ: Mapping[str, str] | None = None,
		*,
		repository_root: Path = REPOSITORY_ROOT,
	) -> Settings:
		"""Build and validate settings from a supplied mapping or process env."""
		values = os.environ if environ is None else environ
		port_text = values.get("BACKEND_PORT", "8000")
		try:
			port = int(port_text)
		except (TypeError, ValueError) as exc:
			raise ValueError("BACKEND_PORT must be an integer") from exc
		if not 1 <= port <= 65535:
			raise ValueError("BACKEND_PORT must be between 1 and 65535")

		log_level = values.get("LOG_LEVEL", "INFO").strip().upper()
		if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
			raise ValueError("LOG_LEVEL must be a supported logging level")

		origins = tuple(
			origin.strip().rstrip("/")
			for origin in values.get(
				"FRONTEND_URL",
				"http://localhost:5173,https://ai.softshell-diminished.ts.net,https://torilo.net,https://www.torilo.net",
			).split(",")
			if origin.strip()
		)
		chroma_path = Path(values.get("CHROMA_PERSIST_DIRECTORY", "chroma_db"))
		if not chroma_path.is_absolute():
			chroma_path = repository_root / chroma_path

		return cls(
			environment=values.get("ENVIRONMENT", "development").strip(),
			log_level=log_level,
			backend_host=values.get("BACKEND_HOST", "0.0.0.0").strip(),
			backend_port=port,
			frontend_origins=origins,
			database_url=values.get("DATABASE_URL") or None,
			llm_model=values.get("LLM_MODEL") or None,
			openai_api_key=values.get("OPENAI_API_KEY") or None,
			embedding_model=values.get("EMBEDDING_MODEL") or None,
			chroma_persist_directory=chroma_path.resolve(),
			chroma_collection_name=values.get(
				"CHROMA_COLLECTION_NAME", "torilo_knowledge_base"
			).strip(),
			vector_store_url=values.get("VECTOR_STORE_URL") or None,
			vector_store_api_key=values.get("VECTOR_STORE_API_KEY") or None,
		)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""Load repository-root .env once, then return the process settings."""
	load_dotenv(REPOSITORY_ROOT / ".env", override=False)
	return Settings.from_env()