"""Test basique: appel OpenAI Whisper API et affichage de la transcription."""

import os
from pathlib import Path

from shared_utils.llm_requests import PricingCalculator
from shared_utils.llm_requests import OpenAISTTCaller


def test_basic_openai_speech_to_text_transcription():
    """Test basique: appel OpenAI Whisper API et affichage de la transcription."""

    # Initialise l'appelant OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    # Chemin du fichier audio
    audio_file = Path(__file__).parent / "data" / "full_first_23s_16k_mono.wav"

    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    caller = OpenAISTTCaller(api_key=api_key, use_api=True)

    # Effectue la transcription
    print("🎤 Appel OpenAI Whisper API avec whisper-1...")
    result = caller.transcribe(audio_path=audio_file, model="whisper-1", language="fr", response_format="verbose_json")

    print(f"✓ Transcription reçue du modèle")
    print(f"\n📝 Transcription :")
    print(f"  {result.get('text', 'N/A')}\n")

    print(f"✓ Informations additionnelles:")
    print(f"  - Durée du traitement: {caller.last_duration:.2f}s")
    if result.get("language"):
        print(f"  - Langue détectée: {result['language']}")
    if result.get("duration"):
        print(f"  - Durée de l'audio: {result['duration']:.2f}s")

    # Calcule le prix
    calculator = PricingCalculator()
    # price = calculator.get_price_for_stt(model="whisper-1", duration_seconds=result.get("duration", 0))
    # Adapted to new API: construct a dict compatible with get_price expecting 'usage'
    duration = result.get("duration", 0)
    mock_stt_response = {"usage": {"seconds": duration}}
    price = calculator.get_price(mock_stt_response, stt_model_name="whisper-1")

    print(f"\n✓ Coût de la transcription :")
    price.display(decimal_places=6)


if __name__ == "__main__":
    test_basic_openai_speech_to_text_transcription()
