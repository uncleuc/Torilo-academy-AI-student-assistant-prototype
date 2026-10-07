"""Construct the selected chat model from environment configuration."""

from __future__ import annotations

import os
from typing import Any

from langchain_openai import ChatOpenAI


class LLMConfigurationError(RuntimeError):
	"""Raised when required model configuration is missing or invalid."""


def create_chat_model(
	*,
	model_name: str | None = None,
	temperature: float = 0.0,
	timeout_seconds: float = 30.0,
	max_retries: int = 2,
) -> Any:
	"""Create a ChatOpenAI model without logging or embedding credentials.

	Tests should inject a fake model into the graph and should not call this
	function. A real provider connection is created only when the model is used.
	 """
	api_key = os.getenv("OPENAI_API_KEY")
	selected_model = model_name or os.getenv("LLM_MODEL")
	if not api_key:
		raise LLMConfigurationError("OPENAI_API_KEY is required to initialize the LLM")
	if not selected_model:
		raise LLMConfigurationError("LLM_MODEL is required to initialize the LLM")
	if not 0.0 <= temperature <= 2.0:
		raise ValueError("temperature must be between 0 and 2")
	if timeout_seconds <= 0:
		raise ValueError("timeout_seconds must be positive")
	if max_retries < 0:
		raise ValueError("max_retries cannot be negative")

	return ChatOpenAI(
		model=selected_model,
		api_key=api_key,
		temperature=temperature,
		timeout=timeout_seconds,
		max_retries=max_retries,
	)
