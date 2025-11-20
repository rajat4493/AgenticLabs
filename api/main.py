import os
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from shared.models import (
    RunRequest, RunResponse, Provenance, PolicyEvaluation,
    AuditInfo, MetricsInfo, MetricsSnapshot
)
from router import new_run_id, compute_alri_tag, evaluate_policy
from router.complexity import score_complexity, choose_band
from analytics.store import metrics_store
from logger import log_event

# ---- Provider selection ----
PROVIDER = os.getenv("PROVIDER", "ollama").lower()
if PROVIDER == "ollama":
    from providers import ollama_adapter as provider_impl
else:
    from providers import stub as provider_impl

# ---- Model mapping by complexity band ----
MODEL_BY_BAND = {
    "simple":  os.getenv("MODEL_SIMPLE",  "llama3"),
    "moderate":os.getenv("MODEL_MODERATE","qwen2:7b-instruct"),
    "complex": os.getenv("MODEL_COMPLEX","qwen2:7b-instruct"),
}

app = FastAPI(title="AgenticLabs API", version="0.1.2")

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "agenticlabs-api",
        "provider": PROVIDER,
        "models": MODEL_BY_BAND
    }

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(payload: RunRequest):
    rid = new_run_id()
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

    chosen_model = force_model or MODEL_BY_BAND.get(cband) or MODEL_BY_BAND["moderate"]

    log_event("route_complexity", {
        "run_id": rid,
        "score": round(cscore, 3),
        "band": cband,
        "model": chosen_model,
        "force_model": bool(force_model),
        "force_band": bool(force_band)
    })

    # ---- Plan + Execute ----
    plan = provider_impl.plan(payload.model_dump(), model_name=chosen_model)
    log_event("route_plan", {"run_id": rid, "plan": plan})

    result = provider_impl.execute(plan, payload.prompt)
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
    metrics_store.record(result["latency_ms"], result["cost_usd"])

    # ---- Response ----
    resp = RunResponse(
        run_id=rid,
        status="ok" if not pol["hil_triggered"] else "hil_required",
        output=result["output"],
        confidence=result["confidence"],
        provenance=Provenance(**result["provenance"]),
        policy_evaluation=PolicyEvaluation(**pol),
        metrics=MetricsInfo(latency_ms=result["latency_ms"], cost_usd=result["cost_usd"]),
        audit=AuditInfo(retention_class=alri_tag, audit_hash=None)
    )

    log_event("router_out", {"run_id": rid, "status": resp.status})
    return JSONResponse(resp.model_dump())

@app.get("/v1/metrics", response_model=MetricsSnapshot)
def metrics():
    snap = metrics_store.snapshot()
    return JSONResponse(snap)
