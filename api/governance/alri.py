from __future__ import annotations

from typing import Optional, Tuple


def compute_alri_v2(
    *,
    band: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    baseline_cost_usd: float,
    overrides_used: bool = False,
    governance_level: Optional[int] = None,
    business_impact_level: Optional[int] = None,
    safety_flag_level: Optional[int] = None,
) -> Tuple[float, str]:
    """Compute ALRI v2 score (0-10) and retention tier."""
    if baseline_cost_usd <= 0:
        r = 0.0
    else:
        r = cost_usd / baseline_cost_usd
    if r <= 0.25:
        C = 0
    elif r <= 0.75:
        C = 1
    elif r <= 1.25:
        C = 2
    else:
        C = 3

    band_lower = (band or "").lower()
    if band_lower == "simple":
        X_base = 0
    elif band_lower == "moderate":
        X_base = 1
    elif band_lower == "complex":
        X_base = 2
    else:
        X_base = 1
    X = min(3, X_base)

    if governance_level is not None:
        G = max(0, min(3, governance_level))
    else:
        if provider == "ollama" and band_lower == "simple":
            G = 0
        elif provider == "ollama":
            G = 1
        elif provider == "openai" and band_lower == "simple":
            G = 1
        elif provider == "openai" and band_lower == "moderate":
            G = 2
        else:
            G = 3

    if safety_flag_level is not None:
        S_base = max(0, min(3, safety_flag_level))
    else:
        S_base = 0
    override_bonus = 1 if overrides_used else 0
    S = min(3, S_base + override_bonus)

    if business_impact_level is not None:
        B = max(0, min(3, business_impact_level))
    else:
        if band_lower == "complex" and provider == "openai":
            B = 2
        elif band_lower == "moderate":
            B = 1
        else:
            B = 0

    wC, wX, wG, wS, wB = 1.0, 1.0, 1.5, 1.5, 2.0
    alri_raw = wC * C + wX * X + wG * G + wS * S + wB * B
    alri_score = max(0.0, min(10.0, round((alri_raw / 21.0) * 10.0, 1)))

    if alri_score <= 2.5:
        alri_tier = "green_low"
    elif alri_score <= 5.0:
        alri_tier = "yellow_medium"
    elif alri_score <= 7.5:
        alri_tier = "orange_high"
    else:
        alri_tier = "red_critical"

    return alri_score, alri_tier
