from typing import Any


def _get_gemini_price(self, response: Any) -> ResponsePrice:
    """Calculate price for Gemini models and return a ResponsePrice compatible object."""
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count
    output_tokens = usage.candidates_token_count
    model = getattr(response, "model", self.model)

    # Default to Flash pricing
    input_pricing_per_m = 0.50
    output_pricing_per_m = 3.00

    if "pro" in model:
        # Prices for gemini-3-pro-preview: $2 / 1M input, $12 / 1M output
        input_pricing_per_m = 2.00
        output_pricing_per_m = 12.00

    input_price = (input_tokens / 1_000_000) * input_pricing_per_m
    output_price = (output_tokens / 1_000_000) * output_pricing_per_m
    total_price = input_price + output_price

    # Instantiate ResponsePrice and set attributes expected by pipeline.py
    price = ResponsePrice(
        input_price=input_price,
        output_price=output_price,
        total_price=total_price,
    )
    # Set additional attributes used in pipeline.py
    price.input_tokens = input_tokens
    price.output_tokens = output_tokens
    price.input_cached_tokens = 0
    price.input_pricing = input_pricing_per_m
    price.output_pricing = output_pricing_per_m
    price.input_cached_pricing = 0.0
    price.input_price = input_price
    price.output_price = output_price
    price.input_cached_price = 0.0
    price.total_price = total_price

    return price
