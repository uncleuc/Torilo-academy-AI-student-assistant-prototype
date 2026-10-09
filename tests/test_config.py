from __future__ import annotations

import logging
from pathlib import Path

import pytest

from backend.config import Settings, configure_logging


def test_settings_parse_origins_paths_and_hide_secrets(tmp_path: Path):
	settings = Settings.from_env(
		{
			"BACKEND_HOST": "127.0.0.1",
			"BACKEND_PORT": "8012",
			"FRONTEND_URL": "http://localhost:5173/, http://localhost:4173",
			"DATABASE_URL": "postgresql://user:secret@localhost/test_db",
			"OPENAI_API_KEY": "test-api-key",
			"LLM_MODEL": "test-chat-model",
			"EMBEDDING_MODEL": "text-embedding-3-small",
			"CHROMA_PERSIST_DIRECTORY": "test-data/chroma",
			"CHROMA_COLLECTION_NAME": "test-collection",
		},
		repository_root=tmp_path,
	)

	assert settings.backend_port == 8012
	assert settings.frontend_origins == (
		"http://localhost:5173",
		"http://localhost:4173",
	)
	assert settings.chroma_persist_directory == (tmp_path / "test-data/chroma").resolve()
	assert settings.chroma_collection_name == "test-collection"
	assert settings.embedding_model == "text-embedding-3-small"
	assert "secret" not in repr(settings)
	assert "test-api-key" not in repr(settings)


def test_default_frontend_origins_include_configured_public_hosts():
	settings = Settings.from_env({})
	assert settings.frontend_origins == (
		"http://localhost:5173",
		"https://ai.softshell-diminished.ts.net",
		"https://torilo.net",
		"https://www.torilo.net",
	)


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_settings_reject_invalid_backend_port(port: str):
	with pytest.raises(ValueError, match="BACKEND_PORT"):
		Settings.from_env({"BACKEND_PORT": port})


def test_logging_configuration_rejects_unknown_level():
	with pytest.raises(TypeError, match="logging level"):
		configure_logging("TRACE")


def test_logging_configuration_sets_level_without_exposing_env_values(monkeypatch):
	previous_level = logging.getLogger().level
	monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-logged")
	try:
		configure_logging("WARNING")
		assert logging.getLogger().level == logging.WARNING
	finally:
		logging.getLogger().setLevel(previous_level)