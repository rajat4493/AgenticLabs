from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/v1")

@router.get("/ping")
def ping():
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat() + "Z",
        "service": "agenticlabs-api"
    }
