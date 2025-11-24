from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.router_runs_repo import list_runs
from db.session import get_db

router = APIRouter(prefix="/v1/logs", tags=["logs"])


@router.get("")
async def list_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return most recent runs, newest first."""
    return list_runs(db, offset=offset, limit=limit)
