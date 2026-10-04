from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="IntentWay API",
    description="Foundation API for the IntentWay multi-stop routing project.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "IntentWay",
        "status": "foundation-ready",
        "service": "intentway-backend",
    }


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok", "service": "intentway-backend"}