"""
Chatbot API — General-Purpose AI Assistant with Specialized Arecanut & Snail Management Expertise.
Integrates Google Gemini API with intelligent local conversational & agronomic knowledge base fallback.
"""
from __future__ import annotations

import logging
import uuid
import re
from typing import Optional, Any
from fastapi import APIRouter, HTTPException

from backend.core.config import GEMINI_API_KEY
from backend.schemas.schemas import ChatRequest, ChatResponse
from backend.knowledge.plantation_advisory import get_knowledge_summary

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session history storage
_sessions: dict[str, list[dict[str, str]]] = {}

SYSTEM_PROMPT = f"""You are 'ArecaKisan AI', an intelligent, versatile general-purpose AI assistant as well as an expert agricultural specialist in Arecanut (Areca catechu) plantation management and Giant African Snail (Lissachatina fulica) pest control.

Your capabilities:
1. General AI Assistant (ChatGPT-style): You can clearly explain computer science concepts, machine learning, artificial intelligence, neural networks (CNNs), Python programming, mathematics, science, and everyday general topics in a friendly, articulate manner.
2. Domain Specialist: You provide expert, scientifically verified advice for arecanut farming (Koleroga / Mahali fruit rot, Bud rot, Yellow leaf disease, Ring spot) and Giant African Snail eradication.
3. Live Scan Interpretation: When current plant analysis context is provided, explain the findings clearly: snail detection count and confidence, disease classification, damage severity, and practical home/organic remedies.
4. If the user asks about the condition of their plant or recent scan and NO analysis data is provided, politely prompt them to capture or upload an arecanut plant photo on the Image Capture & Upload page.
5. Weather Analysis Removal: Do NOT provide weather forecasts, weather risk assessments, or weather alerts, as weather analysis is not part of this platform.
6. Multilingual: If the user communicates in Kannada (ಕನ್ನಡ) or requests Kannada, provide clear, natural responses in Kannada. Otherwise respond in clear, professional English.

Agricultural Reference Knowledge:
{get_knowledge_summary()}
"""


def _explain_current_analysis(analysis: dict[str, Any], language: str = "en") -> str:
    """Format an informative explanation of the user's current analysis results."""
    is_kn = language.startswith("kn")
    snail_info = analysis.get("snail_detection", {})
    disease_info = analysis.get("disease_classification", {})
    damage_info = analysis.get("damage_assessment", {})
    overall_text = analysis.get("overall_status_text") or analysis.get("overall_status", "Analyzed")
    smart_rec = analysis.get("smart_recommendations", {})

    snail_count = snail_info.get("count", 0)
    snail_conf = snail_info.get("confidence", 0.0)
    disease_name = disease_info.get("disease", "Unknown").replace("_", " ")
    is_healthy = disease_info.get("is_healthy", False)
    has_damage = damage_info.get("has_damage", False)
    severity = damage_info.get("severity") or "None"

    if is_kn:
        res = [f"📊 **ನಿಮ್ಮ ಪ್ರಸ್ತುತ ತಪಾಸಣೆಯ ಸಾರಾಂಶ ({overall_text}):**\n"]
        if snail_count > 0:
            res.append(f"• **ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳು:** ಪತ್ತೆಯಾಗಿದೆ ({snail_count} ಬಸವನಹುಳುಗಳು, ವಿಶ್ವಾಸಾರ್ಹತೆ: {snail_conf*100:.1f}%)")
        else:
            res.append("• **ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳು:** ಯಾವುದೇ ಬಸವನಹುಳು ಪತ್ತೆಯಾಗಿಲ್ಲ (ಶುದ್ಧವಾಗಿದೆ)")

        if is_healthy:
            res.append("• **ಅಡಿಕೆ ರೋಗ:** ಸಸ್ಯವು ಆರೋಗ್ಯಕರವಾಗಿದೆ (ಯಾವುದೇ ಶಿಲೀಂಧ್ರ ರೋಗವಿಲ್ಲ)")
        else:
            res.append(f"• **ಅಡಿಕೆ ರೋಗ:** {disease_name} (ವಿಶ್ವಾಸಾರ್ಹತೆ: {disease_info.get('confidence', 0.0)*100:.1f}%)")

        if not has_damage or severity.lower() in ("none", "null"):
            res.append("• **ಹಾನಿಯ ತೀವ್ರತೆ:** ಯಾವುದೇ ಗೋಚರ ಹಾನಿ ಪತ್ತೆಯಾಗಿಲ್ಲ (ಆರೋಗ್ಯಕರ ಸಸ್ಯ)")
        else:
            res.append(f"• **ಹಾನಿಯ ತೀವ್ರತೆ:** {severity.replace('_', ' ').title()}")

        home_remedies = smart_rec.get("home_remedies", [])
        if home_remedies:
            res.append("\n🌿 **ಶಿಫಾರಸು ಮಾಡಲಾದ ಮನೆಮದ್ದುಗಳು ಮತ್ತು ನಿಯಂತ್ರಣ:**")
            for hr in home_remedies[:3]:
                res.append(f"- **{hr.get('title', '')}**: {hr.get('description', '')}")

        return "\n".join(res)
    else:
        res = [f"📊 **Current Plantation Scan Findings ({overall_text}):**\n"]
        if snail_count > 0:
            res.append(f"• **Giant African Snail:** DETECTED ({snail_count} snail(s) identified, {snail_conf*100:.1f}% confidence)")
        else:
            res.append("• **Giant African Snail:** NO SNAILS DETECTED (Clear)")

        if is_healthy:
            res.append("• **Arecanut Disease:** Healthy Plant (No fungal pathogen detected)")
        else:
            res.append(f"• **Arecanut Disease:** {disease_name} ({disease_info.get('confidence', 0.0)*100:.1f}% confidence)")

        if not has_damage or severity.lower() in ("none", "null"):
            res.append("• **Feeding Damage Severity:** No Visible Damage Detected (Healthy palm)")
        else:
            res.append(f"• **Feeding Damage Severity:** {severity.replace('_', ' ').title()}")

        home_remedies = smart_rec.get("home_remedies", [])
        if home_remedies:
            res.append("\n🌿 **Recommended Home Remedies & Actions:**")
            for hr in home_remedies[:3]:
                res.append(f"- **{hr.get('title', '')}**: {hr.get('description', '')}")

        return "\n".join(res)


