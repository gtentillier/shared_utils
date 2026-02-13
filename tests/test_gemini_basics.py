"""Test basique avec un appel Gemini, calcul de pricing et affichage du coût."""

import os
import pytest

from shared_utils.llm_requests.gemini.caller import GeminiLLMCaller
from shared_utils.llm_requests.pricing_calculator import PricingCalculator


def test_basic_gemini_llm_call_and_pricing(model: str = "gemini-3-flash-preview"):
    """Test basique: appel Gemini, calcul de pricing et affichage du coût."""

    # Initialise l'appelant Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return

    caller = GeminiLLMCaller(api_key=api_key)
    
    input_text = "Raconte moi une blague courte sur les développeurs."
    instructions = "Tu es un assistant utile et drôle."

    print(f"\n--- Appel Gemini avec le modèle {model} ---")
    try:
        response = caller.response(
            model=model,
            input=input_text,
            instructions=instructions,
            temperature=0.7
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API : {e}")
        return

    print("✓ Réponse reçue :")
    print(f"  {response.output_text[:100]}...")  # Affiche le début
    
    # Pricing
    calculator = PricingCalculator()
    price = calculator.get_price(response, provider="gemini")
    
    print("✓ Coût estimé :")
    price.display(decimal_places=8)

if __name__ == "__main__":
    test_basic_gemini_llm_call_and_pricing()
