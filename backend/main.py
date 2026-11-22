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
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

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
