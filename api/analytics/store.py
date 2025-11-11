import time
import threading

class MetricsStore:
    """Thread-safe in-memory metrics (can swap to Redis/DB later)."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_runs = 0
        self._total_latency_ms = 0.0
        self._total_cost_usd = 0.0

    def record(self, latency_ms: int, cost_usd: float) -> None:
        with self._lock:
            self._total_runs += 1
            self._total_latency_ms += float(latency_ms)
            self._total_cost_usd += float(cost_usd)

    def snapshot(self) -> dict:
        with self._lock:
            avg = (self._total_latency_ms / self._total_runs) if self._total_runs else 0.0
            return {
                "total_runs": self._total_runs,
                "avg_latency_ms": round(avg, 2),
                "total_cost_usd": round(self._total_cost_usd, 6),
            }

metrics_store = MetricsStore()
