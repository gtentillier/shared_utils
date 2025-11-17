import re
from dataclasses import dataclass

from openai.types.responses import Response


@dataclass
class ModelPricing:
    """Tarification d'un modèle pour les tokens.

    Champs:
      input: Prix par million de tokens ($/M) pour les tokens d'entrée
             (Prompt pour les LLMs), ou prix par seconde pour les STT.
      input_cached: Prix en $/M pour les tokens d'entrée lorsque la réponse est servie
                    depuis un cache (réductions possibles). Valeur None si le tarif
                    n'est pas applicable ou non renseigné.
      output: Prix en $/M pour les tokens de sortie (tokens générés par le modèle).
              Valeur None si le modèle n'a pas de facturation de sortie distincte (STT).
      currency: Devise utilisée pour les prix (par défaut "dollar").
      currency_symbol: Symbole de la devise (par défaut "$").
    """
    input: float
    input_cached: float | None = None
    output: float | None = None
    currency: str = "dollar"
    currency_symbol: str = "$"


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
class ResponsePrice:
    """Coût détaillé d'une réponse API.

    Champs:
      input: Coût des tokens d'entrée non-cachés.
      input_cached: Coût des tokens d'entrée cachés.
      output: Coût des tokens de sortie.
      total: Coût total (input + input_cached + output).
      currency: Devise utilisée pour les prix (par défaut "dollar").
      currency_symbol: Symbole de la devise (par défaut "$").
    """
    input: float
    input_cached: float
    output: float
    total: float
    currency: str = "dollar"
    currency_symbol: str = "$"
    quantity: int = 1

    @classmethod
    def from_tokens(cls, model_pricing: ModelPricing, input_tokens: int, input_cached_tokens: int = 0, output_tokens: int = 0) -> "ResponsePrice":
        """Calcule le coût d'une réponse à partir du nombre de tokens.

        Args:
            model_pricing: Tarif du modèle.
            input_tokens: Nombre de tokens d'entrée non-cachés.
            input_cached_tokens: Nombre de tokens d'entrée cachés (par défaut 0).
            output_tokens: Nombre de tokens de sortie (par défaut 0).

        Returns:
            ResponsePrice avec les coûts calculés.
        """
        input_cost = (input_tokens * model_pricing.input) / 1_000_000
        input_cached_cost = 0.0
        if model_pricing.input_cached is not None:
            input_cached_cost = (input_cached_tokens * model_pricing.input_cached) / 1_000_000

        output_cost = 0.0
        if model_pricing.output is not None:
            output_cost = (output_tokens * model_pricing.output) / 1_000_000

        total_cost = input_cost + input_cached_cost + output_cost

        return cls(input=input_cost, input_cached=input_cached_cost, output=output_cost, total=total_cost, currency=model_pricing.currency, currency_symbol=model_pricing.currency_symbol)

    @classmethod
    def from_duration(cls, model_pricing: ModelPricing, duration_seconds: float) -> "ResponsePrice":
        """Calcule le coût d'une réponse STT à partir de la durée en secondes.

        Args:
            model_pricing: Tarif du modèle (prix par seconde).
            duration_seconds: Durée de l'audio en secondes.

        Returns:
            ResponsePrice avec le coût calculé.
        """
        cost = duration_seconds * model_pricing.input
        return cls(input=cost, input_cached=0.0, output=0.0, total=cost, currency=model_pricing.currency, currency_symbol=model_pricing.currency_symbol)

    def __add__(self, other: "ResponsePrice") -> "ResponsePrice":
        """Additionne deux ResponsePrice et retourne un nouveau ResponsePrice.
        
        Args:
            other: Autre ResponsePrice à additionner.
        
        Returns:
            Nouveau ResponsePrice avec les coûts et quantités additionnés.
        
        Raises:
            ValueError: Si les devises ne correspondent pas.
        """
        if self.currency != other.currency:
            raise ValueError(f"Impossible d'additionner des prix avec des devises différentes: {self.currency} vs {other.currency}")

        new_input = self.input + other.input
        new_input_cached = self.input_cached + other.input_cached
        new_output = self.output + other.output
        new_total = self.total + other.total
        new_quantity = self.quantity + other.quantity

        return ResponsePrice(input=new_input, input_cached=new_input_cached, output=new_output, total=new_total, currency=self.currency, currency_symbol=self.currency_symbol, quantity=new_quantity)

    def __iadd__(self, other: "ResponsePrice") -> "ResponsePrice":
        """Additionne en place un autre ResponsePrice.
        
        Args:
            other: Autre ResponsePrice à additionner.
        
        Returns:
            self avec les coûts et quantités mises à jour.
        
        Raises:
            ValueError: Si les devises ne correspondent pas.
        """
        if self.currency != other.currency:
            raise ValueError(f"Impossible d'additionner des prix avec des devises différentes: {self.currency} vs {other.currency}")

        self.input += other.input
        self.input_cached += other.input_cached
        self.output += other.output
        self.total += other.total
        self.quantity += other.quantity

        return self

    def _format_human_readable(self, decimal_places: int = 8) -> str:
        """Formate les prix de manière lisible pour un humain.
        
        Args:
            decimal_places: Nombre de décimales à afficher (par défaut 8).
        
        Returns:
            Chaîne formatée avec les prix détaillés, pourcentages, total et coût moyen.
            Exemple: "$0.00000024 (input, 37%) + $0.00000041 (output, 63%) = $0.00000065 total"
                     "(x2 appels, $0.000000325 par appel)"
        """

        def format_price(value: float) -> str:
            """Formate un prix en supprimant les zéros inutiles à la fin."""
            formatted = f"{value:.{decimal_places}f}"
            # Supprime les zéros à la fin, mais garde au moins un chiffre après la virgule
            formatted = formatted.rstrip('0')
            # Si on a supprimé tous les zéros après la virgule, ajouter un seul zéro
            if formatted.endswith('.'):
                formatted += '0'
            return formatted

        def get_percentage(value: float, total: float) -> str:
            """Calcule le pourcentage d'un coût par rapport au total."""
            if total == 0:
                return "0%"
            return f"{round(100 * value / total)}%"

        parts = []

        if self.input > 0:
            percentage = get_percentage(self.input, self.total)
            parts.append(f"{self.currency_symbol}{format_price(self.input)} (input, {percentage})")

        if self.input_cached > 0:
            percentage = get_percentage(self.input_cached, self.total)
            parts.append(f"{self.currency_symbol}{format_price(self.input_cached)} (cached, {percentage})")

        if self.output > 0:
            percentage = get_percentage(self.output, self.total)
            parts.append(f"{self.currency_symbol}{format_price(self.output)} (output, {percentage})")

        breakdown = " + ".join(parts) if parts else f"{self.currency_symbol}0"
        result = f"{breakdown} = {self.currency_symbol}{format_price(self.total)} total"

        # Ajouter la quantity et le coût moyen
        if self.quantity > 1:
            avg_cost = self.total / self.quantity
            result += f" (x{self.quantity} appels, {self.currency_symbol}{format_price(avg_cost)} par appel)"

        return result

    def display(self, decimal_places: int = 8) -> None:
        """Affiche le prix de manière lisible pour un humain.
        
        Args:
            decimal_places: Nombre de décimales à afficher (par défaut 8).
        """
        print(self._format_human_readable(decimal_places=decimal_places))

    def __str__(self) -> str:
        """Représentation en chaîne de la réponse de prix."""
        return self._format_human_readable()

    def __repr__(self) -> str:
        """Représentation détaillée de la réponse de prix."""
        return (f"ResponsePrice(input={self.input:.10g}, input_cached={self.input_cached:.10g}, "
                f"output={self.output:.10g}, total={self.total:.10g}, quantity={self.quantity})")


