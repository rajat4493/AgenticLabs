from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from analytics.aggregate_overview import aggregate_overview_costs
from analytics.aggregate_analytics import aggregate_analytics_costs
from db.models import RouterRun
from db.session import get_db
from shared.metrics import (
    OverviewSummary,
    ProviderBreakdownItem,
    ProviderBreakdownResponse,
    TimeseriesPoint,
    TimeseriesResponse,
    SavingsPoint,
    SavingsTrendResponse,
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
)

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/overview", response_model=OverviewSummary)
def get_overview_summary(
    window_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
) -> OverviewSummary:
    """
    Aggregate metrics for the Overview dashboard within the provided window.
    """

    since = datetime.utcnow() - timedelta(hours=window_hours)

    total_runs, avg_latency = (
        db.query(
            func.count(RouterRun.id),
            func.avg(RouterRun.latency_ms),
        )
        .filter(RouterRun.created_at >= since)
        .one()
    )

    total_runs = total_runs or 0
    avg_latency = float(avg_latency or 0.0)

    cost_rows = (
        db.query(
            RouterRun.band,
            RouterRun.prompt_tokens,
            RouterRun.completion_tokens,
            RouterRun.cost_usd,
        )
        .filter(RouterRun.created_at >= since)
        .all()
    )
    overview_costs = aggregate_overview_costs(cost_rows)
    total_cost = float(overview_costs["total_actual_cost"] or 0.0)

    cost_per_run = float(total_cost / total_runs) if total_runs > 0 else 0.0

    baseline_total = (
        float(overview_costs["total_naive_baseline_cost"] or 0.0)
        if total_runs
        else None
    )
    savings_abs = overview_costs["savings_abs"] if total_runs else None
    savings_pct = overview_costs["savings_pct"] if total_runs else None

    return OverviewSummary(
        total_runs=total_runs,
        avg_latency_ms=avg_latency,
        total_cost_usd=total_cost,
        cost_per_run_usd=cost_per_run,
        baseline_total_cost_usd=baseline_total,
        savings_vs_baseline_usd=savings_abs,
        savings_vs_baseline_pct=savings_pct,
    )


