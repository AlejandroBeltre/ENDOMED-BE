"""FastAPI application for ENDOMED.

Mounted at /api/ via config/asgi.py (Django handles the rest).
Phase 1: health check only — routers are added in Phase 2.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ENDOMED API",
    description="Sistema de Gestión Médica Endometabólica",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/", tags=["system"])
async def health_check() -> dict:
    """Railway liveness probe — GET /api/health/"""
    from asgiref.sync import sync_to_async
    from django.db import connection

    try:
        await sync_to_async(connection.ensure_connection)()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "db": db_status, "version": "0.1.0"}
