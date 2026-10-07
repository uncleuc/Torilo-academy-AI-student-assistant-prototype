"""Whitelist and normalize citations returned to the API/frontend."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _metadata_for_source(source: Mapping[str, Any]) -> Mapping[str, Any]:
	metadata = source.get("metadata")
	return metadata if isinstance(metadata, Mapping) else source


def _public_source_fields(metadata: Mapping[str, Any]) -> dict[str, Any]:
	"""Normalize the Phase 1 and pushed Group 1 citation field names."""
	aliases = {
		"document": metadata.get("document", metadata.get("source")),
		"title": metadata.get("title", metadata.get("document_type", metadata.get("document_id"))),
		"section": metadata.get("section"),
		"page": metadata.get("page"),
		"source_type": metadata.get("source_type"),
		"category": metadata.get("category"),
	}
	return {key: value for key, value in aliases.items() if value is not None}


def format_sources(sources: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
	"""Return only citation-safe public fields; drop internal score/embedding data."""
	formatted: list[dict[str, Any]] = []
	seen: set[tuple[Any, ...]] = set()
	for source in sources:
		if source.get("approved", True) is not True:
			continue
		metadata = _metadata_for_source(source)
		if metadata.get("approved", True) is not True:
			continue
		item = _public_source_fields(metadata)
		if not item.get("document") and not item.get("title"):
			continue
		identity = tuple(item.get(key) for key in ("document", "section", "page"))
		if identity not in seen:
			seen.add(identity)
			formatted.append(item)
	return formatted