def _generate_fallback_response(query: str, language: str = "en", current_analysis: Optional[dict[str, Any]] = None) -> str:
    """Intelligent fallback for general AI questions, domain queries, and scan evaluation."""
    q = query.lower().strip()
    is_kn = language.startswith("kn") or any(char in query for char in "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ")

    # 1. Questions asking about the user's current scan or plant image
    scan_keywords = ["my plant", "my scan", "current analysis", "this image", "my photo", "is my plant healthy",
                     "what is wrong with my plant", "did you find snail", "what disease", "ನನ್ನ ಸಸ್ಯ", "ನನ್ನ ಫೋಟೋ", "ಫಲಿತಾಂಶ", "ವಿಶ್ಲೇಷಣೆ"]
    if any(k in q for k in scan_keywords):
        if current_analysis:
            return _explain_current_analysis(current_analysis, language="kn" if is_kn else "en")
        else:
            if is_kn:
                return (
                    "ಪ್ರಸ್ತುತ ಸೆಷನ್‌ನಲ್ಲಿ ಯಾವುದೇ ಸಸ್ಯದ ಚಿತ್ರವನ್ನು ಇನ್ನೂ ವಿಶ್ಲೇಷಿಸಲಾಗಿಲ್ಲ.\n\n"
                    "ದಯವಿಟ್ಟು ನ್ಯಾವಿಗೇಷನ್‌ನಿಂದ **'Image Capture & Upload'** ಪುಟಕ್ಕೆ ಹೋಗಿ ನಿಮ್ಮ ಅಡಿಕೆ ಗಿಡದ ಫೋಟೋವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಕ್ಯಾಮೆರಾದಿಂದ ಸೆರೆಹಿಡಿಯಿರಿ. "
                    "ನಂತರ ನಾನು ನಿಮ್ಮ ಸಸ್ಯವನ್ನು ತಪಾಸಣೆ ಮಾಡಿ ಬಸವನಹುಳು, ರೋಗಗಳು ಮತ್ತು ಹಾನಿಯ ಬಗ್ಗೆ ವಿವರ ನೀಡುತ್ತೇನೆ!"
                )
            else:
                return (
                    "No plant photograph has been analyzed yet in your current session.\n\n"
                    "Please navigate to the **Image Capture & Upload** page to upload or capture a photo of your arecanut plant. "
                    "Once analyzed, I will provide a full report on snail infestation, disease detection, and damage severity!"
                )

    # 2. General AI / Computer Science / Technology Queries
    if "machine learning" in q or "what is ml" in q or "ಮೆಷಿನ್ ಲರ್ನಿಂಗ್" in query:
        if is_kn:
            return (
                "🤖 **ಮೆಷಿನ್ ಲರ್ನಿಂಗ್ (Machine Learning - ML):**\n\n"
                "ಮೆಷಿನ್ ಲರ್ನಿಂಗ್ ಎನ್ನುವುದು ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆಯ (AI) ಒಂದು ಭಾಗವಾಗಿದ್ದು, ಸ್ಪಷ್ಟವಾಗಿ ಪ್ರೋಗ್ರಾಮ್ ಮಾಡದೆಯೇ ಕಂಪ್ಯೂಟರ್‌ಗಳು ಡೇಟಾದಿಂದ ಕಲಿಯಲು ಅನುವು ಮಾಡಿಕೊಡುತ್ತದೆ.\n\n"
                "• **ಮೇಲ್ವಿಚಾರಣಾ ಕಲಿಕೆ (Supervised Learning):** ಲೇಬಲ್ ಮಾಡಿದ ಡೇಟಾವನ್ನು ಬಳಸಿ ಮುನ್ಸೂಚನೆ ನೀಡುವುದು (ಉದಾಹರಣೆಗೆ ನಮ್ಮ ಅಡಿಕೆ ರೋಗ ವರ್ಗೀಕರಣ).\n"
                "• **ಮೇಲ್ವಿಚಾರಣೆಯಿಲ್ಲದ ಕಲಿಕೆ (Unsupervised Learning):** ಡೇಟಾದಲ್ಲಿನ ಮಾದರಿಗಳು ಮತ್ತು ಗುಂಪುಗಳನ್ನು ಸ್ವಯಂ ಕಂಡುಹಿಡಿಯುವುದು.\n"
                "• **ಬಲವರ್ಧನೆಯ ಕಲಿಕೆ (Reinforcement Learning):** ಬಹುಮಾನ ಮತ್ತು ದಂಡದ ಆಧಾರದ ಮೇಲೆ ಕಲಿಯುವುದು."
            )
        return (
            "🤖 **Machine Learning (ML):**\n\n"
            "Machine Learning is a subset of Artificial Intelligence (AI) that focuses on building systems that learn from data and improve their performance over time without being explicitly programmed.\n\n"
            "• **Supervised Learning:** Trained on labeled datasets (e.g., our YOLOv8 and MobileNetV2 models detecting snails and diseases).\n"
            "• **Unsupervised Learning:** Discovers hidden patterns or clusters in unlabeled data (e.g., K-Means, PCA).\n"
            "• **Reinforcement Learning:** An agent learns through trial, reward, and feedback loops."
        )

    if "artificial intelligence" in q or q == "what is ai" or "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ" in query or "ai ಎಂದರೇನು" in query:
        if is_kn:
            return (
                "🧠 **ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ (Artificial Intelligence - AI):**\n\n"
                "ಮಾನವರಂತೆ ಯೋಚಿಸುವ, ಕಲಿಯುವ, ಸಮಸ್ಯೆಗಳನ್ನು ಪರಿಹರಿಸುವ ಮತ್ತು ನಿರ್ಧಾರಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುವ ಯಂತ್ರಗಳನ್ನು ಅಭಿವೃದ್ಧಿಪಡಿಸುವ ತಂತ್ರಜ್ಞಾನವೇ AI ಆಗಿದೆ.\n\n"
                "ನಮ್ಮ ಯೋಜನೆಯಲ್ಲಿ, ಅಡಿಕೆ ತೋಟಗಳಲ್ಲಿನ ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳುಗಳನ್ನು ಮತ್ತು ರೋಗಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗುರುತಿಸಲು ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ AI ಅನ್ನು ಬಳಸಲಾಗುತ್ತದೆ."
            )
        return (
            "🧠 **Artificial Intelligence (AI):**\n\n"
            "Artificial Intelligence refers to the simulation of human intelligence in machines programmed to think, reason, learn, and make decisions.\n\n"
            "Key branches include:\n"
            "• **Computer Vision:** Enables computers to extract information from images and video (used in this project for snail and disease detection).\n"
            "• **Natural Language Processing (NLP):** Enables machines to understand and generate human speech and text.\n"
            "• **Deep Learning:** Uses multi-layered neural networks to model complex patterns in large datasets."
        )

    if "cnn" in q or "convolutional" in q or "ಕಾನ್ವಲ್ಯೂಷನಲ್" in query:
        if is_kn:
            return (
                "👁️ **ಕಾನ್ವಲ್ಯೂಷನಲ್ ನ್ಯೂರಾಲ್ ನೆಟ್‌ವರ್ಕ್ (CNN):**\n\n"
                "CNN ಎನ್ನುವುದು ಡಿಜಿಟಲ್ ಚಿತ್ರಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲು ವಿನ್ಯಾಸಗೊಳಿಸಲಾದ ಡೀಪ್ ಲರ್ನಿಂಗ್ ನೆಟ್‌ವರ್ಕ್ ಆಗಿದೆ. "
                "ಇದು ಚಿತ್ರದಲ್ಲಿನ ಅಂಚುಗಳು (edges), ಬಣ್ಣಗಳು, ಟೆಕ್ಸ್ಚರ್ ಮತ್ತು ಆಕಾರಗಳನ್ನು ಫಿಲ್ಟರ್‌ಗಳ ಮೂಲಕ ಗುರುತಿಸುತ್ತದೆ.\n\n"
                "ನಮ್ಮ ಯೋಜನೆಯಲ್ಲಿ ಅಡಿಕೆ ಎಲೆಗಳ ರೋಗ ವರ್ಗೀಕರಣಕ್ಕೆ ಮತ್ತು ಹಾನಿಯ ತೀವ್ರತೆ ನಿರ್ಣಯಕ್ಕೆ ಮೊಬೈಲ್‌ನೆಟ್ (MobileNetV2) ಎಂಬ ಪರಿಣಾಮಕಾರಿ CNN ಆರ್ಕಿಟೆಕ್ಚರ್ ಅನ್ನು ಬಳಸಲಾಗಿದೆ."
            )
        return (
            "👁️ **Convolutional Neural Network (CNN):**\n\n"
            "A Convolutional Neural Network (CNN) is a specialized deep neural network designed for processing visual data such as images.\n\n"
            "**Core Layers:**\n"
            "1. **Convolutional Layer:** Applies learnable filters (kernels) to capture spatial features such as edges, gradients, and textures.\n"
            "2. **Activation (ReLU):** Introduces non-linearity to help model complex relationships.\n"
            "3. **Pooling Layer (Max/Average):** Reduces spatial dimensions while retaining essential dominant features.\n"
            "4. **Fully Connected / Dense Layer:** Classifies features into output categories (e.g., Koleroga, Bud Rot, Healthy)."
        )

    if "python" in q or "ಪೈಥಾನ್" in query:
        if is_kn:
            return (
                "🐍 **ಪೈಥಾನ್ ಪ್ರೋಗ್ರಾಮಿಂಗ್ (Python):**\n\n"
                "ಪೈಥಾನ್ ಒಂದು ಜನಪ್ರಿಯ, ಓದಲು ಸುಲಭವಾದ ಹೈ-ಲೆವೆಲ್ ಪ್ರೋಗ್ರಾಮಿಂಗ್ ಭಾಷೆಯಾಗಿದೆ. "
                "ಇದು ಡೇಟಾ ಸೈನ್ಸ್, ಆರ್ಟಿಫಿಶಿಯಲ್ ಇಂಟೆಲಿಜೆನ್ಸ್, ವೆಬ್ ಡೆವಲಪ್‌ಮೆಂಟ್ ಮತ್ತು ಆಟೋಮೇಷನ್‌ಗೆ ವ್ಯಾಪಕವಾಗಿ ಬಳಕೆಯಾಗುತ್ತದೆ.\n\n"
                "ನಮ್ಮ ಯೋಜನೆಯ ಬ್ಯಾಕೆಂಡ್ ಅನ್ನು ಪೈಥಾನ್ ಮತ್ತು ಫಾಸ್ಟ್‌ಎಪಿಐ (FastAPI) ಬಳಸಿ ನಿರ್ಮಿಸಲಾಗಿದೆ."
            )
        return (
            "🐍 **Python Programming:**\n\n"
            "Python is a high-level, interpreted, general-purpose programming language renowned for its readability, simplicity, and extensive ecosystem.\n\n"
            "It is the industry standard for AI, Machine Learning, and Computer Vision, powering frameworks like PyTorch, TensorFlow, OpenCV, and FastAPI (which runs this project's backend)."
        )

    if "computer vision" in q or "yolo" in q:
        if is_kn:
            return (
                "🎯 **ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ಮತ್ತು YOLO:**\n\n"
                "ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ಡಿಜಿಟಲ್ ಚಿತ್ರಗಳಿಂದ ಅರ್ಥಪೂರ್ಣ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯುವ ತಂತ್ರಜ್ಞಾನವಾಗಿದೆ.\n"
                "**YOLO (You Only Look Once):** ಇದು ಅತ್ಯಂತ ವೇಗವಾದ ರಿಯಲ್-ಟೈಮ್ ಆಬ್ಜೆಕ್ಟ್ ಡಿಟೆಕ್ಷನ್ ಮಾದರಿಯಾಗಿದೆ. ನಮ್ಮ ಯೋಜನೆಯಲ್ಲಿ ಇದು ಅಡಿಕೆ ಮರಗಳಲ್ಲಿನ ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳುಗಳನ್ನು ನಿಖರವಾಗಿ ಗುರುತಿಸಿ ಬೌಂಡಿಂಗ್ ಬಾಕ್ಸ್‌ಗಳನ್ನು ರಚಿಸುತ್ತದೆ."
            )
        return (
            "🎯 **Computer Vision & YOLO Object Detection:**\n\n"
            "Computer Vision trains computers to interpret and understand the visual world from digital images and videos.\n\n"
            "• **YOLO (You Only Look Once):** A state-of-the-art single-stage object detector that processes the entire image in one pass, predicting bounding boxes and class probabilities simultaneously. This project employs YOLOv8 to locate and count Giant African Snails in real-time."
        )

    # 3. Project-Specific Snail Questions
    if "snail" in q or "slug" in q or "lissachatina" in q or "ಬಸವನಹುಳು" in query or "ಶಂಕದಹುಳು" in query:
        if is_kn:
            return (
                "🐌 **ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳು (Giant African Snail - Lissachatina fulica) ಸಮಗ್ರ ನಿರ್ವಹಣೆ:**\n\n"
                "1. **ಕೈಯಿಂದ ಆರಿಸುವುದು:** ಮುಂಜಾನೆ (5:30 ರಿಂದ 7:00 ಗಂಟೆಯೊಳಗೆ) ಕೈಗವಸು ಧರಿಸಿ ಸಂಗ್ರಹಿಸಿ 15% ಉಪ್ಪುನೀರಿನಲ್ಲಿ ಹಾಕಿ ನಾಶಮಾಡಿ.\n"
                "2. **ಬೆಲ್ಲದ ಆಮಿಷದ ಬಲೆ:** 100 ಗ್ರಾಂ ಬೆಲ್ಲ + 5 ಗ್ರಾಂ ಈಸ್ಟ್ + ಕಳಿತ ಹಣ್ಣುಗಳನ್ನು ಮಣ್ಣಿನ ಮಡಕೆಯಲ್ಲಿ ನೆಲಮಟ್ಟದಲ್ಲಿ ಇಟ್ಟು ಆಕರ್ಷಿಸಿ.\n"
                "3. **ತಡೆಗೋಡೆಗಳು:** ಅಡಿಕೆ ಮರದ ಬುಡಕ್ಕೆ 15 ಸೆಂ.ಮೀ ಸುಣ್ಣ ಅಥವಾ ಮರದ ಬೂದಿಯ ಉಂಗುರ ಹಾಕಿ ಅಥವಾ ತಾಮ್ರದ ಪಟ್ಟಿ (Copper tape) ಸುತ್ತಿ.\n"
                "4. **ಪರಿಸರ ಸ್ನೇಹಿ ರಾಸಾಯನಿಕ:** ಐರನ್ ಫಾಸ್ಫೇಟ್ (Iron Phosphate 1%) ಗುಳಿಗೆಗಳನ್ನು ತೇವಾಂಶವಿರುವ ನೆರಳಿನಲ್ಲಿ ಹರಡಿ (ಇದು ಪಕ್ಷಿ ಹಾಗೂ ಸಾಕುಪ್ರಾಣಿಗಳಿಗೆ ಸುರಕ್ಷಿತ)."
            )
        return (
            "🐌 **Giant African Snail (Lissachatina fulica) Management Protocol:**\n\n"
            "• **Physical Collection:** Hand-pick snails using rubber gloves at dawn (5:30 AM – 7:00 AM) or after rain. Immerse in a 15% salt (NaCl) solution or boiling water.\n"
            "• **Eco-Friendly Bait:** Distribute Iron (III) Phosphate 1% pellets (5g/m²) in shaded, damp zones. It is safe for domestic pets, birds, and earthworms.\n"
            "• **Fermented Bait Trap:** 100g jaggery/molasses + 5g baker's yeast + mashed bananas in an earthen container flush with the soil surface.\n"
            "• **Trunk Barrier Rings:** Apply a 15–20 cm dry ring of slaked lime (chunam) or wood ash around tree bases, or attach copper barrier tape."
        )

    # 4. Disease Specific Questions
    if "koleroga" in q or "mahali" in q or "fruit rot" in q or "ಕೊಳೆರೋಗ" in query or "ಮಹಾಳಿ" in query:
        if is_kn:
            return (
                "🌿 **ಅಡಿಕೆ ಕೊಳೆರೋಗ (Koleroga / Mahali - Phytophthora meadii):**\n\n"
                "• **ರೋಗಲಕ್ಷಣ:** ಕಾಯಿಗಳ ಮೇಲೆ ನೀರಿನಿಂದ ಕೂಡಿದ ಕಲೆಗಳು ಉಂಟಾಗಿ ಕಾಯಿಗಳು ಉದುರುತ್ತವೆ.\n"
                "• **ನಿರ್ವಹಣೆ:** ಮುಂಗಾರು ಆರಂಭಕ್ಕೆ ಮುನ್ನ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣವನ್ನು (Bordeaux mixture 1%) ಕಾಯಿ ಮತ್ತು ಹಿಂಗಾರಗಳಿಗೆ ಸಿಂಪಡಿಸಿ.\n"
                "• 40-45 ದಿನಗಳ ನಂತರ ಎರಡನೇ ಸಿಂಪಡಣೆ ಮಾಡಿ.\n"
                "• ಮಳೆ ನೀರು ಬೀಳದಂತೆ 100 ಗೇಜ್ ಪಾಲಿಥೀನ್ ಹಾಳೆಗಳಿಂದ ಗೊನೆಗಳನ್ನು ಕಟ್ಟಿ."
            )
        return (
            "🌿 **Koleroga (Mahali / Fruit Rot - Phytophthora meadii):**\n\n"
            "• **Symptoms:** Water-soaked lesions on young developing nuts, followed by dark rot and massive premature fruit drop.\n"
            "• **Prophylactic Spray:** Spray 1% freshly prepared Bordeaux mixture (1kg Copper Sulphate + 1kg Lime in 100L water) covering all bunches prior to monsoon.\n"
            "• **Follow-Up:** Repeat 40–45 days later during a monsoon dry break.\n"
            "• **Bunch Covering:** Cover developing bunches with 100-gauge UV-stabilized polythene sheets."
        )

    if "bud rot" in q or "ಸುಳಿ ಕೊಳೆ" in query:
        if is_kn:
            return (
                "🌱 **ಸುಳಿಕೊಳೆ ರೋಗ (Bud Rot - Phytophthora palmivora):**\n\n"
                "• **ರೋಗಲಕ್ಷಣ:** ಸುಳಿ ಎಲೆಯು ಹಳದಿ ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಕೊಳೆಯುತ್ತದೆ, ಎಳೆದರೆ ಸುಲಭವಾಗಿ ಕೈಗೆ ಬರುತ್ತದೆ.\n"
                "• **ಚಿಕಿತ್ಸೆ:** ಕೊಳೆತ ಭಾಗವನ್ನು ಚಾಕುವಿನಿಂದ ಸ್ವಚ್ಛಗೊಳಿಸಿ 10% ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಅಥವಾ ತಾಮ್ರದ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಪೇಸ್ಟ್ ಹಚ್ಚಿ ಪಾಲಿಥೀನ್ ಹೊದಿಕೆಯಿಂದ ಮುಚ್ಚಿ."
            )
        return (
            "🌱 **Bud Rot (Apical Decay - Phytophthora palmivora):**\n\n"
            "• **Symptoms:** Yellowing of the central spindle, foul odor, and rotting of the inner growing apical bud.\n"
            "• **Surgical Debridement:** Excise all necrotic soft tissue with a sterile blade.\n"
            "• **Paste Application:** Dress the exposed wound with 10% Bordeaux paste or Copper Oxychloride paste, and cap with a protective plastic cone."
        )

    if "yellow leaf" in q or "yld" in q or "ಹಳದಿ ಎಲೆ" in query:
        if is_kn:
            return (
                "🍂 **ಹಳದಿ ಎಲೆ ರೋಗ (Yellow Leaf Disease - Phytoplasma):**\n\n"
                "• **ರೋಗಲಕ್ಷಣ:** ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುವುದು, ಗರಿಗಳು ಕುಗ್ಗಿ ಇಳುವರಿ ಕಡಿಮೆಯಾಗುವುದು.\n"
                "• **ನಿರ್ವಹಣೆ:** ಪೊಟ್ಯಾಶ್ ಗೊಬ್ಬರ ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರ ನೀಡಿ. ಸತು ಮತ್ತು ಮೆಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಸಿಂಪಡಿಸಿ. ತೋಟದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿದು ಹೋಗಲು ಕಾಲುವೆ ನಿರ್ಮಿಸಿ."
            )
        return (
            "🍂 **Yellow Leaf Disease (YLD - Phytoplasma organism):**\n\n"
            "• **Symptoms:** Chlorosis beginning in the outer lower whorls, tip necrosis, and root end decay.\n"
            "• **Integrated Protocol:** Apply balanced N:P:K (100:40:140 g/palm/year) + 12kg compost. Foliar application of Zinc Sulphate (0.5%) and Magnesium Sulphate (0.5%)."
        )

    if "ring spot" in q or "ರಿಂಗ್ ಸ್ಪಾಟ್" in query:
        if is_kn:
            return (
                "🟡 **ಅಡಿಕೆ ರಿಂಗ್ ಸ್ಪಾಟ್ ರೋಗ (Ring Spot):**\n\n"
                "• **ರೋಗಲಕ್ಷಣ:** ಎಲೆಗಳ ಮೇಲೆ ಹಳದಿ ಅಂಚುಳ್ಳ ದುಂಡಗಿನ ಕಂದು ಕಲೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ.\n"
                "• **ನಿರ್ವಹಣೆ:** ಮ್ಯಾಂಕೋಜೆಬ್ 75 WP (Mancozeb 2g/L) ಅಥವಾ ತಾಮ್ರದ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಸಿಂಪಡಿಸಿ."
            )
        return (
            "🟡 **Ring Spot Disease:**\n\n"
            "• **Symptoms:** Concentric chlorotic rings with brownish necrotic centers on mature foliage.\n"
            "• **Management:** Spray Mancozeb 75 WP (2g/L) or Copper Oxychloride 50 WP (2.5g/L). Prune severely blighted leaflets."
        )

    # 5. Home remedies / Organic remedies
    if "home remed" in q or "organic" in q or "ಮನೆಮದ್ದು" in query or "ನೈಸರ್ಗಿಕ" in query:
        if is_kn:
            return (
                "🏡 **ಅಡಿಕೆ ತೋಟಕ್ಕೆ ನೈಸರ್ಗಿಕ ಮನೆಮದ್ದುಗಳು ಮತ್ತು ಸಾವಯವ ಪರಿಹಾರಗಳು:**\n\n"
                "1. **ಉಪ್ಪುನೀರಿನ ನಿರ್ಮೂಲನೆ (15% Brine):** ಸಂಗ್ರಹಿಸಿದ ಬಸವನಹುಳುಗಳನ್ನು 15% ಕಲ್ಲುಪ್ಪಿನ ನೀರಿನಲ್ಲಿ ಹಾಕಿ ನಾಶಪಡಿಸಿ.\n"
                "2. **ಸುಣ್ಣ ಮತ್ತು ಬೂದಿಯ ಉಂಗುರ:** ಅಡಿಕೆ ಮರದ ಬುಡದಲ್ಲಿ 15 ಸೆಂ.ಮೀ ಅಗಲದ ಸುಣ್ಣ ಅಥವಾ ಒಣ ಮರದ ಬೂದಿಯ ಉಂಗುರ ನಿರ್ಮಿಸಿ. ಇದು ಬಸವನಹುಳು ಮರ ಹತ್ತುವುದನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತಡೆಯುತ್ತದೆ.\n"
                "3. **ಬೆಲ್ಲ ಮತ್ತು ಈಸ್ಟ್ ಬಲೆ:** ಮಣ್ಣಿನ ಬಟ್ಟಲಿನಲ್ಲಿ ಬೆಲ್ಲದ ದ್ರಾವಣ ಮತ್ತು ಈಸ್ಟ್ ಹಾಕಿ ನೆಲದಲ್ಲಿ ಹೂತಿಡಿ; ಹುಳುಗಳು ವಾಸನೆಗೆ ಆಕರ್ಷಿತವಾಗಿ ಬೀಳುತ್ತವೆ.\n"
                "4. **ಬೋರ್ಡೋ ಪೇಸ್ಟ್ (10%):** ಗಾಯಗೊಂಡ ಕಾಂಡ ಮತ್ತು ಕೊಳೆತ ಭಾಗಗಳಿಗೆ ತಕ್ಷಣ ಹಚ್ಚಿ ರೋಗಾಣು ಪ್ರವೇಶ ತಡೆಯಿರಿ."
            )
        return (
            "🏡 **Safe Home Remedies & Eco-Friendly Plantation Solutions:**\n\n"
            "1. **15% Salt Brine Immersion:** Submerge collected snails into a saturated salt-water bucket (150g table salt per 1L water) for humane and complete eradication.\n"
            "2. **Slaked Lime & Wood Ash Barrier Rings:** Create a 15–20 cm dry ring of slaked lime (chunam) or sifted wood ash around every palm base. Snails will not cross this abrasive, desiccating border.\n"
            "3. **Fermented Jaggery-Yeast Siphon Traps:** Set shallow pans with fermented molasses/jaggery water flush with the ground under shady mulched beds.\n"
            "4. **Copper Foil Banding:** Wrap a 2-inch band of copper tape around younger palms; it produces a harmless natural electro-chemical deterrent to snails.\n"
            "5. **10% Bordeaux Paste:** Apply as a prophylactic healing sealant to wounded palm tissues."
        )

    # 6. Conversational Greetings
    if any(g in q for g in ["hello", "hi", "hey", "good morning", "good evening", "namaste", "ನಮಸ್ಕಾರ"]):
        if is_kn:
            return (
                "ನಮಸ್ಕಾರ! ನಾನು **ArecaKisan AI**.\n\n"
                "ನಾನು ಸಾಮಾನ್ಯ AI ಮತ್ತು ತಾಂತ್ರಿಕ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಬಲ್ಲೆ, ಹಾಗೆಯೇ ಅಡಿಕೆ ತೋಟಗಾರಿಕೆ, ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳು ನಿಯಂತ್ರಣ, ರೋಗ ಪತ್ತೆ ಮತ್ತು ಮನೆಮದ್ದುಗಳ ಬಗ್ಗೆ ಸಂಪೂರ್ಣ ಮಾಹಿತಿ ನೀಡಬಲ್ಲೆ.\n\n"
                "ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"
            )
        return (
            "Hello! I am **ArecaKisan AI**, your versatile general AI assistant and plantation expert.\n\n"
            "I can answer:\n"
            "• **General Knowledge & Tech:** Artificial Intelligence, Machine Learning, CNNs, Python, and everyday questions.\n"
            "• **Arecanut Health:** Koleroga, Bud Rot, Yellow Leaf, and Ring Spot management.\n"
            "• **Snail Infestation:** Giant African Snail control, barriers, and organic home remedies.\n"
            "• **Live Scan Analysis:** Interpret your current plant photograph and detection results.\n\n"
            "How can I assist you today?"
        )

    # 7. General Knowledge Open-Ended Fallback
    if is_kn:
        return (
            f"ನಾನು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ: '{query}'.\n\n"
            "ನಾನು ಆರ್ಟಿಫಿಶಿಯಲ್ ಇಂಟೆಲಿಜೆನ್ಸ್, ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್, ಅಡಿಕೆ ಕೃಷಿ, ಬಸವನಹುಳು ನಿಯಂತ್ರಣ ಮತ್ತು ನಿಮ್ಮ ಸಸ್ಯದ ತಪಾಸಣಾ ಫಲಿತಾಂಶಗಳ ಕುರಿತು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. "
            "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನಿರ್ದಿಷ್ಟವಾಗಿ ಕೇಳಿ ಅಥವಾ ಸಸ್ಯದ ಫೋಟೋ ತಪಾಸಣೆಗಾಗಿ Image Upload ಪುಟವನ್ನು ಬಳಸಿ!"
        )
    return (
        f"Thank you for your question: '{query}'.\n\n"
        "As your AI assistant, I can assist you with general topics (AI, Machine Learning, Python, computer vision), "
        "as well as specialized arecanut farming practices, Giant African Snail eradication, and interpreting your plant scans. "
        "Could you please specify your question, or ask about any AI concept or crop management practice?"
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """
    Multilingual conversation endpoint. Uses Gemini if configured; falls back to
    intelligent general-purpose AI and agronomic engine smoothly.
    """
    user_msg = (body.message or "").strip()
    if not user_msg:
        raise HTTPException(400, "Message cannot be empty.")

    session_id = body.session_id or str(uuid.uuid4())
    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]
    history.append({"role": "user", "content": user_msg})

    reply_text = ""

    # Attempt Gemini API call if key configured
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)

            # Enrich system prompt with current analysis context if provided
            analysis_context = ""
            if body.current_analysis:
                analysis_context = f"\n\nCURRENT ANALYSIS CONTEXT OF USER'S PLANT SCAN:\n{body.current_analysis}"

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT + analysis_context
            )
            # Format chat history
            chat_session = model.start_chat(history=[
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in history[:-1]
            ])
            response = chat_session.send_message(user_msg)
            reply_text = response.text
        except Exception as e:
            logger.warning("Gemini API call failed, falling back to local advisory engine: %s", e)
            reply_text = _generate_fallback_response(user_msg, body.language, body.current_analysis)
    else:
        reply_text = _generate_fallback_response(user_msg, body.language, body.current_analysis)

    history.append({"role": "assistant", "content": reply_text})

    # Limit session history to last 20 messages
    if len(history) > 20:
        _sessions[session_id] = history[-20:]

    return ChatResponse(reply=reply_text, session_id=session_id)
