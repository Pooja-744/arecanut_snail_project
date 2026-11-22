"""Application configuration — reads from .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (two levels up from this file: backend/core/ -> backend/ -> project/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "backend" / ".env")

# Supabase
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_in_production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

# Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Model paths
SNAIL_MODEL_PATH: Path = PROJECT_ROOT / os.getenv("SNAIL_MODEL_PATH", "models/snail_detection_best.pt")
DISEASE_MODEL_PATH: Path = PROJECT_ROOT / os.getenv("DISEASE_MODEL_PATH", "models/arecanut_disease_best.pt")
DAMAGE_MODEL_PATH: Path = PROJECT_ROOT / os.getenv("DAMAGE_MODEL_PATH", "models/snail_damage_best.pt")

# CORS
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

# App
APP_ENV: str = os.getenv("APP_ENV", "development")
IS_DEV: bool = APP_ENV == "development"
