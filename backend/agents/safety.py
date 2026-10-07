"""Deterministic input screening and fixed safety response helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

SAFETY_RESPONSE = (
	"I can only provide information supported by approved Torilo Academy sources. "
	"I can't make up or override academy information."
)

_INJECTION_PATTERNS = (
	re.compile(r"\bignore\b.{0,50}\b(instructions|rules|prompt|policy)\b", re.IGNORECASE),
	re.compile(r"\b(disregard|override|bypass)\b.{0,50}\b(instructions|rules|safety|policy)\b", re.IGNORECASE),
	re.compile(r"\b(make up|invent|fabricate|pretend)\b.{0,60}\b(policy|academy|torilo|answer|information)\b", re.IGNORECASE),
	re.compile(r"\b(reveal|print|show|expose)\b.{0,60}\b(system prompt|api key|secret|credential|token)\b", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class SafetyDecision:
	blocked: bool
	reason: str | None = None


def inspect_user_message(message: str) -> SafetyDecision:
	"""Screen for direct override/fabrication requests before any tool/LLM call.

	This narrow deterministic check is defense in depth, not a complete security
	classifier. Retrieved documents and database records must also be treated as
	untrusted data by prompts and downstream code.
	 """
	normalized = " ".join(message.split())
	if not normalized:
		return SafetyDecision(blocked=True, reason="empty_message")
	for pattern in _INJECTION_PATTERNS:
		if pattern.search(normalized):
			return SafetyDecision(blocked=True, reason="instruction_override_or_fabrication")
	return SafetyDecision(blocked=False)


def safe_response() -> str:
	"""Return a fixed response; this path intentionally does not invoke the LLM."""
	return SAFETY_RESPONSE
