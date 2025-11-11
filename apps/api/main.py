from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="AgenticLabs API")

@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok"})
