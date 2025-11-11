import uuid
from typing import Dict, Any

def new_run_id() -> str:
    return f"r_{uuid.uuid4().hex[:16]}"

def compute_alri_tag(risk_band: str | None = None, jurisdiction: str | None = None) -> str:
    """
    Placeholder ALRI tag.
    Later: use your paper's ALRI formula with risk & jurisdiction to compute retention.
    """
    base_months = 12  # simple default; will expand to ALRI(B + Rn*Rmax + In)
    return f"ALRI_{base_months}M"

def evaluate_policy(confidence: float, threshold: float = 0.7) -> Dict[str, Any]:
    hil = confidence < threshold
    return {
        "allow_list_passed": True,     # no tools in stub
        "confidence_threshold": threshold,
        "hil_triggered": hil,
        "violations": [] if not hil else ["confidence_below_threshold"],
    }
