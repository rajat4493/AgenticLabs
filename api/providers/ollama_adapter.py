import time
import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2:7b-instruct"  # you can change to mistral, phi3, etc.
TIMEOUT = 120  # seconds

def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))  # rough token estimate

def plan(req: Dict[str, Any]) -> Dict[str, Any]:
    prompt = req.get("prompt", "")
    tokens = _estimate_tokens(prompt)
    return {
        "target": {"provider": "ollama", "model": MODEL_NAME},
        "est_tokens": tokens,
        "est_cost_usd": 0.0  # local → free
    }

def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    start = time.time()
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
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
    total_tokens = tokens_in + tokens_out

    return {
        "output": output.strip(),
        "confidence": 0.9,  # fixed for now; can add scoring later
        "latency_ms": latency_ms,
        "cost_usd": 0.0,
        "provenance": {
            "provider": "ollama",
            "model": MODEL_NAME,
            "parameters": {"temperature": 0.7}
        }
    }
