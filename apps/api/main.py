from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apps.api.routes.ping import router as ping_router

app = FastAPI(title="AgenticLabs API")

# allow local UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok"})

app.include_router(ping_router)
