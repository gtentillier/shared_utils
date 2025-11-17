import warnings
from pathlib import Path
from time import perf_counter
from typing import Any

import torch
import whisper
from openai import OpenAI
from openai.types.audio.transcription import Transcription

warnings.filterwarnings("ignore", message=r".*FP16 is not supported on CPU; using FP32.*")


class OpenAISTTCaller:
    """Handle audio transcription using either local Whisper or OpenAI's Whisper API.
    
    Provides a unified interface for transcribing audio files with support for both
    local Whisper models and OpenAI's Whisper API.
    
    Attributes:
        use_api: If True, uses OpenAI's Whisper API, otherwise uses local Whisper model.
        model: Loaded Whisper model instance (for local mode only, None for API mode).
        last_duration: Duration of the last transcription call in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        use_api: bool = False,
        model: str | None = None,
    ):
        """Initialize the Speech-to-Text caller.
        
        Args:
            api_key: OpenAI API key. If not provided and use_api=True,
                    will use OPENAI_API_KEY environment variable.
            use_api: If True, use OpenAI's Whisper API instead of local model.
                           Defaults to False.
            model: Model to load for local transcription.
                   - For local Whisper: "large" or "turbo"
                   - Ignored if use_api=True (remains None)
                   - If None and use_api=False, defaults to "turbo"
                   Defaults to None.
        
        Raises:
            ValueError: If model is invalid for local mode.
        """
        self.use_api = use_api
        self.last_duration: float | None = None
        self._loaded_model_name: str | None = None

        if self.use_api:
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = OpenAI()
            self.model = None
        else:
            # Load model at initialization for local mode
            model_to_load = model or "turbo"

            valid_models = ["large", "turbo"]
            if model_to_load not in valid_models:
                raise ValueError(f"Model '{model_to_load}' not supported for local Whisper. "
                                 f"Use one of: {', '.join(valid_models)}")

            device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
            self.model = whisper.load_model(model_to_load, device=device)
            self._loaded_model_name = model_to_load

    def transcribe(
        self,
        audio_path: Path | str,
        model: str | None = None,
        language: str | None = None,
        response_format: str = "verbose_json",
        timestamp_granularities: list | None = None,
        task: str = "transcribe",
    ) -> dict[str, Any]:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file to transcribe.
            model: Model to use for transcription (optional).
                   - For OpenAI API: "whisper-1", "gpt-4o-mini-transcribe", or "gpt-4o-transcribe"
                   - For local Whisper: "large" or "turbo"
                   If None, uses the model specified at initialization (local mode), "turbo" by default, or defaults to "whisper-1" (API mode).
            language: Language code (e.g., "fr", "en"). If None, auto-detect.
            response_format: Response format for OpenAI API. Options: "json", "text", "verbose_json", "srt", "vtt".
                           Defaults to "verbose_json".
            timestamp_granularities: only for "whisper-1", if response_format is set to "verbose_json" : ["word"], ["segment"] or ["word", "segment"]. Defaults to ["segment"].
            task: Transcription task - "transcribe" or "translate". Only used for local Whisper mode.
                  Defaults to "transcribe".

        Returns:
            dict[str, Any] containing transcription results. For verbose_json format, includes:
                - "text": Full transcribed text
                - "language": Detected language
                - "duration": Audio duration
                - "segment": List of segments with timestamps
                - "usage": Seconds usage details
            For other formats, returns the API response as dict.

        Raises:
            FileNotFoundError: If audio file does not exist.
            ValueError: If model is not supported for the chosen mode.
            KeyError: If expected keys are missing from API response.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start = perf_counter()

        try:
            if self.use_api:
                # Use provided model or default to whisper-1
                api_model = model or "whisper-1"
                # Fix mutable default argument
                timestamp_granularities = timestamp_granularities or ["segment"]
                result = self._transcribe_with_openai_api(
                    audio_path=audio_path,
                    model=api_model,
                    language=language,
                    response_format=response_format,
                    timestamp_granularities=timestamp_granularities,
                )
            else:
                result = self._transcribe_with_local_model(
                    audio_path=audio_path,
                    model=model,
                    language=language,
                    task=task,
                )
        finally:
            end = perf_counter()
            self.last_duration = end - start

        return result

    def _transcribe_with_openai_api(
        self,
        audio_path: Path,
        model: str,
        language: str | None,
        response_format: str = "verbose_json",
        timestamp_granularities: list | None = None,
    ) -> dict[str, Any]:
        """Call OpenAI's Whisper API for transcription."""
        if model not in ["whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe"]:
            raise ValueError(f"Model '{model}' not supported for OpenAI API. "
                             "Use 'whisper-1', 'gpt-4o-mini-transcribe', or 'gpt-4o-transcribe'.")

        # Build request parameters
        request_params = {
            "model": model,
            "file": audio_path.open("rb"),
            "response_format": response_format,
        }

        if language:
            request_params["language"] = language

        if timestamp_granularities:
            request_params["timestamp_granularities"] = timestamp_granularities

        try:
            result = self.client.audio.transcriptions.create(**request_params)

            # Convert response to dict
            if hasattr(result, "to_dict"):
                response_dict = result.to_dict()
            elif isinstance(result, dict):
                response_dict = result
            else:
                response_dict = getattr(result, "__dict__", {})

            return response_dict

        finally:
            request_params["file"].close()

    def _transcribe_with_local_model(
        self,
        audio_path: Path,
        model: str | None,
        language: str | None,
        task: str,
    ) -> dict[str, Any]:
        """Transcribe using local Whisper model.
        
        Args:
            audio_path: Path to the audio file.
            model: Specific model to use. If provided and different from loaded model,
                   will reload. If None, uses the model loaded at initialization.
            language: Language code for transcription.
            task: Task type ("transcribe" or "translate").
            
        Returns:
            dict[str, Any]: Transcription results including text, language, duration, and segments.
            
        Raises:
            ValueError: If model is not supported.
        """
        valid_models = ["large", "turbo"]

        # Determine which model to use
        model_to_use = model if model is not None else self._loaded_model_name

        # Validate and load model if needed
        if model is not None and model not in valid_models:
            raise ValueError(f"Model '{model}' not supported for local Whisper. "
                             f"Use one of: {', '.join(valid_models)}")

        # Reload model if a different one is requested
        if model is not None and model != self._loaded_model_name:
            device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
            self.model = whisper.load_model(model, device=device)
            self._loaded_model_name = model

        # Prepare transcription parameters
        transcribe_params = {
            "audio": str(audio_path),
            "task": task,
        }

        if language:
            transcribe_params["language"] = language

        # Transcribe
        result = self.model.transcribe(**transcribe_params)

        return result
