from __future__ import annotations

from typing import Dict

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
