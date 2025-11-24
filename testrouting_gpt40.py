import requests
import json
from time import sleep

API_BASE = "http://localhost:8000"

HEADERS = {
    "Content-Type": "application/json",
}

prompts = [
    "Explain quantum entanglement using 5 different analogies and compare how accurate each analogy is.",
    "Design a 3-step decision tree for a bank's fraud detection workflow and explain the trade-offs at each node.",
    "Compare transformers, RNNs, and gradient boosted trees for credit risk modeling. When would you choose each and why?",
    "Given a SaaS startup with churn of 4%/month and CAC of $500, outline 3 retention experiments and how you’d measure them.",
    "Explain the concept of causal inference vs correlation using 3 business examples: marketing, fraud, and HR analytics.",
    "Act as a staff engineer. Propose a high-level architecture for an AI-powered customer support router, including data stores and observability.",
    "Explain how Monte Carlo simulation can be used for portfolio risk and what its main limitations are.",
    "Compare RLHF and DPO training methods and explain in which scenarios each is more appropriate.",
    "For a KYC process in online gambling, outline a risk-based scoring model and how AI could make it adaptive over time.",
    "Explain vector databases to a non-technical CFO using 3 analogies and a concrete ROI example."
]

def call_router(prompt: str):
    payload = {
        "prompt": prompt,
        "agent_id": "default-agent",
        "context": {},
        "policy_overrides": {}   # No forcing — natural routing
    }

    resp = requests.post(
        f"{API_BASE}/v1/chat",
        headers=HEADERS,
        data=json.dumps(payload)
    )

    print(f"Status {resp.status_code}")
    try:
        print(resp.json())
    except:
        print(resp.text)


for i, p in enumerate(prompts, start=1):
    print(f"\n--- Run {i} ---")
    call_router(p)
    sleep(0.3)
