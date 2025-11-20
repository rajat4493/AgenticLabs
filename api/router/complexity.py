import re

def score_complexity(prompt: str) -> float:
    """
    Lightweight heuristic complexity score in [0,1].
    Factors: length, numerics, code fences/JSON, sentences, keywords.
    """
    if not prompt:
        return 0.0

    # length factor
    n_chars = len(prompt)
    f_len = min(n_chars / 2000.0, 1.0)

    # numerics & symbols
    f_digits = min(len(re.findall(r"\d", prompt)) / 50.0, 1.0)
    f_symbols = min(len(re.findall(r"[\{\}\[\]\(\)\=\+\-\*/<>]", prompt)) / 80.0, 1.0)

    # code/JSON fences
    f_code = 0.2 if "```" in prompt or re.search(r"\bclass\b|\bdef\b|\bfunction\b", prompt) else 0.0
    f_json = 0.2 if re.search(r"\{.*:.*\}", prompt, flags=re.S) else 0.0

    # sentences (rough)
    f_sent = min(len(re.split(r"[.!?]+", prompt)) / 20.0, 1.0)

    # keywords hinting complexity
    KW = ["analyze", "optimize", "summarize", "compare", "design", "explain", "policy", "architecture"]
    f_kw = 0.15 if any(k in prompt.lower() for k in KW) else 0.0

    score = (0.45 * f_len) + (0.15 * f_digits) + (0.1 * f_symbols) + f_code + f_json + (0.2 * f_sent) + f_kw
    return max(0.0, min(score, 1.0))

def choose_band(score: float) -> str:
    if score < 0.25:
        return "simple"
    if score < 0.6:
        return "moderate"
    return "complex"
