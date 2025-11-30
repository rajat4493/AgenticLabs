from __future__ import annotations

from typing import Dict

from routing.categories import QueryCategory

OPENAI_PRICING: Dict[str, Dict[str, float]] = {
    # prices per single token in USD
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
}


def get_pricing(model: str, default: str = "gpt-4o-mini") -> Dict[str, float]:
    return OPENAI_PRICING.get(model) or OPENAI_PRICING[default]


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = get_pricing(model)
    cost_input = prompt_tokens * pricing["input"]
    cost_output = completion_tokens * pricing["output"]
    return round(cost_input + cost_output, 8)


def calc_baseline_cost(
    prompt_tokens: int,
    completion_tokens: int,
    baseline_model: str = "gpt-4o",
) -> float:
    pricing = get_pricing(baseline_model, default="gpt-4o")
    cost_input = prompt_tokens * pricing["input"]
    cost_output = completion_tokens * pricing["output"]
    return round(cost_input + cost_output, 8)


CATEGORY_OUTPUT_MULTIPLIERS = {
    QueryCategory.CODING: 1.8,
    QueryCategory.DATA: 1.3,
    QueryCategory.LEGAL: 2.2,
    QueryCategory.COMPLIANCE: 2.0,
    QueryCategory.FINANCE: 1.7,
    QueryCategory.CREATIVE: 1.5,
    QueryCategory.GENERAL: 1.0,
    QueryCategory.PRODUCT: 1.2,
    QueryCategory.OPERATIONS: 1.1,
    QueryCategory.UNKNOWN: 1.0,
}


def estimate_output_tokens(prompt_tokens: int, category: QueryCategory) -> int:
    multiplier = CATEGORY_OUTPUT_MULTIPLIERS.get(category, 1.0)
    return int(prompt_tokens * multiplier)


def estimate_cost_for_model(
    model: str, prompt_tokens: int, category: QueryCategory
) -> float:
    pricing = get_pricing(model)
    output_tokens = estimate_output_tokens(prompt_tokens, category)
    cost_input = prompt_tokens * pricing["input"]
    cost_output = output_tokens * pricing["output"]
    return round(cost_input + cost_output, 8)
