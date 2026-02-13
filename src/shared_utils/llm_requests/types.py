from dataclasses import dataclass


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


@dataclass
class ResponsePrice:
    """Coût détaillé d'une réponse API.

    Champs:
      input_price: Coût des tokens d'entrée non-cachés.
      input_cached_price: Coût des tokens d'entrée cachés.
      output_price: Coût des tokens de sortie.
      total_price: Coût total (input_price + input_cached_price + output_price).
      input_tokens: Nombre de tokens d'entrée non-cachés (ou secondes pour STT).
      input_cached_tokens: Nombre de tokens d'entrée cachés.
      output_tokens: Nombre de tokens de sortie.
      input_pricing: Tarif appliqué pour les tokens d'entrée ($/M).
      input_cached_pricing: Tarif appliqué pour les tokens cachés ($/M).
      output_pricing: Tarif appliqué pour les tokens de sortie ($/M).
      currency: Devise utilisée pour les prix (par défaut "dollar").
      currency_symbol: Symbole de la devise (par défaut "$").
    """
    input_price: float = 0.0
    input_cached_price: float = 0.0
    output_price: float = 0.0
    total_price: float = 0.0
    
    input_tokens: int = 0  # Nombre de tokens d'entrée ou secondes pour STT
    input_cached_tokens: int = 0  # Nombre de tokens d'entrée cachés
    output_tokens: int = 0  # Nombre de tokens de sortie
    
    input_pricing: float = 0.0  # Tarif en $/M pour les tokens d'entrée
    input_cached_pricing: float = 0.0  # Tarif en $/M pour les tokens cachés
    output_pricing: float = 0.0  # Tarif en $/M pour les tokens de sortie
    
    currency: str = "dollar"
    currency_symbol: str = "$"
    quantity: int = 1  # Nombre d'appels ou d'unités facturées

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

        return cls(
            input_price=input_cost,
            input_cached_price=input_cached_cost,
            output_price=output_cost,
            total_price=total_cost,
            input_tokens=input_tokens,
            input_cached_tokens=input_cached_tokens,
            output_tokens=output_tokens,
            input_pricing=model_pricing.input,
            input_cached_pricing=model_pricing.input_cached or 0.0,
            output_pricing=model_pricing.output or 0.0,
            currency=model_pricing.currency,
            currency_symbol=model_pricing.currency_symbol
        )

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
        return cls(
            input_price=cost,
            input_cached_price=0.0,
            output_price=0.0,
            total_price=cost,
            input_tokens=int(duration_seconds),
            input_cached_tokens=0,
            output_tokens=0,
            input_pricing=model_pricing.input,
            input_cached_pricing=0.0,
            output_pricing=0.0,
            currency=model_pricing.currency,
            currency_symbol=model_pricing.currency_symbol
        )

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

        new_input_price = self.input_price + other.input_price
        new_input_cached_price = self.input_cached_price + other.input_cached_price
        new_output_price = self.output_price + other.output_price
        new_total_price = self.total_price + other.total_price
        new_input_tokens = self.input_tokens + other.input_tokens
        new_input_cached_tokens = self.input_cached_tokens + other.input_cached_tokens
        new_output_tokens = self.output_tokens + other.output_tokens
        new_quantity = self.quantity + other.quantity

        return ResponsePrice(
            input_price=new_input_price,
            input_cached_price=new_input_cached_price,
            output_price=new_output_price,
            total_price=new_total_price,
            input_tokens=new_input_tokens,
            input_cached_tokens=new_input_cached_tokens,
            output_tokens=new_output_tokens,
            input_pricing=self.input_pricing,
            input_cached_pricing=self.input_cached_pricing,
            output_pricing=self.output_pricing,
            currency=self.currency,
            currency_symbol=self.currency_symbol,
            quantity=new_quantity
        )

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

        self.input_price += other.input_price
        self.input_cached_price += other.input_cached_price
        self.output_price += other.output_price
        self.total_price += other.total_price
        self.input_tokens += other.input_tokens
        self.input_cached_tokens += other.input_cached_tokens
        self.output_tokens += other.output_tokens
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

        if self.input_price > 0:
            percentage = get_percentage(self.input_price, self.total_price)
            parts.append(f"{self.currency_symbol}{format_price(self.input_price)} (input, {percentage})")

        if self.input_cached_price > 0:
            percentage = get_percentage(self.input_cached_price, self.total_price)
            parts.append(f"{self.currency_symbol}{format_price(self.input_cached_price)} (cached, {percentage})")

        if self.output_price > 0:
            percentage = get_percentage(self.output_price, self.total_price)
            parts.append(f"{self.currency_symbol}{format_price(self.output_price)} (output, {percentage})")

        breakdown = " + ".join(parts) if parts else f"{self.currency_symbol}0"
        result = f"{breakdown} = {self.currency_symbol}{format_price(self.total_price)} total"

        # Ajouter la quantity et le coût moyen
        if self.quantity > 1:
            avg_cost = self.total_price / self.quantity
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
        return (f"ResponsePrice(input_price={self.input_price:.10g}, input_cached_price={self.input_cached_price:.10g}, "
                f"output_price={self.output_price:.10g}, total_price={self.total_price:.10g}, "
                f"input_tokens={self.input_tokens}, input_cached_tokens={self.input_cached_tokens}, output_tokens={self.output_tokens}, "
                f"input_pricing={self.input_pricing:.10g}, input_cached_pricing={self.input_cached_pricing:.10g}, "
                f"output_pricing={self.output_pricing:.10g}, quantity={self.quantity})")
