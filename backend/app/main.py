"""Entry point for the CognitoForge Labs FastAPI application."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.settings import get_settings
from backend.app.integrations.supabase_service import init_snowflake
from backend.app.routers import ai, operations, performance
from backend.app.services.gradient_service import init_gradient, run_gradient_task
from backend.app.routers import code_assist
from backend.app.routers import vulnscan
from backend.app.routers import reports

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Data directory anchoring ──────────────────────────────────────────────────
#
# Container layout (Dockerfile WORKDIR=/app, COPY backend/ ./backend/):
#   This file  →  /app/backend/app/main.py
#   parents[0] →  /app/backend/app
#   parents[1] →  /app/backend          ← _BACKEND_ROOT
#   parents[2] →  /app
#
# docker-compose volume:  api_data:/app/backend/data  ✓
# Dockerfile mkdir:       backend/data/{repos,…}       ✓
# repo_fetcher.py parents[3] from /app/backend/app/services/ → /app/backend ✓
# code_assist.py parents[3] from /app/backend/app/routers/  → /app/backend ✓
#
_BACKEND_ROOT = Path(__file__).resolve().parents[1]  # /app/backend
_DATA_ROOT    = _BACKEND_ROOT / "data"               # /app/backend/data  ← volume mountpoint

for _subdir in ("repos", "vector_index", "performance_tests", "simulations"):
    (_DATA_ROOT / _subdir).mkdir(parents=True, exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CognitoForge Labs",
    version="0.1.0",
    description="Hackathon backend for AI-driven DevSecOps red team simulations.",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins: set[str] = {
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "https://major-drab.vercel.app",
    # Removed trailing slash — browsers send origins without trailing slash
    "https://major-gi2s8fjth-murtuzamaazs-projects.vercel.app",
    "https://threatforge.duckdns.org",
    "http://threatforge.duckdns.org",
}

if settings.auth0_domain:
    allowed_origins.add(settings.auth0_domain.rstrip("/"))

# Extra origins via env var (comma-separated), e.g. new Vercel preview URLs
extra = os.environ.get("COGNITOFORGE_ALLOWED_ORIGINS", "")
for _origin in (o.strip() for o in extra.split(",") if o.strip()):
    allowed_origins.add(_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(operations.router)
app.include_router(ai.router)
app.include_router(performance.router)
app.include_router(code_assist.router)
app.include_router(vulnscan.router)
app.include_router(reports.router)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event() -> None:
    """Initialise optional integrations once the application boots."""

    # These lines appear in CloudWatch / Docker logs — verify paths on every deploy
    logger.info("Backend root : %s", _BACKEND_ROOT)
    logger.info("Data root    : %s (exists=%s)", _DATA_ROOT, _DATA_ROOT.exists())
    logger.info("Repos dir    : %s (exists=%s)",
                _DATA_ROOT / "repos", (_DATA_ROOT / "repos").exists())

    try:
        client = init_snowflake()
        if client is not None:
            logger.info("Supabase integration initialised")
        else:
            logger.debug("Supabase integration skipped (configuration missing or connector absent)")
    except Exception as exc:
        logger.exception("Supabase initialisation failed", extra={"error": str(exc)})

    try:
        init_gradient()
        logger.debug("Gradient task handler ready", extra={"callable": run_gradient_task.__name__})
    except Exception as exc:
        logger.exception("Gradient initialisation failed", extra={"error": str(exc)})

    logger.info("Code Assist service ready")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def healthcheck() -> dict[str, bool]:
    """Liveness probe used by Docker and AWS."""
    return {"ok": True}


@app.get("/health/storage")
async def storage_healthcheck() -> dict[str, object]:
    """
    Diagnostic endpoint — confirms volume mount is working inside the container.

    Call after every deploy:
        curl https://threatforge.duckdns.org/health/storage

    Healthy response: all directories exist=true, paths start with /app/backend/data/
    If repos dir shows 0 files after upload, the volume is not mounted correctly.
    """
    dirs = {
        "repos":             _DATA_ROOT / "repos",
        "vector_index":      _DATA_ROOT / "vector_index",
        "performance_tests": _DATA_ROOT / "performance_tests",
        "simulations":       _DATA_ROOT / "simulations",
    }
    return {
        "backend_root": str(_BACKEND_ROOT),
        "data_root":    str(_DATA_ROOT),
        "directories": {
            name: {
                "path":   str(path),
                "exists": path.exists(),
                "is_dir": path.is_dir(),
                "files":  len(list(path.iterdir())) if path.exists() else 0,
            }
            for name, path in dirs.items()
        },
    }