@router.get("/savings")
def get_savings_overview(
    window_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """
    Savings vs baseline within a rolling window.
    """
    since = datetime.utcnow() - timedelta(hours=window_hours)
    runs = (
        db.query(
            RouterRun.band,
            RouterRun.prompt_tokens,
            RouterRun.completion_tokens,
            RouterRun.cost_usd,
        )
        .filter(RouterRun.created_at >= since)
        .all()
    )

    stats = aggregate_analytics_costs(runs)
    actual_cost = float(stats["total_actual_cost"] or 0.0)
    baseline_cost = float(stats["total_band_baseline_cost"] or 0.0)
    savings = float(stats["savings_band_abs"] or 0.0)
    savings_pct = float(stats["savings_band_pct"] or 0.0)
    projected_monthly = savings * 30.0

    return {
        "actual_cost": actual_cost,
        "baseline_cost": baseline_cost,
        "savings_usd": savings,
        "savings_pct": savings_pct,
        "projected_monthly_savings": projected_monthly,
        "message": stats.get("message"),
    }


@router.get("/savings/timeseries", response_model=SavingsTrendResponse)
def get_savings_timeseries(
    window_hours: int = Query(168, ge=1, le=2160),
    bucket: str = Query("day", regex="^(day|hour)$"),
    db: Session = Depends(get_db),
) -> SavingsTrendResponse:
    since = datetime.utcnow() - timedelta(hours=window_hours)
    bucket_expr = func.date_trunc(bucket, RouterRun.created_at)

    rows = (
        db.query(
            bucket_expr.label("bucket"),
            func.coalesce(func.sum(RouterRun.cost_usd), 0.0).label("actual"),
            func.coalesce(func.sum(RouterRun.baseline_cost_usd), 0.0).label(
                "baseline"
            ),
        )
        .filter(RouterRun.created_at >= since)
        .group_by(bucket_expr)
        .order_by(bucket_expr)
        .all()
    )

    cumulative = 0.0
    points: list[SavingsPoint] = []
    for row in rows:
        actual = float(row.actual or 0.0)
        baseline = float(row.baseline or 0.0)
        savings = baseline - actual
        cumulative += savings
        points.append(
            SavingsPoint(
                timestamp=row.bucket,
                actual_cost=actual,
                baseline_cost=baseline,
                savings_usd=savings,
                cumulative_savings=cumulative,
            )
        )

    return SavingsTrendResponse(
        window_hours=window_hours,
        bucket=bucket,
        points=points,
    )


@router.get("/efficiency")
def routing_efficiency(
    window_hours: int = Query(168, ge=1, le=2160),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=window_hours)
    prev_since = since - timedelta(hours=window_hours)

    current_total, current_hits = (
        db.query(
            func.count(RouterRun.id),
            func.coalesce(
                func.sum(case((RouterRun.routing_efficient.is_(True), 1), else_=0)),
                0,
            ),
        )
        .filter(RouterRun.created_at >= since)
        .one()
    )

    prev_total, prev_hits = (
        db.query(
            func.count(RouterRun.id),
            func.coalesce(
                func.sum(case((RouterRun.routing_efficient.is_(True), 1), else_=0)),
                0,
            ),
        )
        .filter(RouterRun.created_at >= prev_since)
        .filter(RouterRun.created_at < since)
        .one()
    )

    current_pct = (current_hits / current_total * 100.0) if current_total else 0.0
    prev_pct = (prev_hits / prev_total * 100.0) if prev_total else 0.0
    delta_pct = current_pct - prev_pct if prev_total else None

    return {
        "window_hours": window_hours,
        "efficiency_pct": current_pct,
        "delta_pct": delta_pct,
        "total_runs": current_total,
    }


@router.get("/providers", response_model=ProviderBreakdownResponse)
def get_provider_breakdown(
    window_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
) -> ProviderBreakdownResponse:
    """
    Aggregate metrics by provider for dashboard breakdowns.
    """

    since = datetime.utcnow() - timedelta(hours=window_hours)

    total_runs, total_cost = (
        db.query(
            func.count(RouterRun.id),
            func.sum(RouterRun.cost_usd),
        )
        .filter(RouterRun.created_at >= since)
        .one()
    )

    total_runs = total_runs or 0
    total_cost = float(total_cost or 0.0)

    rows = (
        db.query(
            RouterRun.provider,
            func.count(RouterRun.id).label("runs"),
            func.sum(RouterRun.cost_usd).label("cost"),
            func.avg(RouterRun.latency_ms).label("avg_latency"),
            func.sum(RouterRun.prompt_tokens + RouterRun.completion_tokens).label("tokens"),
            func.sum(
                case(
                    (
                        RouterRun.alri_tier.in_(["orange_high", "red_critical"]),
                        1,
                    ),
                    else_=0,
                )
            ).label("high_risk_runs"),
            func.sum(
                case((RouterRun.band == "low", 1), else_=0)
            ).label("band_low_runs"),
            func.sum(
                case((RouterRun.band == "medium", 1), else_=0)
            ).label("band_medium_runs"),
            func.sum(
                case((RouterRun.band == "high", 1), else_=0)
            ).label("band_high_runs"),
        )
        .filter(RouterRun.created_at >= since)
        .group_by(RouterRun.provider)
        .all()
    )

    items: list[ProviderBreakdownItem] = []
    for (
        provider,
        runs,
        cost,
        avg_latency,
        tokens,
        high_risk_runs,
        band_low_runs,
        band_medium_runs,
        band_high_runs,
    ) in rows:
        runs = runs or 0
        cost = float(cost or 0.0)
        avg_latency = float(avg_latency or 0.0)
        tokens = int(tokens or 0)
        high_risk_runs = int(high_risk_runs or 0)
        band_low_runs = int(band_low_runs or 0)
        band_medium_runs = int(band_medium_runs or 0)
        band_high_runs = int(band_high_runs or 0)
        avg_cost_per_run = cost / runs if runs > 0 else 0.0
        cost_share_pct = (cost / total_cost * 100.0) if total_cost > 0 else 0.0
        cost_per_1k_tokens = (cost / (tokens / 1000.0)) if tokens > 0 else None
        high_risk_pct = (high_risk_runs / runs * 100.0) if runs > 0 else 0.0
        band_low_pct = (band_low_runs / runs * 100.0) if runs > 0 else 0.0
        band_medium_pct = (band_medium_runs / runs * 100.0) if runs > 0 else 0.0
        band_high_pct = (band_high_runs / runs * 100.0) if runs > 0 else 0.0

        items.append(
            ProviderBreakdownItem(
                provider=provider or "unknown",
                total_runs=runs,
                total_cost_usd=cost,
                avg_cost_per_run_usd=avg_cost_per_run,
                cost_share_pct=cost_share_pct,
                avg_latency_ms=avg_latency,
                total_tokens=tokens,
                cost_per_1k_tokens_usd=cost_per_1k_tokens,
                high_risk_pct=high_risk_pct,
                band_low_pct=band_low_pct,
                band_medium_pct=band_medium_pct,
                band_high_pct=band_high_pct,
            )
        )

    return ProviderBreakdownResponse(
        window_hours=window_hours,
        total_runs=total_runs,
        total_cost_usd=total_cost,
        items=items,
    )


@router.get("/categories", response_model=CategoryBreakdownResponse)
def get_category_distribution(
    window_hours: int = Query(168, ge=1, le=2160),
    db: Session = Depends(get_db),
) -> CategoryBreakdownResponse:
    since = datetime.utcnow() - timedelta(hours=window_hours)
    total_runs = (
        db.query(func.count(RouterRun.id))
        .filter(RouterRun.created_at >= since)
        .scalar()
        or 0
    )

    rows = (
        db.query(
            RouterRun.query_category,
            func.count(RouterRun.id).label("runs"),
        )
        .filter(RouterRun.created_at >= since)
        .group_by(RouterRun.query_category)
        .order_by(func.count(RouterRun.id).desc())
        .all()
    )

    items: list[CategoryBreakdownItem] = []
    for category, runs in rows:
        cat = category or "unknown"
        pct = (runs / total_runs * 100.0) if total_runs else 0.0
        items.append(
            CategoryBreakdownItem(
                category=cat,
                runs=runs,
                pct=pct,
            )
        )

    return CategoryBreakdownResponse(
        window_hours=window_hours,
        total_runs=total_runs,
        items=items,
    )


@router.get("/timeseries", response_model=TimeseriesResponse)
def get_timeseries(
    metric: str = Query(..., regex="^(cost|requests|tokens|alri)$"),
    window_hours: int = Query(24, ge=1, le=720),
    bucket: str = Query("hour", regex="^(hour|day)$"),
    provider: str | None = Query(None),
    band: str | None = Query(None, regex="^(low|medium|high)$"),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> TimeseriesResponse:
    """
    Analytics-friendly timeseries endpoint with optional filters.
    """

    since = datetime.utcnow() - timedelta(hours=window_hours)
    bucket_expr = func.date_trunc(bucket, RouterRun.created_at)

    if metric == "cost":
        value_expr = func.sum(RouterRun.cost_usd)
    elif metric == "requests":
        value_expr = func.count(RouterRun.id)
    elif metric == "tokens":
        value_expr = func.sum(RouterRun.prompt_tokens + RouterRun.completion_tokens)
    elif metric == "alri":
        value_expr = func.avg(RouterRun.alri_score)
    else:
        raise ValueError("Unsupported metric")

    query = (
        db.query(bucket_expr.label("bucket"), value_expr.label("value"))
        .filter(RouterRun.created_at >= since)
    )

    if provider:
        query = query.filter(RouterRun.provider == provider)
    if band:
        query = query.filter(RouterRun.band == band)
    if status:
        query = query.filter(RouterRun.status == status)

    rows = query.group_by(bucket_expr).order_by(bucket_expr).all()

    points = [
        TimeseriesPoint(timestamp=row.bucket, value=float(row.value or 0.0))
        for row in rows
    ]

    return TimeseriesResponse(
        metric=metric,
        bucket=bucket,
        window_hours=window_hours,
        points=points,
    )
