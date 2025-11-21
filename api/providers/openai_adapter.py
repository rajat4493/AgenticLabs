import os
import time
from typing import Any, Dict

import requests

from pricing import estimate_cost


def plan(run_payload: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    temperature = run_payload.get("temperature") if isinstance(run_payload, dict) else None
    if not isinstance(temperature, (int, float)):
        temperature = 0.2

    max_tokens = run_payload.get("max_tokens", 512) if isinstance(run_payload, dict) else 512
    if not isinstance(max_tokens, int):
        max_tokens = 512

    return {
        "target": {
            "provider": "openai",
            "model": model_name,
        },
        "params": {
            "temperature": float(temperature),
            "max_tokens": max_tokens,
        },
    }


def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    target = plan.get("target") or {}
    params = plan.get("params") or {}

    model = target.get("model") or "gpt-4o-mini"
    temperature = params.get("temperature", 0.2)
    max_tokens = params.get("max_tokens", 512)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful, concise assistant used inside AgenticLabs smart router.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.perf_counter()
    resp = requests.post(
        os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1") + "/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    resp.raise_for_status()
    data = resp.json()

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    output_text = message.get("content", "")

    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    completion_tokens = int(usage.get("completion_tokens", 0))

    cost_usd = estimate_cost(model, prompt_tokens, completion_tokens)

    provenance = {
        "provider": "openai",
        "model": model,
        "mode": "chat.completions",
        "input_tokens": int(prompt_tokens),
        "output_tokens": int(completion_tokens),
    }

    return {
        "output": output_text,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "confidence": 0.9,
        "provenance": provenance,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
