from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from google import genai


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
        """Call Gemini API and return a GeminiResponse object.
        
        Args:
            model: Model to use.
            input: User input text.
            instructions: System instructions.
            temperature: Temperature.
            max_output_tokens: Max tokens.
            text: Configuration dict (compatible with OpenAILLMCaller signature). 
                  Supports 'format': {'type': 'json_schema', 'schema': ...}.
        
        Returns:
            GeminiResponse object details.
        """

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

        # Add thinking level if model is gemini-3 or similar reasoning model
        # Note: This is a heuristic based on the provided code snippet
        if "gemini-3" in model:
            # Add logic if specific config is needed for gemini-3
            pass

        response = self.client.models.generate_content(model=model, contents=input, config=config_args)

        return GeminiResponse(output_text=response.text, usage_metadata=response.usage_metadata, model=model)
