from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from cost.calculator import calculate_cost
from router.model_registry import (
    NAIVE_BASELINE_MODEL_KEY,
    get_band_baseline_model,
)

OPTIMAL_MESSAGE = "Premium model required for this task (correct)."


def _extract_run_fields(run: Any) -> Dict[str, Any]:
    if isinstance(run, dict):
        getter = run.get
    else:
        getter = lambda key: getattr(run, key, None)

    return {
        "band": getter("band"),
        "prompt_tokens": getter("prompt_tokens") or 0,
        "completion_tokens": getter("completion_tokens") or 0,
        "actual_cost": getter("cost_usd") or 0.0,
    }


def extract_run_fields(run: Any) -> Dict[str, Any]:
    data = _extract_run_fields(run)
    return {
        "band": data["band"],
        "prompt_tokens": data["prompt_tokens"],
        "completion_tokens": data["completion_tokens"],
        "actual_cost": data["actual_cost"],
    }


def calculate_naive_gpt4o_savings(run: Any) -> Dict[str, Any]:
    values = _extract_run_fields(run)
    baseline_cost = calculate_cost(
        model_key=NAIVE_BASELINE_MODEL_KEY,
        input_tokens=values["prompt_tokens"],
        output_tokens=values["completion_tokens"],
    )
    optimal = values["actual_cost"] >= baseline_cost and baseline_cost > 0
    savings = 0.0 if optimal else max(baseline_cost - values["actual_cost"], 0.0)
    return {
        "baseline_cost": baseline_cost,
        "savings": round(savings, 10),
        "optimal": optimal,
    }


def calculate_band_savings(run: Any) -> Dict[str, Any]:
    values = _extract_run_fields(run)
    baseline_model = get_band_baseline_model(values["band"])
    baseline_cost = calculate_cost(
        model_key=baseline_model,
        input_tokens=values["prompt_tokens"],
        output_tokens=values["completion_tokens"],
    )
    optimal = values["actual_cost"] >= baseline_cost and baseline_cost > 0
    savings = 0.0 if optimal else max(baseline_cost - values["actual_cost"], 0.0)
    return {
        "baseline_cost": baseline_cost,
        "baseline_model": baseline_model,
        "savings": round(savings, 10),
        "optimal": optimal,
    }


def summarize_savings(total_actual: float, total_baseline: float) -> Tuple[float, float, str | None]:
    if total_baseline <= 0:
        return 0.0, 0.0, None
    raw = total_baseline - total_actual
    if raw <= 0:
        return 0.0, 0.0, OPTIMAL_MESSAGE
    pct = (raw / total_baseline) * 100.0
    return round(raw, 10), round(pct, 4), None
