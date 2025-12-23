"""
IndicTrans2 Translation API Routes
Provides REST API endpoints for neural machine translation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from app.indictrans2_service import indictrans2_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translate", tags=["Translation"])

# ============ MODELS ============

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate", min_length=1, max_length=5000)
    source_lang: str = Field(..., description="Source language code (e.g., 'en', 'hi', 'ta')")
    target_lang: str = Field(..., description="Target language code")
    use_cache: Optional[bool] = Field(True, description="Use cached translations")

class BatchTranslateRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to translate", max_items=50)
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")

class TranslateResponse(BaseModel):
    success: bool
    translation: Optional[str] = None
    source_lang: str
    target_lang: str
    source_text: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None

# ============ ENDPOINTS ============

@router.post("/", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text using IndicTrans2 neural translation
    
    Supports 22+ Indian languages + English with high accuracy
    """
    try:
        result = await indictrans2_service.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            use_cache=request.use_cache
        )
        
        return TranslateResponse(**result)
        
    except Exception as e:
        logger.error(f"Translation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_translate(request: BatchTranslateRequest):
    """
    Translate multiple texts in batch for efficiency
    
    Maximum 50 texts per request
    """
    try:
        if len(request.texts) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 texts allowed per batch request"
            )
        
        results = await indictrans2_service.batch_translate(
            texts=request.texts,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return {
            "success": True,
            "total_texts": len(request.texts),
            "translations": results
        }
        
    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    
    Returns all language codes supported by IndicTrans2
    """
    return {
        "success": True,
        "languages": indictrans2_service.get_supported_languages(),
        "total_languages": len(indictrans2_service.get_supported_languages()),
        "language_details": indictrans2_service.SUPPORTED_LANGUAGES
    }


@router.get("/language-pairs")
async def get_language_pairs():
    """
    Get all supported language pairs
    
    Returns all possible source→target combinations
    """
    pairs = indictrans2_service.get_language_pairs()
    
    return {
        "success": True,
        "total_pairs": len(pairs),
        "language_pairs": [
            {"source": src, "target": tgt}
            for src, tgt in pairs[:100]  # Limit response size
        ],
        "note": f"Showing first 100 of {len(pairs)} total pairs"
    }


@router.get("/status")
async def translation_service_status():
    """
    Check translation service status
    
    Returns model loading status and availability
    """
    return {
        "service": "IndicTrans2 Translation",
        "status": "available" if indictrans2_service.is_available() else "loading",
        "model_loaded": indictrans2_service.model_loaded,
        "gpu_enabled": indictrans2_service.use_gpu,
        "supported_languages": len(indictrans2_service.get_supported_languages()),
        "model_name": indictrans2_service.model_name
    }


@router.post("/auto-translate")
async def auto_translate(
    text: str = Query(..., description="Text to translate"),
    target_lang: str = Query(..., description="Target language code"),
    detect_source: bool = Query(True, description="Auto-detect source language")
):
    """
    Auto-detect source language and translate
    
    Combines language detection with translation
    """
    try:
        # Detect source language if requested
        if detect_source:
            from app.language_utils import language_manager
            detected = language_manager.detect_language(text)
            source_lang = detected
        else:
            source_lang = "en"  # Default to English
        
        # Translate
        result = await indictrans2_service.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        return {
            **result,
            "detected_source_lang": source_lang if detect_source else None
        }
        
    except Exception as e:
        logger.error(f"Auto-translate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
