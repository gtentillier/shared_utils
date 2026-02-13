"""Test basique avec un appel OpenAI, calcul de pricing et affichage du coût."""

import json
import os

from shared_utils.llm_requests import OpenAILLMCaller
from shared_utils.llm_requests import PricingCalculator


def test_basic_openai_llm_call_and_pricing(model: str = "gpt-4.1-nano"):
    """Test basique: appel OpenAI, calcul de pricing et affichage du coût."""

    # Initialise l'appelant OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    caller = OpenAILLMCaller(api_key=api_key)

    # Effectue un appel API simple
    print(f"📞 Appel OpenAI avec {model}...")
    response = caller.response(
        model=model,
        input="Dis-moi un nombre aléatoire entre 1 et 100 sans phrase, uniquement un nombre",
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
        # reasoning={'effort': 'high'},
    )
    try:
        print("Input:", "Dis-moi un nombre aléatoire entre 1 et 100 sans phrase, uniquement un nombre", '\nOutput:', json.loads(response.output_text).get("result"), '\n')
    except AttributeError:
        pass
    print(f"Output complet: {response.output_text}\n")

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
    test_basic_openai_llm_call_and_pricing(model="gpt-4.1-nano")