@dataclass
class PricingCalculator:
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

    def get_price(self, response: Response, model_name: str | None = None) -> ResponsePrice:
        """Calcule le coût détaillé d'une réponse API.
        
        Support pour :
        - Réponses LLM avec usage en tokens
        - Réponses STT avec usage en secondes
        
        Args:
            response: La réponse API OpenAI contenant usage, model et service_tier.
            model_name: Le nom du modèle. Requis uniquement pour les réponses STT.
                Pour les réponses LLM, le modèle est extrait de la réponse.

        Returns:
            ResponsePrice avec les coûts calculés.

        Raises:
            KeyError: Si le modèle ou le tier n'est pas dans la table de tarification.
            ValueError: Si model_name n'est pas fourni pour une réponse STT.

        """
        try:
            model_name = response.model
        except AttributeError:
            if model_name is None:
                raise ValueError("Le nom du modèle doit être fourni si la réponse n'a pas d'attribut 'model' (pour le STT donc)")

        # Enlève le suffixe de date (ex: "gpt-4.1-nano-2025-04-14" → "gpt-4.1-nano")
        model_name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model_name)

        pricing = self._get_pricing(model_name, response.service_tier)
        # Déterminer le type de réponse (STT ou LLM)
        if hasattr(response.usage, 'seconds'):
            # STT: usage = {'seconds': X, 'type': 'duration'}
            duration_seconds = response.usage.seconds
            return ResponsePrice.from_duration(model_pricing=pricing, duration_seconds=duration_seconds)
        else:
            # LLM: usage avec tokens
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cached_tokens = response.usage.input_tokens_details.cached_tokens
            return ResponsePrice.from_tokens(model_pricing=pricing, input_tokens=input_tokens - cached_tokens, input_cached_tokens=cached_tokens, output_tokens=output_tokens)


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
