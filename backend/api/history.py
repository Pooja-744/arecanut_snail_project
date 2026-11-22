"""
Detection History API — retrieve past analyses for the authenticated user.
Backed by the local SQLite database to protect user privacy.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from backend.api.auth import verify_token
from backend.core.db import get_user_analyses, get_analysis_by_id

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _get_user_id(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


@router.get("/")
async def list_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    status_filter: Optional[str] = Query(None),
    token: Optional[str] = Depends(oauth2_scheme),
):
    user_id = _get_user_id(token)
    # Return user-specific history if logged in, or recent public scans
    res = get_user_analyses(user_id=user_id, page=page, per_page=per_page)
    
    if status_filter:
        res["items"] = [item for item in res["items"] if item.get("overall_status") == status_filter]
        
    return res


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, token: Optional[str] = Depends(oauth2_scheme)):
    row = get_analysis_by_id(analysis_id)
    if not row:
        raise HTTPException(404, "Analysis record not found.")
    
    user_id = _get_user_id(token)
    # If record has a user_id and current user does not match, block unauthorized access
    if row.get("user_id") and user_id and row["user_id"] != user_id:
        raise HTTPException(403, "Access denied. You can only view your own analysis reports.")

    return row
