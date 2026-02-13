import re
from dataclasses import dataclass

from openai.types.responses import Response

from ...llm_requests.types import ModelPricing, ResponsePrice


# Dictionnaire des modèles → tarifs extraits de la page, à jour du 17/11/2025
# Structure: {model: {service_tier: ModelPricing}}
PRICINGS: dict[str, dict[str, ModelPricing]] = {
    # GPT-5
    "gpt-5.1": {
        "default": ModelPricing(input=1.250, input_cached=0.125, output=10.000),
        "priority": ModelPricing(input=2.50, input_cached=0.25, output=20.00),
        "flex": ModelPricing(input=0.625, input_cached=0.0625, output=5.00),
    },
    "gpt-5": {
        "default": ModelPricing(input=1.250, input_cached=0.125, output=10.000),
        "priority": ModelPricing(input=2.50, input_cached=0.25, output=20.00),
        "flex": ModelPricing(input=0.625, input_cached=0.0625, output=5.00),
    },
    "gpt-5-mini": {
        "default": ModelPricing(input=0.250, input_cached=0.025, output=2.000),
        "priority": ModelPricing(input=0.45, input_cached=0.045, output=3.60),
        "flex": ModelPricing(input=0.125, input_cached=0.0125, output=1.00),
    },
    "gpt-5-nano": {
        "default": ModelPricing(input=0.050, input_cached=0.005, output=0.400),
        "flex": ModelPricing(input=0.025, input_cached=0.0025, output=0.20),
    },
    "gpt-5-pro": {"default": ModelPricing(input=15.000, input_cached=None, output=120.000), },

    # GPT-4.1
    "gpt-4.1": {
        "default": ModelPricing(input=2.000, input_cached=0.50, output=8.000),
        "priority": ModelPricing(input=3.50, input_cached=0.875, output=14.00),
    },
    "gpt-4.1-mini": {
        "default": ModelPricing(input=0.40, input_cached=0.10, output=1.60),
        "priority": ModelPricing(input=0.70, input_cached=0.175, output=2.80),
    },
    "gpt-4.1-nano": {
        "default": ModelPricing(input=0.10, input_cached=0.025, output=0.40),
        "priority": ModelPricing(input=0.20, input_cached=0.05, output=0.80),
    },

    # STT
    "whisper-1": {"default": ModelPricing(input=0.0001), },
}


@dataclass
class OpenAIPricingCalculator:
    """Calculateur de tarification pour les réponses API OpenAI.
    
    Permet de récupérer les tarifs des modèles et de calculer le coût
    détaillé d'une réponse API.
    """

    def _get_pricing(self, model_name: str, service_tier: str = "default") -> ModelPricing:
        """Retourne le Pricing pour le modèle donné, ou lève KeyError si inconnu.
        
        Args:
            model_name: Nom du modèle.
            service_tier: Tier de service ("default", "priority", "flex"). Par défaut "default".
        
        Returns:
            ModelPricing pour le modèle et le tier donné.
        
        Raises:
            KeyError: Si le modèle ou le tier n'est pas disponible.
        """
        if model_name not in PRICINGS:
            raise KeyError(f"Modèle inconnu: {model_name}")
        model_pricings = PRICINGS[model_name]
        if service_tier not in model_pricings:
            raise KeyError(f"Service tier '{service_tier}' non disponible pour le modèle {model_name}. Tiers disponibles: {list(model_pricings.keys())}")
        return model_pricings[service_tier]

    def get_price(self, response: Response | dict, stt_model_name: str | None = None) -> ResponsePrice:
        """Calcule le coût détaillé d'une réponse API.
        
        Support pour :
        - Réponses LLM avec usage en tokens
        - Réponses STT avec usage en secondes
        
        Args:
            response: La réponse API OpenAI contenant usage, model et service_tier.
            stt_model_name: Le nom du modèle. Requis uniquement pour les réponses STT.
                Pour les réponses LLM, le modèle est extrait de la réponse directement.

        Returns:
            ResponsePrice avec les coûts calculés.

        Raises:
            KeyError: Si le modèle ou le tier n'est pas dans la table de tarification.
            ValueError: Si stt_model_name n'est pas fourni pour une réponse STT.

        """
        try:
            stt_model_name = response.model
            mode = "LLM"
        except AttributeError:
            mode = "STT"
            if stt_model_name is None:
                raise ValueError("Le nom du modèle doit être fourni si la réponse n'a pas d'attribut 'model' (pour le STT donc)")

        # Enlève le suffixe de date (ex: "gpt-4.1-nano-2025-04-14" → "gpt-4.1-nano")
        stt_model_name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", stt_model_name)

        if mode == "LLM":
            # LLM: usage avec tokens
            pricing = self._get_pricing(stt_model_name, response.service_tier)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cached_tokens = response.usage.input_tokens_details.cached_tokens
            return ResponsePrice.from_tokens(model_pricing=pricing, input_tokens=input_tokens - cached_tokens, input_cached_tokens=cached_tokens, output_tokens=output_tokens)
        else:
            pricing = self._get_pricing(stt_model_name)
            # STT: usage = {'seconds': X, 'type': 'duration'}
            duration_seconds = response["usage"]["seconds"]
            return ResponsePrice.from_duration(model_pricing=pricing, duration_seconds=duration_seconds)


def print_all_pricings():
    print("Tarifs API OpenAI :")
    # calcule la largeur du nom de modèle le plus long pour aligner les colonnes
    max_model_len = max((len(m) for m in PRICINGS.keys()), default=0)
    # largeur pour l'affichage des nombres (ex: ' 15.000')
    num_width = 7

    for model in sorted(PRICINGS.keys()):
        model_tiers = PRICINGS[model]
        for tier in sorted(model_tiers.keys()):
            pr = model_tiers[tier]
            # formate chaque valeur numérique en gardant l'alignement, remplace None par '-'
            input_s = f"{pr.input:{num_width}.3f}" if pr.input is not None else f"{'-':>{num_width}}"
            input_cached_s = (f"{pr.input_cached:{num_width}.3f}" if pr.input_cached is not None else f"{'-':>{num_width}}")
            output_s = f"{pr.output:{num_width}.3f}" if pr.output is not None else f"{'-':>{num_width}}"

            parts = [
                f"input = {input_s} $/M",
                f"output = {output_s} $/M",
                f"input_cached = {input_cached_s} $/M",
            ]

            # aligne le nom du modèle et le tier sur la largeur calculée
            label = f"{model:<{max_model_len}} ({tier})"
            print(f"  {label:<{max_model_len + 12}} : " + ", ".join(parts))


if __name__ == "__main__":
    print_all_pricings()
