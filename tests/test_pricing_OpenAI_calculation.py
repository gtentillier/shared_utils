"""Test basique avec un appel OpenAI, calcul de pricing et affichage du coût."""

import json
import os

from shared_utils.openAI_requests._LLM_API_caller import OpenAILLMCaller
from shared_utils.openAI_requests._pricing_calculation import PricingCalculator


def test_basic_openai_llm_call_and_pricing():
    """Test basique: appel OpenAI, calcul de pricing et affichage du coût."""

    # Initialise l'appelant OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    caller = OpenAILLMCaller(api_key=api_key, model="gpt-4.1-nano")

    # Effectue un appel API simple
    print("📞 Appel OpenAI avec gpt-4.1-nano...")
    response = caller.response(
        input="Dis-moi un nombre aléatoire entre 1 et 100",
        text={
            "format": {
                "type": "json_schema",
                "strict": True,
                "name": "response_name",
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
            },
            "verbosity": "medium",
        },
        max_output_tokens=100,
    )
    print("Input:", "Dis-moi un nombre aléatoire entre 1 et 100", '\nOutput:', json.loads(response.output_text).get("result"), '\n')

    print(f"✓ Réponse reçue du modèle: {response.model}")
    print(f"✓ Tokens utilisés:")
    print(f"  - Input tokens: {response.usage.input_tokens}")
    print(f"  - Cached tokens: {response.usage.input_tokens_details.cached_tokens}")
    print(f"  - Output tokens: {response.usage.output_tokens}")

    # Calcule le prix
    calculator = PricingCalculator()
    price = calculator.get_price(response)

    # Affiche le coût
    price.display(decimal_places=8)


if __name__ == "__main__":
    test_basic_openai_llm_call_and_pricing()
