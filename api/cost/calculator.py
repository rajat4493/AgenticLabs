from __future__ import annotations

from typing import Tuple

from config.model_registry import MODEL_REGISTRY, ModelConfig
from costs import get_unit_prices


def resolve_model_key(provider: str | None, model: str | None) -> str | None:
    if not provider or not model:
        return None
    return f"{provider}:{model}"


def _lookup_model_config(model_key: str | None) -> ModelConfig | None:
    if not model_key:
        return None
    return MODEL_REGISTRY.get(model_key)


def _determine_provider_model(
    model_key: str | None, provider: str | None, model: str | None
) -> Tuple[str | None, str | None]:
    if model_key and ":" in model_key:
        key_provider, key_model = model_key.split(":", 1)
        provider = provider or key_provider
        model = model or key_model
    return provider, model


def _per_token_prices(model_key: str | None, provider: str | None, model: str | None) -> Tuple[float, float]:
    cfg = _lookup_model_config(model_key)
    if cfg and cfg.pricing:
        return (
            (cfg.pricing.get("input_per_million", 0.0) / 1_000_000),
            (cfg.pricing.get("output_per_million", 0.0) / 1_000_000),
        )

    provider, model = _determine_provider_model(model_key, provider, model)
    if provider and model:
        per_1k_in, per_1k_out = get_unit_prices(provider, model)
    else:
        per_1k_in, per_1k_out = (0.0, 0.0)
    return (per_1k_in / 1000.0, per_1k_out / 1000.0)


def calculate_cost(
    *,
    model_key: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> float:
    """
    Compute spend for a model given token counts.
    Falls back to pricing profile if registry lacks explicit pricing.
    """
    input_tokens = int(input_tokens or 0)
    output_tokens = int(output_tokens or 0)
    per_in, per_out = _per_token_prices(model_key, provider, model)
    cost = input_tokens * per_in + output_tokens * per_out
    return round(cost, 10)
