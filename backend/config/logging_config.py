"""Configure application logging without emitting secrets or request payloads."""

from __future__ import annotations

import logging

from backend.config.settings import get_settings


def configure_logging(level: str | None = None) -> None:
	"""Configure a compact, safe root logger; calling it repeatedly is harmless."""
	selected_level = (level or get_settings().log_level).upper()
	log_level = getattr(logging, selected_level, None)
	if not isinstance(log_level, int):
		raise TypeError("Unsupported logging level")

	logging.basicConfig(
		level=log_level,
		format="%(asctime)s %(levelname)s %(name)s %(message)s",
	)
	logging.getLogger().setLevel(log_level)