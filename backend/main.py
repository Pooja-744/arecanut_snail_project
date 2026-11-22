"""FastAPI application entry point."""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend` package resolves correctly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Point matplotlib/ultralytics to writable local dirs
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib"))
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / ".yolo"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.core.config import CORS_ORIGINS
from backend.api import analysis, auth, history, chatbot, dashboard, reports, admin_models

app = FastAPI(
    title="Arecanut Snail Project API",
    description="AI-Based Detection System for Arecanut Diseases and Giant African Snail Infestation",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["AI Analysis"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(admin_models.router, prefix="/api/admin", tags=["Model Administration"])

# ---------------------------------------------------------------------------
# Health & Safe System Status (No secrets exposed)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    import sqlite3
    from backend.core.db import DB_PATH
    db_ok = False
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=3.0)
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok",
        "api_status": "connected",
        "database_status": "connected" if db_ok else "disconnected",
        "database_type": "SQLite",
        "version": "1.0.0"
    }


@app.get("/api/system/status", tags=["System Status"])
async def system_status():
    """
    Safe runtime system health endpoint.
    Performs real live checks on API, SQLite database, and active AI model files.
    Never exposes internal URLs, passwords, API keys, or service credentials.
    """
    import sqlite3
    from backend.core.db import DB_PATH
    from backend.core.config import (
        SNAIL_MODEL_PATH,
        DISEASE_MODEL_PATH,
        DAMAGE_MODEL_PATH,
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY
    )
    from backend.core.inference import _registry

    # 1. Real SQLite connection test
    db_status = "connected"
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=3.0)
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        db_status = "error"

    # 2. Check model loading states
    snail_status = "loaded" if "yolo" in _registry else ("available" if SNAIL_MODEL_PATH.exists() else "missing")
    disease_status = "loaded" if "disease" in _registry else ("available" if DISEASE_MODEL_PATH.exists() else "missing")
    damage_status = "loaded" if "damage" in _registry else ("available" if DAMAGE_MODEL_PATH.exists() else "missing")

    # 3. Supabase integration audit
    supabase_configured = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and "your-project-id" not in SUPABASE_URL)

    return {
        "api_status": "connected",
        "database_status": db_status,
        "database_type": "SQLite",
        "supabase_status": "connected" if supabase_configured else "not_configured",
        "models": {
            "snail_model": snail_status,
            "disease_model": disease_status,
            "damage_model": damage_status,
        },
        "model_files": {
            "snail_model_available": SNAIL_MODEL_PATH.exists(),
            "disease_model_available": DISEASE_MODEL_PATH.exists(),
            "damage_model_available": DAMAGE_MODEL_PATH.exists(),
        }
    }


# ---------------------------------------------------------------------------
# Serve React Frontend
# ---------------------------------------------------------------------------
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend_root():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # Allow /api and /health to fall through
        if full_path.startswith("api/") or full_path == "health":
            return {"error": "Not Found"}
        return FileResponse(str(FRONTEND_DIST / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 65)
    print("🌾 ARECANUT SURVEILLANCE SYSTEM READY")
    print("👉 Open your browser at: http://127.0.0.1:8000 (or http://localhost:8000)")
    print("=" * 65 + "\n")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
