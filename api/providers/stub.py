import time
from typing import Dict, Any

PRICING_USD_PER_1K_TOKENS = 0.0005  # e.g., $0.50 / 1M tokens

def _estimate_tokens(text: str) -> int:
    # super rough: ~4 chars per token
    return max(1, int(len(text) / 4))

def plan(req: Dict[str, Any]) -> Dict[str, Any]:
    prompt = req.get("prompt", "")
    tokens = _estimate_tokens(prompt)
    est_cost = (tokens / 1000.0) * PRICING_USD_PER_1K_TOKENS
    return {
        "target": {"provider": "stub", "model": "stub-echo-1"},
        "est_tokens": tokens,
        "est_cost_usd": est_cost,
    }

def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    start = time.time()
    # pretend to "think"
    time.sleep(0.01)
    output = f"Stub summary: {prompt}"

    tokens_in = _estimate_tokens(prompt)
    tokens_out = _estimate_tokens(output)
    total_tokens = tokens_in + tokens_out
    cost = (total_tokens / 1000.0) * PRICING_USD_PER_1K_TOKENS

    latency_ms = int((time.time() - start) * 1000)
    return {
        "output": output,
        "confidence": 0.95,  # fixed high confidence for stub
        "latency_ms": latency_ms,
        "cost_usd": round(cost, 6),
        "prompt_tokens": tokens_in,
        "completion_tokens": tokens_out,
        "provenance": {
            "provider": "stub",
            "model": "stub-echo-1",
            "parameters": {"temperature": 0.0}
        }
    }
