import openai
from openai.types.responses import Response


class OpenAILLMCaller:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.Client(api_key=self.api_key)

    def response(
        self,
        model: str,
        include: list | None = None,
        input: str | list | None = None,
        instructions: str | None = None,
        max_output_tokens: int | None = None,
        max_tool_calls: int | None = None,
        metadata: dict | None = None,
        parallel_tool_calls: bool | None = None,
        prompt: dict | None = None,
        prompt_cache_key: str | None = None,
        safety_identifier: str | None = None,
        service_tier: str | None = "default",
        store: bool = False,
        stream: bool = False,
        stream_options: dict | None = None,
        temperature: float = 0.0,
        text: dict = {"format": {"type": "text"}, "verbosity": "low"},
        tool_choice: dict | str | None = None,
        tools: list | None = None,
        top_logprobs: int | None = None,
    ) -> Response:
        """Call OpenAI Response API.

        Args:
            model: Model to use for the request.
            include: Additional output data to include in the response.
                - web_search_call.action.sources
                - file_search_call.results
                - message.output_text.logprobs
            input: str or list of str input(s) to the model (prompt).
            instructions: Instructions to the model for context (new developer role).
            max_output_tokens: Maximum number of tokens used to generate the output, including reasoning tokens.
            max_tool_calls: Maximum number of built-in tool calls allowed during generation.
            metadata: Dict of metadata to associate with the request (does not affect generation).
            parallel_tool_calls: Whether to allow parallel tool calls. Defaults to True.
            prompt: Dict with 'id', 'variables', 'version' keys for using a prompt template stored in OpenAI API Dashboard.
            prompt_cache_key: Key for caching prompt input larger than 1024 tokens. The 256 first tokens and the prompt_cache_key are hashed to identify the prompt.
            safety_identifier: Key for identifying user.
            service_tier: One of 'flex', 'priority', 'auto'.
            store: Whether to store for later retrievals by API.
            stream: Whether to stream the response.
            stream_options: Options for streaming.
            temperature: Between 0 and 2, not for gpt-5
            text: dict with 'format' and 'verbosity' keys like :
                {
                "verbosity": "low"|"medium"|"high". Only medium supported often,
                "format": {
                        "type": "json_schema",
                        "strict": True,
                        "name": "response_with_steps",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "steps": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "explanation": {"type": "string"},
                                            "output": {"type": "string"},
                                        },
                                        "required": ["explanation", "output"],
                                        "additionalProperties": False,
                                    },
                                },
                                "result": {"type": "integer"},
                            },
                            "required": ["result", "steps"],
                            "additionalProperties": False,
                        },
                    }
                    or
                    {
                        "type": "text"
                    }
                }
            tool_choice: Tool choice configuration.
            tools: List of tools for tool use.
            top_logprobs: Include the logprobs of the top N tokens at each position.

        Returns:
            Response object from OpenAI API.

        Note:
            Unused parameters:
                - background: For launching a long task and polling the result later.
                - conversation, previous_response_id: For conversation context.
                - reasoning: Configuration options for reasoning models (gpt-5 and o-series models only).
                - truncation: For automatic truncation of long inputs exceeding model context length.
        """

        if include is None:
            include = []

        if model not in ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-5-mini", "gpt-5-nano"]:
            raise ValueError(f"Model {model} not supported for LLM mode.")

        request_params = {key: value
                          for key, value in {
                              "model": model,
                              "include": include,
                              "input": input,
                              "instructions": instructions,
                              "max_output_tokens": max_output_tokens,
                              "max_tool_calls": max_tool_calls,
                              "metadata": metadata,
                              "parallel_tool_calls": parallel_tool_calls,
                              "prompt": prompt,
                              "prompt_cache_key": prompt_cache_key,
                              "safety_identifier": safety_identifier,
                              "service_tier": service_tier,
                              "store": store,
                              "stream": stream,
                              "stream_options": stream_options,
                              "temperature": temperature,
                              "text": text,
                              "tool_choice": tool_choice,
                              "tools": tools,
                              "top_logprobs": top_logprobs,
                          }.items() if (value is not None) and (key != 'temperature' or model.startswith('gpt-5'))}

        response = self.client.responses.create(**request_params)
        return response
