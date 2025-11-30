from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional


class OverviewSummary(BaseModel):
    total_runs: int
    avg_latency_ms: float
    total_cost_usd: float
    cost_per_run_usd: float
    baseline_total_cost_usd: Optional[float] = None
    savings_vs_baseline_usd: Optional[float] = None
    savings_vs_baseline_pct: Optional[float] = None
    what_if_cost_usd: Optional[float] = None
    what_if_vs_actual_usd: Optional[float] = None


class ProviderBreakdownItem(BaseModel):
    provider: str
    total_runs: int
    total_cost_usd: float
    avg_cost_per_run_usd: float
    cost_share_pct: float
    avg_latency_ms: float
    total_tokens: int
    cost_per_1k_tokens_usd: Optional[float] = None
    high_risk_pct: Optional[float] = None
    band_low_pct: Optional[float] = None
    band_medium_pct: Optional[float] = None
    band_high_pct: Optional[float] = None


class ProviderBreakdownResponse(BaseModel):
    window_hours: int
    total_runs: int
    total_cost_usd: float
    items: List[ProviderBreakdownItem]


class TimeseriesPoint(BaseModel):
    timestamp: datetime
    value: float


class TimeseriesResponse(BaseModel):
    metric: str
    bucket: str
    window_hours: int
    points: List[TimeseriesPoint]


class SavingsPoint(BaseModel):
    timestamp: datetime
    actual_cost: float
    baseline_cost: float
    savings_usd: float
    cumulative_savings: float


class SavingsTrendResponse(BaseModel):
    window_hours: int
    bucket: str
    points: List[SavingsPoint]


class CategoryBreakdownItem(BaseModel):
    category: str
    runs: int
    pct: float


class CategoryBreakdownResponse(BaseModel):
    window_hours: int
    total_runs: int
    items: List[CategoryBreakdownItem]


__all__ = [
    "OverviewSummary",
    "ProviderBreakdownItem",
    "ProviderBreakdownResponse",
    "TimeseriesPoint",
    "TimeseriesResponse",
    "SavingsPoint",
    "SavingsTrendResponse",
    "CategoryBreakdownItem",
    "CategoryBreakdownResponse",
]
