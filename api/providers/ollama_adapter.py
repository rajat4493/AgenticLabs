import time
import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2:7b-instruct"  # fallback if none provided
TIMEOUT = 120  # seconds

def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))  # rough token estimate

def plan(req: Dict[str, Any], model_name: str | None = None) -> Dict[str, Any]:
    prompt = req.get("prompt", "")
    tokens = _estimate_tokens(prompt)
    model = model_name or DEFAULT_MODEL
    return {
        "target": {"provider": "ollama", "model": model},
        "est_tokens": tokens,
        "est_cost_usd": 0.0
    }

def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    start = time.time()
    model = plan.get("target", {}).get("model", DEFAULT_MODEL)
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        output = data.get("response", "")
    except Exception as e:
        output = f"[Ollama error] {e}"

    latency_ms = int((time.time() - start) * 1000)
    tokens_in = _estimate_tokens(prompt)
    tokens_out = _estimate_tokens(output)
    _ = tokens_in + tokens_out

    return {
        "output": output.strip(),
        "confidence": 0.9,  # placeholder; scoring comes later
        "latency_ms": latency_ms,
        "cost_usd": 0.0,
        "provenance": {
            "provider": "ollama",
            "model": model,
            "parameters": {"temperature": 0.7}
        }
    }
