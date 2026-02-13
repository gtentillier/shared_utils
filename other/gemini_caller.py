from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger("api_logger")


@dataclass
class GeminiResponse:
    """Mock a response object that can be used by DialogueLLMCleaner."""
    output_text: str
    usage_metadata: Any
    model: str


@dataclass
class GeminiLLMCaller:
    api_key: str | None = None

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key must be provided either via api_key or GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def response(self, model: str, input: str, instructions: str, temperature: float = 1.0, max_output_tokens: int | None = None, text: dict[str, Any] | None = None, **kwargs: Any) -> GeminiResponse:
        """Call Gemini API and return a GeminiResponse object."""

        config_args: dict[str, Any] = {
            "system_instruction": instructions,
            "temperature": temperature,
        }

        if max_output_tokens:
            config_args["max_output_tokens"] = max_output_tokens

        if text and text.get("format", {}).get("type") == "json_schema":
            schema = text["format"]["schema"]
            config_args["response_mime_type"] = "application/json"
            config_args["response_json_schema"] = schema

        # Add thinking level if model is gemini-3
        if "gemini-3" in model:
            # Map verbosity to thinking_level
            verbosity = text.get("verbosity", "medium") if text else "medium"

            if "pro" in model:
                # Pro only supports low and high
                verbosity_map = {
                    "low": "low",
                    "medium": "high",  # medium is not supported on Pro, upgrade to high
                    "high": "high"
                }
            else:
                # Flash supports minimal, medium, low, high
                verbosity_map = {"low": "minimal", "medium": "medium", "high": "high"}

            thinking_level = kwargs.get("thinking_level", verbosity_map.get(verbosity, "medium"))
            config_args["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)

        try:
            response = self.client.models.generate_content(model=model, contents=input, config=types.GenerateContentConfig(**config_args))

            return GeminiResponse(output_text=response.text, usage_metadata=response.usage_metadata, model=model)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise e
