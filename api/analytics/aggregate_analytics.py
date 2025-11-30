from __future__ import annotations

from typing import Any, Dict, Iterable

from cost.baseline_resolver import (
    calculate_band_savings,
    extract_run_fields,
    summarize_savings,
)


def aggregate_analytics_costs(runs: Iterable[Any]) -> Dict[str, float | None]:
    total_actual = 0.0
    total_baseline = 0.0

    for run in runs:
        fields = extract_run_fields(run)
        total_actual += fields["actual_cost"]
        band_result = calculate_band_savings(run)
        total_baseline += band_result["baseline_cost"]

    savings_abs, savings_pct, message = summarize_savings(
        total_actual, total_baseline
    )

    return {
        "total_actual_cost": round(total_actual, 10),
        "total_band_baseline_cost": round(total_baseline, 10),
        "savings_band_abs": savings_abs,
        "savings_band_pct": savings_pct,
        "message": message,
    }
