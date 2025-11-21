from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Deque, Dict, List

@dataclass
class RunRecord:
    id: int
    timestamp: float
    band: str
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    baseline_cost_usd: float
    savings_usd: float


class MetricsStore:
    """Thread-safe in-memory metrics with rolling history."""

    def __init__(self, max_runs: int = 10_000) -> None:
        self._lock = threading.Lock()
        self._runs: Deque[RunRecord] = deque(maxlen=max_runs)
        self._counter = 0

    def add_run(
        self,
        *,
        band: str,
        provider: str,
        model: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        baseline_cost_usd: float,
    ) -> None:
        with self._lock:
            self._counter += 1
            savings_usd = baseline_cost_usd - cost_usd
            record = RunRecord(
                id=self._counter,
                timestamp=time.time(),
                band=band,
                provider=provider,
                model=model,
                latency_ms=float(latency_ms),
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                cost_usd=float(cost_usd),
                baseline_cost_usd=float(baseline_cost_usd),
                savings_usd=float(savings_usd),
            )
            self._runs.append(record)

    # Backwards compatibility with previous naming
    def record(self, *args, **kwargs) -> None:
        self.add_run(*args, **kwargs)

    def snapshot(self) -> dict:
        with self._lock:
            runs = list(self._runs)

        total_runs = len(runs)
        total_cost = sum(r.cost_usd for r in runs)
        total_latency = sum(r.latency_ms for r in runs)
        total_baseline = sum(r.baseline_cost_usd for r in runs)
        total_savings = sum(r.savings_usd for r in runs)

        provider_stats: Dict[str, Dict[str, float]] = {}
        for r in runs:
            stats = provider_stats.setdefault(
                r.provider,
                {"runs": 0, "latency": 0.0, "cost": 0.0},
            )
            stats["runs"] += 1
            stats["latency"] += r.latency_ms
            stats["cost"] += r.cost_usd

        provider_breakdown = [
            {
                "provider": provider,
                "runs": stats["runs"],
                "total_cost_usd": round(stats["cost"], 6),
                "avg_latency_ms": round(stats["latency"] / stats["runs"], 2)
                if stats["runs"]
                else 0.0,
            }
            for provider, stats in provider_stats.items()
        ]

        avg_latency = total_latency / total_runs if total_runs else 0.0
        cost_per_run = total_cost / total_runs if total_runs else 0.0

        baseline_cost_usd = round(total_baseline, 6) if total_runs else None
        savings_vs_baseline = round(total_savings, 6) if total_runs else None
        savings_pct = (
            round((total_savings / total_baseline) * 100.0, 2)
            if total_baseline
            else None
        )

        return {
            "total_runs": total_runs,
            "avg_latency_ms": round(avg_latency, 2),
            "total_cost_usd": round(total_cost, 6),
            "cost_per_run_usd": round(cost_per_run, 6),
            "baseline_cost_usd": baseline_cost_usd,
            "savings_vs_baseline_usd": savings_vs_baseline,
            "savings_pct": savings_pct,
            "provider_breakdown": provider_breakdown,
            "timeseries": [],
        }

    def list_runs(self, offset: int = 0, limit: int = 50) -> Dict:
        with self._lock:
            runs = list(self._runs)
        total = len(runs)
        runs = runs[::-1]
        page = runs[offset : offset + limit]
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [asdict(r) for r in page],
        }


metrics_store = MetricsStore()
