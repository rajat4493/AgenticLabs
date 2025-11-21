from fastapi import APIRouter, Query

from analytics.store import metrics_store

router = APIRouter(prefix="/v1/logs", tags=["logs"])


@router.get("")
async def list_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """Return most recent runs, newest first."""
    return metrics_store.list_runs(offset=offset, limit=limit)
