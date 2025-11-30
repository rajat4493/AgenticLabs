from __future__ import annotations

from typing import Iterable, Optional

from config.model_registry import MODEL_REGISTRY, ModelConfig
from routing.categories import QueryCategory


def capability_key_for_category(category: QueryCategory) -> str:
    if category in (QueryCategory.CODING, QueryCategory.DATA):
        return "coding"
    if category in (QueryCategory.LEGAL, QueryCategory.COMPLIANCE, QueryCategory.FINANCE):
        return "reasoning"
    if category == QueryCategory.CREATIVE:
        return "creative"
    if category == QueryCategory.OPERATIONS:
        return "operations"
    if category == QueryCategory.PRODUCT:
        return "product"
    return "reasoning"


def normalized_cost(model: ModelConfig) -> float:
    cost = (
        model.pricing.get("input_per_million", 0.0)
        + model.pricing.get("output_per_million", 0.0)
    )
    return cost if cost > 0 else 1.0


def cost_score(model: ModelConfig, sensitivity: str = "medium") -> float:
    inv = 1.0 / normalized_cost(model)
    if sensitivity == "high":
        return inv
    if sensitivity == "low":
        return inv * 0.4
    return inv * 0.7


def risk_penalty_for_band(band: str) -> float:
    band = (band or "").lower()
    if band in {"high", "complex", "long_context"}:
        return 0.4
    if band in {"medium", "moderate"}:
        return 0.2
    return 0.0


def choose_enhanced_model(
    *,
    category: QueryCategory,
    allowed_model_keys: Iterable[str],
    resolved_band: str,
) -> Optional[ModelConfig]:
    candidates = [
        MODEL_REGISTRY[key]
        for key in allowed_model_keys
        if key in MODEL_REGISTRY
    ]
    if not candidates:
        return None

    cap_key = capability_key_for_category(category)
    best_model: Optional[ModelConfig] = None
    best_score = float("-inf")
    penalty = risk_penalty_for_band(resolved_band)

    for model in candidates:
        capability = model.capabilities.get(cap_key, 0.6)
        cost_component = cost_score(model)
        score = (0.6 * capability) + (0.3 * cost_component) - penalty
        if score > best_score:
            best_score = score
            best_model = model

    return best_model
