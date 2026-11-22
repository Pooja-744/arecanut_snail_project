"""
Local SQLite database engine for Arecanut Snail Project.
Provides reliable local persistence for users, authentication, and analysis history.
Works seamlessly without requiring external cloud database credentials.
"""
from __future__ import annotations

import sqlite3
import hashlib
import os
import json
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Any

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

DB_PATH = PROJECT_ROOT / "backend" / "database.db"

def get_db_connection() -> sqlite3.Connection:
    """Return a connection with dictionary-like row access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256 with salt."""
    if not salt:
        salt = os.urandom(16).hex()
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    pwd_hash = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000).hex()
    return pwd_hash, salt

def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    """Verify password against stored hash and salt."""
    calculated_hash, _ = hash_password(password, salt)
    return calculated_hash == pwd_hash

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            language_preference TEXT DEFAULT 'en',
            role TEXT DEFAULT 'farmer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            overall_status TEXT NOT NULL,
            snail_detected INTEGER DEFAULT 0,
            snail_count INTEGER DEFAULT 0,
            snail_confidence REAL DEFAULT 0.0,
            boxes_json TEXT DEFAULT '[]',
            disease_class TEXT DEFAULT 'HEALTHY',
            disease_confidence REAL DEFAULT 0.0,
            is_healthy INTEGER DEFAULT 1,
            damage_severity TEXT DEFAULT NULL,
            damage_confidence REAL DEFAULT 0.0,
            recommendation TEXT,
            original_image TEXT,
            annotated_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Local SQLite database initialized at %s", DB_PATH)

# Initialize on module load
init_db()

# ---------------------------------------------------------------------------
# Database Helper Functions
# ---------------------------------------------------------------------------

def create_user(name: str, email: str, password: str, language_preference: str = "en") -> dict[str, Any]:
    """Create a new user. Raises ValueError if email already registered."""
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("An account with this email address already exists.")

    user_id = str(uuid.uuid4())
    pwd_hash, salt = hash_password(password)

    cursor.execute(
        """
        INSERT INTO users (id, name, email, password_hash, salt, language_preference)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, name.strip(), email_clean, pwd_hash, salt, language_preference)
    )
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "name": name.strip(),
        "email": email_clean,
        "language_preference": language_preference,
        "role": "farmer"
    }

def authenticate_user(email: str, password: str) -> Optional[dict[str, Any]]:
    """Verify credentials and return user info or None."""
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    if verify_password(password, row["password_hash"], row["salt"]):
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "language_preference": row["language_preference"],
            "role": row["role"]
        }
    return None

def get_user_by_id(user_id: str) -> Optional[dict[str, Any]]:
    """Retrieve user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, language_preference, role, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_user_language(user_id: str, language_preference: str):
    """Update preferred language."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language_preference = ? WHERE id = ?", (language_preference, user_id))
    conn.commit()
    conn.close()

def save_analysis_record(data: dict[str, Any]) -> str:
    """Save an analysis record into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    analysis_id = data.get("id") or str(uuid.uuid4())

    damage_sev = data.get("damage_severity")
    if not damage_sev or str(damage_sev).lower() in ("none", "null", "no_damage", "no damage"):
        damage_sev = None

    cursor.execute(
        """
        INSERT INTO analyses (
            id, user_id, overall_status, snail_detected, snail_count, snail_confidence,
            boxes_json, disease_class, disease_confidence, is_healthy, damage_severity,
            damage_confidence, recommendation, original_image, annotated_image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            analysis_id,
            data.get("user_id"),
            data.get("overall_status", "healthy"),
            1 if data.get("snail_detected") else 0,
            data.get("snail_count", 0),
            data.get("snail_confidence", 0.0),
            json.dumps(data.get("boxes", [])),
            data.get("disease_class", "HEALTHY"),
            data.get("disease_confidence", 0.0),
            1 if data.get("is_healthy") else 0,
            damage_sev,
            data.get("damage_confidence", 0.0) if damage_sev else 0.0,
            data.get("recommendation", ""),
            data.get("original_image", ""),
            data.get("annotated_image", "")
        )
    )
    conn.commit()
    conn.close()
    return analysis_id

def get_user_analyses(user_id: Optional[str] = None, page: int = 1, per_page: int = 10) -> dict[str, Any]:
    """Retrieve paginated analyses for a specific user (or all if user_id is None)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    offset = (page - 1) * per_page

    if user_id:
        cursor.execute("SELECT COUNT(*) as total FROM analyses WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT id, user_id, overall_status, snail_detected, snail_count, snail_confidence,
                   boxes_json, disease_class, disease_confidence, is_healthy, damage_severity,
                   damage_confidence, recommendation, original_image, annotated_image, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, per_page, offset)
        )
    else:
        cursor.execute("SELECT COUNT(*) as total FROM analyses")
        total = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT id, user_id, overall_status, snail_detected, snail_count, snail_confidence,
                   boxes_json, disease_class, disease_confidence, is_healthy, damage_severity,
                   damage_confidence, recommendation, original_image, annotated_image, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset)
        )

    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        try:
            d["boxes"] = json.loads(d.get("boxes_json") or "[]")
        except Exception:
            d["boxes"] = []
        items.append(d)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page > 0 else 1
    }

def get_analysis_by_id(analysis_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a single analysis record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["boxes"] = json.loads(d.get("boxes_json") or "[]")
        except Exception:
            d["boxes"] = []
        return d
    return None

def get_dashboard_summary(user_id: Optional[str] = None) -> dict[str, Any]:
    """Compute aggregate statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM analyses WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM analyses")
    rows = cursor.fetchall()
    conn.close()

    total = len(rows)
    healthy = 0
    disease = 0
    snail = 0
    snail_damage = 0
    both = 0
    further_inspection = 0

    disease_dist: dict[str, int] = {}
    for r in rows:
        status = r["overall_status"]
        is_h = bool(r["is_healthy"])
        has_s = bool(r["snail_detected"])
        sev = r["damage_severity"]
        has_d = bool(sev and str(sev).lower() not in ("none", "null", "no_damage", "no damage"))
        dc = r["disease_class"]
        has_dis = bool(not is_h and dc not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN"))

        if status == "both_detected" or (has_s and has_dis):
            both += 1
        elif status == "disease_detected" or (has_dis and not has_s and not has_d):
            disease += 1
        elif status == "snail_damage_detected" or (has_d and not has_dis):
            snail_damage += 1
        elif status == "snail_detected" or (has_s and not has_d and not has_dis):
            snail += 1
        elif status == "further_inspection" or dc == "UNCERTAIN":
            further_inspection += 1
        else:
            healthy += 1

        if dc and not is_h and dc not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN"):
            disease_dist[dc] = disease_dist.get(dc, 0) + 1

    recent = [dict(r) for r in sorted(rows, key=lambda x: x["created_at"], reverse=True)[:5]]
    for r in recent:
        try:
            r["boxes"] = json.loads(r.get("boxes_json") or "[]")
        except Exception:
            r["boxes"] = []

    return {
        "total_analyses": total,
        "healthy_count": healthy,
        "disease_count": disease,
        "snail_count": snail,
        "snail_damage_count": snail_damage,
        "both_count": both,
        "further_inspection_count": further_inspection,
        "recent_analyses": recent,
        "disease_distribution": disease_dist
    }
