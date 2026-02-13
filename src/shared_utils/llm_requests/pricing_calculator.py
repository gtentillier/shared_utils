from typing import Any
import re
from openai.types.responses import Response

from .openai.pricing import OpenAIPricingCalculator
from .gemini.pricing import GeminiPricingCalculator
from .types import ResponsePrice

class ConsolidatedPricingCalculator:
    """Calculateur de tarification unifié pour les réponses API LLM (OpenAI & Gemini)."""

    def __init__(self):
        self.openai_calculator = OpenAIPricingCalculator()
        self.gemini_calculator = GeminiPricingCalculator()

    def get_price(self, response: Any, provider: str | None = None, stt_model_name: str | None = None) -> ResponsePrice:
        """Calcule le coût détaillé d'une réponse API, quel que soit le fournisseur.

        Args:
            response: La réponse API (OpenAI Response, dict, ou GeminiResponse).
            provider: 'openai' ou 'gemini'. Si None, tente de déduire automatiquement.
            stt_model_name: Le nom du modèle, requis pour les réponses STT OpenAI si le modèle n'est pas dans l'objet réponse.

        Returns:
            ResponsePrice avec les coûts calculés.
        """
        
        # Détection automatique du provider si non fourni
        if provider is None:
            if hasattr(response, 'usage_metadata'): # Gemini specific
                provider = 'gemini'
            elif hasattr(response, 'service_tier'): # OpenAI specific
                 provider = 'openai'
            elif isinstance(response, Response): # OpenAI Response object
                provider = 'openai'
            elif isinstance(response, dict) and 'usage' in response and 'seconds' in response['usage']: # OpenAI STT
                provider = 'openai'
            elif isinstance(response, dict) and 'usage' in response: # OpenAI dict fallback
                provider = 'openai'
            else:
                raise ValueError("Impossible de déterminer le fournisseur (OpenAI ou Gemini). Spécifiez 'provider'.")

        if provider == 'openai':
            return self.openai_calculator.get_price(response, stt_model_name=stt_model_name)
        elif provider == 'gemini':
            return self.gemini_calculator.get_price(response)
        else:
            raise ValueError(f"Fournisseur non supporté: {provider}")

# Expose as the main PricingCalculator
PricingCalculator = ConsolidatedPricingCalculator
