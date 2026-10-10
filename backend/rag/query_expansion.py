"""Small deterministic query variants for approved-document retrieval."""

from __future__ import annotations

import re


def expand_query_variants(query: str, max_variants: int = 3) -> list[str]:
	"""Keep the original first and add a few lexical variants for retrieval only."""
	original = " ".join(query.split())
	if not original:
		return []

	variants = [original]
	lower = original.lower()
	if re.search(r"\bprogram\b", lower):
		variants.append(re.sub(r"\bprogram\b", "programme", original, flags=re.IGNORECASE))
	elif re.search(r"\bprogramme\b", lower):
		variants.append(re.sub(r"\bprogramme\b", "program", original, flags=re.IGNORECASE))

	if re.search(r"\bremote\b", lower):
		variants.append(re.sub(r"\bremote\b", "online", original, flags=re.IGNORECASE))
	elif re.search(r"\bonline\b", lower):
		variants.append(re.sub(r"\bonline\b", "remote", original, flags=re.IGNORECASE))

	unique: list[str] = []
	seen: set[str] = set()
	for variant in variants:
		key = variant.casefold()
		if key not in seen:
			unique.append(variant)
			seen.add(key)
		if len(unique) >= max(1, max_variants):
			break
	return unique
