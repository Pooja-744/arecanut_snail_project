"""
AI Analysis API — unified image analysis endpoint.
Accepts an uploaded or live captured image, runs all three actual models,
returns plotted bounding boxes, diagnosis, severity, and stores to history.
"""
from __future__ import annotations

import io
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from PIL import Image

from backend.core.inference import analyze_image
from backend.core.db import save_analysis_record
from backend.api.auth import verify_token
from backend.schemas.schemas import AnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    save_to_history: bool = Form(True),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Upload an image (or live captured frame) and get unified AI analysis results:
    1. YOLOv8n Snail Detection & Counting with bounding boxes.
    2. MobileNetV2 Arecanut Disease Identification.
    3. MobileNetV2 Snail Feeding Damage Severity Rating.
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES and not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(400, "Only JPG, JPEG, PNG, and WebP images are supported.")

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(400, "Image too large. Maximum size is 25 MB.")

    try:
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Cannot read image file. It may be corrupted: {e}")

    # Run actual model inference
    try:
        result = analyze_image(pil_img)
    except Exception as e:
        logger.exception("Inference error during analyze_image: %s", e)
        raise HTTPException(500, f"AI inference failed: {e}")

    analysis_id = str(uuid.uuid4())
    user_id = None

    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")

    # Save to local database
    if save_to_history:
        try:
            save_analysis_record({
                "id": analysis_id,
                "user_id": user_id,
                "overall_status": result["overall_status"],
                "snail_detected": result["snail_detection"]["detected"],
                "snail_count": result["snail_detection"]["count"],
                "snail_confidence": result["snail_detection"]["confidence"],
                "boxes": result["snail_detection"]["boxes"],
                "disease_class": result["disease_classification"]["predicted_class"],
                "disease_confidence": result["disease_classification"]["confidence"],
                "is_healthy": result["disease_classification"]["is_healthy"],
                "damage_severity": result["damage_assessment"]["severity"],
                "damage_confidence": result["damage_assessment"]["confidence"],
                "recommendation": result["combined_recommendation"],
                "original_image": result.get("original_image"),
                "annotated_image": result.get("annotated_image"),
            })
        except Exception as e:
            logger.warning("Could not persist analysis record to database: %s", e)

    return AnalysisResponse(
        analysis_id=analysis_id,
        image_url=None,
        original_image=result.get("original_image"),
        annotated_image=result.get("annotated_image"),
        snail_detection=result["snail_detection"],
        disease_classification=result["disease_classification"],
        damage_assessment=result["damage_assessment"],
        combined_recommendation=result["combined_recommendation"],
        overall_status=result["overall_status"],
        overall_status_text=result.get("overall_status_text"),
        smart_recommendations=result.get("smart_recommendations"),
    )
