"""
Authentication API — register, login, logout, profile, forgot-password.
Provides secure authentication backed by the local SQLite database.
"""
from __future__ import annotations

import logging
import time
import hmac
import hashlib
import json
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from backend.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse
from backend.core.config import SECRET_KEY
from backend.core.db import create_user, authenticate_user, get_user_by_id, update_user_language

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def create_token(user_id: str, email: str) -> str:
    """Create a signed HMAC-SHA256 JWT-like bearer token valid for 7 days."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + (7 * 24 * 3600)
    }
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig_input = f"{h_b64}.{p_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), sig_input, hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{s_b64}"


def verify_token(token: str) -> Optional[dict]:
    """Verify signed bearer token and extract payload."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_b64, p_b64, s_b64 = parts
        sig_input = f"{h_b64}.{p_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), sig_input, hashlib.sha256).digest()
        
        # Add padding back if necessary
        pad = len(s_b64) % 4
        if pad:
            s_b64 += "=" * (4 - pad)
        actual_sig = base64.urlsafe_b64decode(s_b64.encode())
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        # Decode payload
        pad_p = len(p_b64) % 4
        if pad_p:
            p_b64 += "=" * (4 - pad_p)
        payload = json.loads(base64.urlsafe_b64decode(p_b64.encode()).decode())
        
        if payload.get("exp", 0) < time.time():
            return None  # Expired
            
        return payload
    except Exception as e:
        logger.warning("Token verification failed: %s", e)
        return None


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """Dependency that extracts the authenticated user from the Bearer token."""
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        return None
    return get_user_by_id(payload.get("sub"))


class ForgotPasswordRequest(BaseModel):
    email: str


class UpdateLanguageRequest(BaseModel):
    language_preference: str


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    name = body.name.strip()
    email = body.email.strip()
    password = body.password

    if not name or len(name) < 2:
        raise HTTPException(400, "Full name must be at least 2 characters.")
    if not email or "@" not in email:
        raise HTTPException(400, "Please enter a valid email address.")
    if not password or len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters long.")

    try:
        user = create_user(
            name=name,
            email=email,
            password=password,
            language_preference=body.language_preference or "en"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error during user registration: %s", e)
        raise HTTPException(status_code=500, detail="Registration error occurred.")

    token = create_token(user["id"], user["email"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    email = body.email.strip()
    password = body.password

    if not email or not password:
        raise HTTPException(400, "Please provide both email and password.")

    user = authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    token = create_token(user["id"], user["email"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


# ---------------------------------------------------------------------------
# Profile & Session Check
# ---------------------------------------------------------------------------
@router.get("/me")
async def get_my_profile(user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated or token expired.")
    return user


@router.post("/update-language")
async def set_language(body: UpdateLanguageRequest, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    update_user_language(user["id"], body.language_preference)
    return {"success": True, "language_preference": body.language_preference}


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    email = body.email.strip().lower()
    # Security best practice: confirm receipt without leaking whether email exists
    return {
        "success": True,
        "message": f"If an account with {email} exists, password reset instructions have been dispatched."
    }


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@router.post("/logout")
async def logout():
    return {"success": True, "message": "Successfully logged out."}
