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
from router.rule_based import PROVIDER_DEFAULT_MODELS, SelectedModel, select_model
from router.routing_rules import load_routing_rules
from router.model_registry import NAIVE_BASELINE_MODEL_KEY
from router.routing_bands import RoutingBand
from logger import log_event
from providers import PROVIDERS
from costs import compute_costs
from governance.alri import compute_alri_v2
from routes import logs, metrics
from db.models import Base
from db.router_runs_repo import get_summary, list_runs as list_runs_repo, log_run
from db.session import engine, get_db
from config.router import RouterMode
from config.model_registry import MODEL_REGISTRY
from cost.calculator import calculate_cost, resolve_model_key
from deps import get_router_mode_dep, get_tenant_dep
from models.tenant import Tenant
from routing.categories import classify_query, QueryCategory
from routing.scoring import choose_enhanced_model
from pricing import estimate_cost_for_model

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
app.include_router(metrics.router)

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
        "routing_rules": load_routing_rules(),
    }

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(
    payload: RunRequest,
    db: Session = Depends(get_db),
    router_mode: RouterMode = Depends(get_router_mode_dep),
    tenant: Tenant = Depends(get_tenant_dep),
):
    if payload.router_mode:
        try:
            router_mode = RouterMode(payload.router_mode.lower())
        except ValueError:
            router_mode = router_mode
    rid = new_run_id()
    t_start = time.perf_counter()
    log_event(
        "router_in",
        {"run_id": rid, "agent_id": payload.agent_id, "router_mode": router_mode.value},
    )

    # ---- Smart routing (with manual override) ----
    cscore = score_complexity(payload.prompt)
    inferred_band_raw = choose_band(cscore, payload.prompt)
    inferred_band = RoutingBand.normalize(inferred_band_raw).value

    overrides = payload.policy_overrides or {}
    force_model = payload.force_model or overrides.get("force_model")
    force_provider = payload.force_provider or overrides.get("force_provider")
    force_band = payload.force_band or overrides.get("force_band")

    def canonical_band(value: str | None) -> str:
        return RoutingBand.normalize(value).value

    requested_band = canonical_band(payload.band or inferred_band)
    if isinstance(force_band, str) and force_band:
        requested_band = canonical_band(force_band)

    task_type = payload.task_type

    default_selection: SelectedModel = select_model(
        band=inferred_band,
        task_type=task_type,
    )

    selected: SelectedModel = select_model(
        band=requested_band,
        task_type=task_type,
        force_provider=force_provider,
        force_model=force_model,
    )
    category, category_conf = classify_query(payload.prompt)

    provider_name = selected.provider
    model_name = selected.model
    resolved_band = selected.band
    selection_source = selected.route_source

    allowed_keys = tenant.allowed_models or list(MODEL_REGISTRY.keys())

    if router_mode == RouterMode.ENHANCED:
        choice = choose_enhanced_model(
            category=category,
            allowed_model_keys=allowed_keys,
            resolved_band=resolved_band,
        )
        if choice:
            provider_name = choice.provider
            model_name = choice.model_id
            selection_source = "enhanced"

    final_key = f"{provider_name}:{model_name}"
    if allowed_keys and final_key not in allowed_keys:
        fallback_choice = choose_enhanced_model(
            category=category,
            allowed_model_keys=allowed_keys,
            resolved_band=resolved_band,
        )
        if fallback_choice:
            provider_name = fallback_choice.provider
            model_name = fallback_choice.model_id
            selection_source = "enhanced"

    if provider_name not in PROVIDERS:
        provider_name = "openai"
        model_name = PROVIDER_DEFAULT_MODELS.get(provider_name, model_name)

    provider_impl = PROVIDERS.get(provider_name)
    if provider_impl is None:
        raise ValueError(f"Provider '{provider_name}' is not configured")

    log_event("route_complexity", {
        "run_id": rid,
        "score": round(cscore, 3),
        "band": resolved_band,
        "inferred_band": inferred_band,
        "provider": provider_name,
        "model": model_name,
        "force_model": bool(force_model),
        "force_band": bool(force_band),
        "force_provider": bool(force_provider),
        "route_source": selection_source,
        "category": category.value,
        "category_confidence": category_conf,
    })

    # ---- Plan + Execute ----
    plan = provider_impl.plan(payload.model_dump(), model_name=model_name)
    log_event("route_plan", {"run_id": rid, "plan": plan})
    t_router_done = time.perf_counter()

    t_provider_start = time.perf_counter()
    result = provider_impl.execute(plan, payload.prompt)
    t_provider_end = time.perf_counter()

    prompt_tokens = result.get("prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = (result.get("provenance") or {}).get("input_tokens", 0)
    completion_tokens = result.get("completion_tokens")
    if completion_tokens is None:
        completion_tokens = (result.get("provenance") or {}).get("output_tokens", 0)

    prompt_tokens = int(prompt_tokens or 0)
    completion_tokens = int(completion_tokens or 0)

    model_key = resolve_model_key(provider_name, model_name) or f"{provider_name}:{model_name}"
    cost_usd = calculate_cost(
        model_key=model_key,
        provider=provider_name,
        model=model_name,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if cost_usd <= 0:
        legacy_cost, _ = compute_costs(
            provider=provider_name,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        if legacy_cost and legacy_cost > 0:
            cost_usd = legacy_cost
        else:
            cost_usd = float(result.get("cost_usd", 0.0) or 0.0)

    baseline_cost = calculate_cost(
        model_key=NAIVE_BASELINE_MODEL_KEY,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if baseline_cost <= 0:
        _, legacy_baseline = compute_costs(
            provider=provider_name,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        baseline_cost = legacy_baseline or cost_usd
    cost_usd = float(cost_usd or 0.0)
    baseline_cost = float(baseline_cost or cost_usd)

    result["cost_usd"] = cost_usd

    log_event("provider_out", {
        "run_id": rid,
        "latency_ms": result["latency_ms"],
        "cost_usd": cost_usd,
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
    overrides_used = selected.route_source == "manual_override"

    run_status = "ok" if not pol["hil_triggered"] else "hil_required"

    alri_score, alri_tier = compute_alri_v2(
        band=selected.band,
        provider=provider_name,
        model=model_name,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        overrides_used=overrides_used,
        prompt_text=payload.prompt,
    )

    t_done = time.perf_counter()
    total_latency_ms = (t_done - t_start) * 1000.0
    router_latency_ms = (t_router_done - t_start) * 1000.0
    provider_latency_ms = (t_provider_end - t_provider_start) * 1000.0
    processing_latency_ms = max(
        0.0, total_latency_ms - router_latency_ms - provider_latency_ms
    )

    # Routing efficiency: compare against default selection cost
    default_model_key = resolve_model_key(
        default_selection.provider, default_selection.model
    ) or f"{default_selection.provider}:{default_selection.model}"
    default_cost = calculate_cost(
        model_key=default_model_key,
        provider=default_selection.provider,
        model=default_selection.model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if default_cost <= 0:
        legacy_default_cost, _ = compute_costs(
            provider=default_selection.provider,
            model=default_selection.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        default_cost = legacy_default_cost
    default_cost = float(default_cost or 0.0)
    epsilon = 0.02
    routing_efficient = False
    if default_cost > 0:
        routing_efficient = cost_usd <= (default_cost * (1 + epsilon))
    else:
        routing_efficient = True

    what_if_cost_usd = estimate_cost_for_model(
        "gpt-4.1",
        prompt_tokens,
        category,
    )

    log_run(
        db,

        band=resolved_band,
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
        status=run_status,
        routing_efficient=routing_efficient,
        query_category=category.value,
        query_category_conf=category_conf,
        counterfactual_cost_usd=what_if_cost_usd,
    )

    # ---- Response ----
    provenance = result.get("provenance") or {}
    provenance.update(
        {
            "provider": provider_name,
            "model": model_name,
            "route_source": selection_source,
        }
    )
    result["provenance"] = provenance

    resp = RunResponse(
        run_id=rid,
        status=run_status,
        output=result["output"],
        confidence=result["confidence"],
        provenance=Provenance(**result["provenance"]),
        policy_evaluation=PolicyEvaluation(**pol),
        metrics=MetricsInfo(latency_ms=int(total_latency_ms), cost_usd=result["cost_usd"]),
        audit=AuditInfo(retention_class=alri_tag, audit_hash=None),
        query_category=category.value,
        query_category_conf=category_conf,
    )

    log_event("router_out", {"run_id": rid, "status": resp.status})
    return JSONResponse(resp.model_dump())
