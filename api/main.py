import os
import time
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from shared.models import (
    AuditInfo,
    MetricsInfo,
    RunRequest,
    RunResponse,
    Provenance,
    PolicyEvaluation,
)
from router import compute_alri_tag, evaluate_policy, new_run_id
from router.complexity import choose_band, score_complexity
from logger import log_event
from providers import PROVIDERS
from pricing import calc_baseline_cost
from governance.alri import compute_alri_v2
from routes import logs
from db.models import Base
from db.router_runs_repo import get_summary, list_runs as list_runs_repo, log_run
from db.session import engine, get_db


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default

# ---- Band-based routing config ----
# Defaults are OpenAI; can be overridden via env vars.
BAND_ROUTING = {
    "simple": {
        "provider": _env("PROVIDER_SIMPLE", _env("PROVIDER_DEFAULT", "openai")).lower(),
        "model": _env("MODEL_SIMPLE", "gpt-4o-mini"),
    },
    "moderate": {
        "provider": _env("PROVIDER_MODERATE", _env("PROVIDER_DEFAULT", "openai")).lower(),
        "model": _env("MODEL_MODERATE", "gpt-4o"),
    },
    "complex": {
        "provider": _env("PROVIDER_COMPLEX", _env("PROVIDER_DEFAULT", "openai")).lower(),
        "model": _env("MODEL_COMPLEX", "gpt-4o"),
    },
}

app = FastAPI(title="AgenticLabs API", version="0.1.2")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)

@app.get("/v1/metrics/summary")
def metrics_summary(db: Session = Depends(get_db)):
    """
    Aggregate router metrics for the dashboard.
    """
    summary = get_summary(db)
    return JSONResponse(summary)

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "agenticlabs-api",
        "routing": BAND_ROUTING,
    }

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(payload: RunRequest, db: Session = Depends(get_db)):
    rid = new_run_id()
    t_start = time.perf_counter()
    log_event("router_in", {"run_id": rid, "agent_id": payload.agent_id})

    # ---- Smart routing (with manual override) ----
    cscore = score_complexity(payload.prompt)
    cband = choose_band(cscore)

    force_model = None
    force_band = None
    if payload.policy_overrides:
        force_model = payload.policy_overrides.get("force_model")
        force_band = payload.policy_overrides.get("force_band")

    if force_band in {"simple", "moderate", "complex"}:
        cband = force_band

    route_cfg = BAND_ROUTING.get(cband) or BAND_ROUTING["moderate"]
    provider_name = route_cfg["provider"]
    model_name = force_model or route_cfg["model"]

    if provider_name not in PROVIDERS:
        provider_name = "openai"

    provider_impl = PROVIDERS.get(provider_name)
    if provider_impl is None:
        raise ValueError(f"Provider '{provider_name}' is not configured")

    log_event("route_complexity", {
        "run_id": rid,
        "score": round(cscore, 3),
        "band": cband,
        "provider": provider_name,
        "model": model_name,
        "force_model": bool(force_model),
        "force_band": bool(force_band)
    })

    # ---- Plan + Execute ----
    plan = provider_impl.plan(payload.model_dump(), model_name=model_name)
    log_event("route_plan", {"run_id": rid, "plan": plan})
    t_router_done = time.perf_counter()

    t_provider_start = time.perf_counter()
    result = provider_impl.execute(plan, payload.prompt)
    t_provider_end = time.perf_counter()
    log_event("provider_out", {
        "run_id": rid,
        "latency_ms": result["latency_ms"],
        "cost_usd": result["cost_usd"]
    })

    # ---- Policy evaluation ----
    threshold = 0.7
    if payload.policy_overrides and isinstance(payload.policy_overrides.get("confidence_threshold"), (int, float)):
        threshold = float(payload.policy_overrides["confidence_threshold"])
    pol = evaluate_policy(result["confidence"], threshold)

    # ---- ALRI tag ----
    ctx = payload.context or {}
    alri_tag = compute_alri_tag(ctx.get("risk_band"), ctx.get("jurisdiction"))

    # ---- Metrics ----
    prompt_tokens = result.get("prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = (result.get("provenance") or {}).get("input_tokens", 0)
    completion_tokens = result.get("completion_tokens")
    if completion_tokens is None:
        completion_tokens = (result.get("provenance") or {}).get("output_tokens", 0)

    if prompt_tokens or completion_tokens:
        baseline_cost = calc_baseline_cost(
            int(prompt_tokens or 0),
            int(completion_tokens or 0),
            baseline_model="gpt-4o",
        )
    else:
        baseline_cost = result["cost_usd"]

    overrides_obj = payload.policy_overrides or {}
    overrides_used = bool(
        overrides_obj.get("force_provider")
        or overrides_obj.get("force_model")
        or overrides_obj.get("force_band")
    )

    alri_score, alri_tier = compute_alri_v2(
        band=cband,
        provider=provider_name,
        model=model_name,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        overrides_used=overrides_used,
    )

    t_done = time.perf_counter()
    total_latency_ms = (t_done - t_start) * 1000.0
    router_latency_ms = (t_router_done - t_start) * 1000.0
    provider_latency_ms = (t_provider_end - t_provider_start) * 1000.0
    processing_latency_ms = max(
        0.0, total_latency_ms - router_latency_ms - provider_latency_ms
    )

    log_run(
        db,

        band=cband,
        provider=provider_name,
        model=model_name,
        latency_ms=total_latency_ms,
        router_latency_ms=router_latency_ms,
        provider_latency_ms=provider_latency_ms,
        processing_latency_ms=processing_latency_ms,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        alri_score=alri_score,
        alri_tier=alri_tier,
    )

    # ---- Response ----
    resp = RunResponse(
        run_id=rid,
        status="ok" if not pol["hil_triggered"] else "hil_required",
        output=result["output"],
        confidence=result["confidence"],
        provenance=Provenance(**result["provenance"]),
        policy_evaluation=PolicyEvaluation(**pol),
        metrics=MetricsInfo(latency_ms=int(total_latency_ms), cost_usd=result["cost_usd"]),
        audit=AuditInfo(retention_class=alri_tag, audit_hash=None)
    )

    log_event("router_out", {"run_id": rid, "status": resp.status})
    return JSONResponse(resp.model_dump())
