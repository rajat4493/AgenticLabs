import time
from typing import Any, Dict

def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Tiny structured logger (stdout). Swap to OTEL later."""
    print({
        "ts": time.time(),
        "event": event_type,
        **payload,
    })
