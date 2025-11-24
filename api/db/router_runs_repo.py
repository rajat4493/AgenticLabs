from typing import Any, Dict, List

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .models import RouterRun


def log_run(
    db: Session,
    *,
    band: str,
    provider: str,
    model: str,
    latency_ms: float,
    router_latency_ms: float | None = None,
    provider_latency_ms: float | None = None,
    processing_latency_ms: float | None = None,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    baseline_cost_usd: float,
    alri_score: float | None = None,
    alri_tier: str | None = None,
) -> RouterRun:
    savings_usd = baseline_cost_usd - cost_usd
    run = RouterRun(
        band=band,
        provider=provider,
        model=model,
        latency_ms=latency_ms,
        router_latency_ms=router_latency_ms,
        provider_latency_ms=provider_latency_ms,
        processing_latency_ms=processing_latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        baseline_cost_usd=baseline_cost_usd,
        savings_usd=savings_usd,
        alri_score=alri_score,
        alri_tier=alri_tier,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_summary(db: Session) -> Dict[str, Any]:
    base = db.query(RouterRun)
    total_runs = base.count()
    total_cost = (
        base.with_entities(func.coalesce(func.sum(RouterRun.cost_usd), 0.0)).scalar()
        or 0.0
    )
    avg_latency = (
        base.with_entities(func.coalesce(func.avg(RouterRun.latency_ms), 0.0)).scalar()
        or 0.0
    )
    baseline_cost = (
        base.with_entities(func.coalesce(func.sum(RouterRun.baseline_cost_usd), 0.0)).scalar()
        or 0.0
    )
    savings = baseline_cost - total_cost
    savings_pct = (savings / baseline_cost * 100.0) if baseline_cost > 0 else None
    cost_per_run = (total_cost / total_runs) if total_runs > 0 else 0.0

    provider_rows = (
        base.with_entities(
            RouterRun.provider.label("provider"),
            func.count(RouterRun.id).label("runs"),
            func.coalesce(func.sum(RouterRun.cost_usd), 0.0).label("total_cost"),
            func.coalesce(func.avg(RouterRun.latency_ms), 0.0).label("avg_latency"),
        )
        .group_by(RouterRun.provider)
        .all()
    )
    provider_breakdown = [
        {
            "provider": row.provider,
            "runs": row.runs,
            "total_cost_usd": row.total_cost,
            "avg_latency_ms": row.avg_latency,
        }
        for row in provider_rows
    ]

    timeseries_rows = (
        base.with_entities(
            func.date_trunc("day", RouterRun.created_at).label("day"),
            func.count(RouterRun.id).label("requests"),
            func.coalesce(func.sum(RouterRun.cost_usd), 0.0).label("cost_usd"),
        )
        .group_by(func.date_trunc("day", RouterRun.created_at))
        .order_by(func.date_trunc("day", RouterRun.created_at))
        .all()
    )
    timeseries = [
        {
            "date": row.day.date().isoformat(),
            "requests": row.requests,
            "cost_usd": row.cost_usd,
        }
        for row in timeseries_rows
    ]

    avg_alri = base.with_entities(func.avg(RouterRun.alri_score)).scalar()
    avg_alri = float(avg_alri) if avg_alri is not None else None

    high_tiers = ["long_365d_full", "immutable_7y_full"]
    high_risk = (
        base.with_entities(func.count(RouterRun.id))
        .filter(RouterRun.alri_tier.in_(high_tiers))
        .scalar()
        or 0
    )
    high_risk_pct = (high_risk / total_runs * 100.0) if total_runs else 0.0

    return {
        "total_runs": total_runs,
        "avg_latency_ms": avg_latency,
        "total_cost_usd": total_cost,
        "cost_per_run_usd": cost_per_run,
        "baseline_cost_usd": baseline_cost if total_runs else None,
        "savings_vs_baseline_usd": savings if total_runs else None,
        "savings_pct": savings_pct,
        "provider_breakdown": provider_breakdown,
        "timeseries": timeseries,
        "avg_alri_score": avg_alri,
        "high_alri_run_pct": high_risk_pct,
    }


def list_runs(db: Session, *, offset: int, limit: int) -> Dict[str, Any]:
    base = db.query(RouterRun)
    total = base.count()
    rows: List[RouterRun] = (
        base.order_by(desc(RouterRun.created_at)).offset(offset).limit(limit).all()
    )

    items = [
        {
            "id": row.id,
            "timestamp": row.created_at.timestamp(),
            "band": row.band,
            "provider": row.provider,
            "model": row.model,
            "latency_ms": row.latency_ms,
            "router_latency_ms": row.router_latency_ms,
            "provider_latency_ms": row.provider_latency_ms,
            "processing_latency_ms": row.processing_latency_ms,
            "prompt_tokens": row.prompt_tokens,
            "completion_tokens": row.completion_tokens,
            "cost_usd": row.cost_usd,
            "baseline_cost_usd": row.baseline_cost_usd,
            "savings_usd": row.savings_usd,
            "alri_score": row.alri_score,
            "alri_tier": row.alri_tier,
        }
        for row in rows
    ]

    return {"total": total, "offset": offset, "limit": limit, "items": items}
