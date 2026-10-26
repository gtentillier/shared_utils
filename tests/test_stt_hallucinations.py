from pathlib import Path

from shared_utils.llm_requests.openai.stt import HALLUCINATED_PHRASES, OpenAISTTCaller


def test_hallucination_phrases_defined():
    assert "Sous-titrage ST' 501" in HALLUCINATED_PHRASES
    assert "Sous-titres réalisés par la communauté d'Amara.org" in HALLUCINATED_PHRASES


def test_clean_hallucinations_alone():
    # Segments that contain ONLY the hallucinated phrase (with/without leading spaces, with/without trailing dot)
    result = {
        "text": "Bonjour. Sous-titrage ST' 501.",
        "segments": [
            {"id": 0, "text": " Bonjour."},
            {"id": 1, "text": " Sous-titrage ST' 501"},
            {"id": 2, "text": " Sous-titrage ST' 501."},
            {"id": 3, "text": "  Sous-titres réalisés par la communauté d'Amara.org  "},
            {"id": 4, "text": "Sous-titres réalisés par la communauté d'Amara.org."},
        ],
    }

    cleaned = OpenAISTTCaller._clean_hallucinations(result)
    assert len(cleaned["segments"]) == 1
    assert cleaned["segments"][0]["text"] == " Bonjour."
    assert cleaned["text"] == "Bonjour."


def test_clean_hallucinations_at_end_of_segment():
    # Segments that contain text before the hallucinated phrase
    result = {
        "text": "Merci d'avoir regardé. Sous-titrage ST' 501.",
        "segments": [
            {"id": 0, "text": " Merci d'avoir regardé. Sous-titrage ST' 501"},
            {"id": 1, "text": " À bientôt! Sous-titres réalisés par la communauté d'Amara.org."},
        ],
    }

    cleaned = OpenAISTTCaller._clean_hallucinations(result)
    assert len(cleaned["segments"]) == 2
    assert cleaned["segments"][0]["text"] == " Merci d'avoir regardé."
    assert cleaned["segments"][1]["text"] == " À bientôt!"
    assert cleaned["text"] == "Merci d'avoir regardé. À bientôt!"


def test_clean_hallucinations_no_segments():
    result = {"text": "Juste du texte", "language": "fr"}
    cleaned = OpenAISTTCaller._clean_hallucinations(result)
    assert cleaned == {"text": "Juste du texte", "language": "fr"}


def test_clean_hallucinations_from_audio(audio_path: Path | str = "tests/data/empty.m4a", verbose: bool = True):
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    caller = OpenAISTTCaller()
    result = caller.transcribe(audio_path=audio_file, language="fr", verbose=verbose)

    # Vérifie qu'aucun segment ne se termine par l'une des phrases hallucinées
    for segment in result.get("segments", []):
        text = segment.get("text", "").strip()
        for phrase in HALLUCINATED_PHRASES:
            assert not text.endswith(phrase)
            assert not text.endswith(phrase + ".")


if __name__ == "__main__":
    # test_hallucination_phrases_defined()
    # test_clean_hallucinations_alone()
    # test_clean_hallucinations_at_end_of_segment()
    # test_clean_hallucinations_no_segments()
    test_clean_hallucinations_from_audio("tests/data/tmpwlc_5s0o_16k_mono_clean_normalized-before_compressed.wav", verbose=True)
    print("All tests passed.")
