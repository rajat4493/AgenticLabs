from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModelConfig:
    key: str
    provider: str
    model_id: str
    display_name: str
    capabilities: Dict[str, float]
    pricing: Dict[str, float]


MODEL_REGISTRY: Dict[str, ModelConfig] = {
    "openai:gpt-4o-mini": ModelConfig(
        key="openai:gpt-4o-mini",
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        capabilities={
            "reasoning": 0.75,
            "coding": 0.8,
            "creative": 0.78,
            "operations": 0.72,
            "product": 0.74,
        },
        pricing={"input_per_million": 0.15, "output_per_million": 0.6},
    ),
    "openai:gpt-4o": ModelConfig(
        key="openai:gpt-4o",
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o",
        capabilities={
            "reasoning": 0.85,
            "coding": 0.88,
            "creative": 0.86,
            "operations": 0.82,
            "product": 0.83,
        },
        pricing={"input_per_million": 2.5, "output_per_million": 10.0},
    ),
    "openai:gpt-4.1-mini": ModelConfig(
        key="openai:gpt-4.1-mini",
        provider="openai",
        model_id="gpt-4.1-mini",
        display_name="GPT-4.1 Mini",
        capabilities={
            "reasoning": 0.8,
            "coding": 0.86,
            "creative": 0.8,
            "operations": 0.75,
            "product": 0.78,
        },
        pricing={"input_per_million": 0.15, "output_per_million": 0.6},
    ),
    "openai:gpt-4.1": ModelConfig(
        key="openai:gpt-4.1",
        provider="openai",
        model_id="gpt-4.1",
        display_name="GPT-4.1",
        capabilities={
            "reasoning": 0.9,
            "coding": 0.92,
            "creative": 0.9,
            "operations": 0.9,
            "product": 0.88,
        },
        pricing={"input_per_million": 5.0, "output_per_million": 15.0},
    ),
    "anthropic:claude-3.7-sonnet": ModelConfig(
        key="anthropic:claude-3.7-sonnet",
        provider="anthropic",
        model_id="claude-3.7-sonnet",
        display_name="Claude 3.7 Sonnet",
        capabilities={
            "reasoning": 0.88,
            "coding": 0.86,
            "creative": 0.87,
            "operations": 0.85,
            "product": 0.84,
        },
        pricing={"input_per_million": 3.0, "output_per_million": 15.0},
    ),
}
