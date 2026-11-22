"""
Dashboard statistics API — computes user-specific and plantation overview metrics.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from backend.api.auth import verify_token
from backend.core.db import get_dashboard_summary

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@router.get("/stats")
async def get_dashboard_stats(token: Optional[str] = Depends(oauth2_scheme)):
    user_id = None
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")

    return get_dashboard_summary(user_id=user_id)
