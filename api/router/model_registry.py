from __future__ import annotations

from typing import Dict

from config.model_registry import MODEL_REGISTRY, ModelConfig

NAIVE_BASELINE_MODEL_KEY = "openai:gpt-4o"

BAND_BASELINES: Dict[str, str] = {
    "low": "openai:gpt-4o-mini",
    "medium": NAIVE_BASELINE_MODEL_KEY,
    "high": "anthropic:claude-3.7-sonnet",
}


def get_model_config(model_key: str | None) -> ModelConfig | None:
    if not model_key:
        return None
    return MODEL_REGISTRY.get(model_key)


def get_band_baseline_model(band: str | None) -> str:
    if not band:
        return NAIVE_BASELINE_MODEL_KEY
    return BAND_BASELINES.get(band.lower(), NAIVE_BASELINE_MODEL_KEY)
