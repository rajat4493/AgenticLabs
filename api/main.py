from providers import ollama_adapter as provider_stub
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Any, Dict
import time

from shared.models import RunRequest, RunResponse, Provenance, PolicyEvaluation, AuditInfo, MetricsInfo, MetricsSnapshot
#from providers import stub as provider_stub
from router import new_run_id, compute_alri_tag, evaluate_policy
from analytics.store import metrics_store
from logger import log_event

app = FastAPI(title="AgenticLabs API", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True, "service": "agenticlabs-api"}

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(payload: RunRequest):
    t0 = time.time()
    rid = new_run_id()

    # Router: (schema already validated by Pydantic)
    log_event("router_in", {"run_id": rid, "agent_id": payload.agent_id})

    # Planner (stub provider)
    plan = provider_stub.plan(payload.model_dump())
    log_event("route_plan", {"run_id": rid, "plan": plan})

    # Execute
    result = provider_stub.execute(plan, payload.prompt)
    log_event("provider_out", {"run_id": rid, "latency_ms": result["latency_ms"], "cost_usd": result["cost_usd"]})

    # Policy evaluation (confidence threshold can be overridden later)
    threshold = 0.7
    if payload.policy_overrides and isinstance(payload.policy_overrides.get("confidence_threshold"), (int, float)):
        threshold = float(payload.policy_overrides["confidence_threshold"])

    pol = evaluate_policy(result["confidence"], threshold)

    # ALRI retention tag (placeholder)
    ctx = payload.context or {}
    alri_tag = compute_alri_tag(ctx.get("risk_band"), ctx.get("jurisdiction"))

    # Record metrics
    metrics_store.record(result["latency_ms"], result["cost_usd"])

    # Compose response
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
