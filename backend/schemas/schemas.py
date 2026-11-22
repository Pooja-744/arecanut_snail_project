"""
Pydantic schemas for requests and responses.
Includes multi-task diagnostic models, general-purpose chatbot schemas, and dashboard metrics.
"""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    language_preference: str = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
class SnailDetectionResult(BaseModel):
    detected: bool
    count: int
    confidence: float
    boxes: list[list[float]]
    inference_ms: float
    status_text: Optional[str] = None


class DiseaseClassificationResult(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict[str, float]
    is_healthy: bool
    inference_ms: float
    status_text: Optional[str] = None
    explanation: Optional[str] = None


class DamageAssessmentResult(BaseModel):
    has_damage: bool = False
    severity: Optional[str] = None
    confidence: float = 0.0
    probabilities: dict[str, float] = {}
    status_text: Optional[str] = None
    explanation: Optional[str] = None


class AnalysisResponse(BaseModel):
    analysis_id: Optional[str] = None
    image_url: Optional[str] = None
    original_image: Optional[str] = None
    annotated_image: Optional[str] = None
    snail_detection: SnailDetectionResult
    disease_classification: DiseaseClassificationResult
    damage_assessment: DamageAssessmentResult
    combined_recommendation: str
    overall_status: str
    overall_status_text: Optional[str] = None
    smart_recommendations: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# General-Purpose Chatbot
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: str = "en"
    current_analysis: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_analyses: int
    healthy_count: int
    disease_count: int
    snail_count: int
    both_count: int
    recent_analyses: list[dict[str, Any]]
    disease_distribution: dict[str, int]
