from typing import Any

from ...llm_requests.types import ModelPricing, ResponsePrice

# Dictionnaire des modèles → tarifs extraits de la page
# Structure: {model: {service_tier: ModelPricing}}
# service_tier est "default" pour Gemini sauf s'il y a des tiers spécifiques
GEMINI_PRICINGS: dict[str, dict[str, ModelPricing]] = {
    # Gemini 3 pro
    "gemini-3-pro-preview": {"default": ModelPricing(input=2.00, output=12.00), },
    # Gemini 3 flash
    "gemini-3-flash-preview": {"default": ModelPricing(input=0.50, output=3.00), },
}


class GeminiPricingCalculator:
    """Calculateur de tarification pour les réponses Gemini.
    
    Permet de calculer le coût estimé d'une réponse API Gemini.
    """

    def _get_pricing(self, model_name: str, service_tier: str = "default") -> ModelPricing:
        """Retourne le Pricing pour le modèle donné.
        
        Args:
            model_name: Nom du modèle.
            service_tier: Tier de service.
        
        Returns:
            ModelPricing pour le modèle.
        """
        # Simplistic lookup for now

        # Try exact match first
        if model_name in GEMINI_PRICINGS:
            return GEMINI_PRICINGS[model_name].get(service_tier, GEMINI_PRICINGS[model_name]["default"])

        # Try partial match (heuristic)
        if "pro" in model_name:
            return GEMINI_PRICINGS["gemini-3-pro-preview"]["default"]

        # Default to Flash
        return GEMINI_PRICINGS["gemini-3-flash-preview"]["default"]

    def get_price(self, response: Any) -> ResponsePrice:
        """Calculate price for Gemini models and return a ResponsePrice compatible object.
        
        Args:
            response: Response object from GeminiLLMCaller (GeminiResponse) or api response.
            
        Returns:
            ResponsePrice object.
        """
        usage = response.usage_metadata
        # Check if usage attributes exist, otherwise defaults to 0
        input_tokens = getattr(usage, "prompt_token_count", 0)
        output_tokens = getattr(usage, "candidates_token_count", 0)

        model = getattr(response, "model", "gemini-3-flash-preview")

        pricing = self._get_pricing(model)

        input_pricing_per_m = pricing.input
        output_pricing_per_m = pricing.output if pricing.output is not None else 0.0

        input_price = (input_tokens / 1_000_000) * input_pricing_per_m
        output_price = (output_tokens / 1_000_000) * output_pricing_per_m
        total_price = input_price + output_price

        return ResponsePrice(
            input_price=input_price,
            input_cached_price=0.0,
            output_price=output_price,
            total_price=total_price,
            input_tokens=input_tokens,
            input_cached_tokens=0,
            output_tokens=output_tokens,
            input_pricing=input_pricing_per_m,
            input_cached_pricing=0.0,
            output_pricing=output_pricing_per_m,
        )
