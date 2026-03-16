"""FastAPI application for ENDOMED.

Mounted at /api/ via config/asgi.py.
All REST endpoints live here. Django handles /admin/ and static files.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import agenda, auth, documentos, hce, pacientes

_extra = os.environ.get("CORS_ALLOWED_ORIGINS", "")
_origins = [o.strip() for o in _extra.split(",") if o.strip()]
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] + _origins

app = FastAPI(
    title="ENDOMED API",
    description="Sistema de Gestión Médica Endometabólica",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agenda.router)
app.include_router(pacientes.router)
app.include_router(hce.router)
app.include_router(documentos.router)


@app.get("/health/", tags=["system"])
def health_check() -> dict:
    """Railway liveness probe — GET /api/health/"""
    from django.db import connection

    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "db": db_status, "version": "0.2.0"}
