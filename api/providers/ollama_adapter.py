import os
import time
from typing import Any, Dict

import requests

OLLAMA_BASE = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:7b-instruct")
TIMEOUT = 120  # seconds


def _estimate_tokens(text: str) -> int:
    # crude heuristic ~4 chars per token
    return max(1, int(len(text) / 4))


def plan(req: Dict[str, Any], model_name: str | None = None) -> Dict[str, Any]:
    prompt = req.get("prompt", "")
    tokens = _estimate_tokens(prompt)
    model = model_name or DEFAULT_MODEL
    return {
        "target": {"provider": "ollama", "model": model},
        "est_tokens": tokens,
        "est_cost_usd": 0.0,
    }


def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    target = plan.get("target") or {}
    model = target.get("model") or DEFAULT_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    start = time.time()
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        output = data.get("response", "")
    except requests.HTTPError as e:
        output = f"[Ollama HTTP error] {e.response.status_code if e.response else 'unknown'}: {e}"
    except requests.RequestException as e:
        output = f"[Ollama error] {e}"

    latency_ms = int((time.time() - start) * 1000)
    tokens_in = _estimate_tokens(prompt)
    tokens_out = _estimate_tokens(output)

    return {
        "output": output.strip(),
        "confidence": 0.9,
        "latency_ms": latency_ms,
        "cost_usd": 0.0,
        "prompt_tokens": tokens_in,
        "completion_tokens": tokens_out,
        "provenance": {
            "provider": "ollama",
            "model": model,
            "parameters": {"stream": False},
        },
    }
