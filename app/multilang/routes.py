"""
Multi-Language API Routes for Medicine Reminder System
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging

from app.language_utils import language_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multilang", tags=["Multi-Language Support"])

class LanguageDetectionRequest(BaseModel):
    text: str = Field(..., description="Text to detect language from")
    require_confirmation: bool = Field(default=True, description="Whether to require confirmation for uncertain detections")

class LanguageConfirmationRequest(BaseModel):
    text: str = Field(..., description="Original text")
    confirmed_language: str = Field(..., description="User-confirmed language code")
    detection_id: Optional[str] = Field(default=None, description="Detection tracking ID")

class TranslationRequest(BaseModel):
    key: str = Field(..., description="Translation key")
    language: str = Field(default='en', description="Target language code")
    variables: Optional[Dict] = Field(default={}, description="Variables for text formatting")

class MultilingualReminderRequest(BaseModel):
    patient_name: str = Field(..., description="Patient name")
    medicine_name: str = Field(..., description="Medicine name")
    dosage: str = Field(..., description="Medicine dosage")
    timing_type: str = Field(..., description="Timing type (morning/afternoon/evening/night/before_food/after_food)")
    language: str = Field(default='en', description="Language code (en/ta/hi)")

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        return {
            "success": True,
            "languages": language_manager.SUPPORTED_LANGUAGES,
            "total_languages": len(language_manager.SUPPORTED_LANGUAGES)
        }
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported languages: {str(e)}")

@router.post("/detect-language")
async def detect_language(request: LanguageDetectionRequest):
    """Enhanced language detection with confidence thresholds and graceful fallback"""
    try:
        # Use enhanced detection method
        detection_result = language_manager.enhanced_language_detection(request.text)
        
        # Honor require_confirmation parameter
        if not request.require_confirmation and detection_result.get('requires_confirmation'):
            # If user doesn't want confirmation prompts, use the detected/suggested language
            detection_result['requires_confirmation'] = False
            if 'suggested_language' in detection_result:
                detection_result['language'] = detection_result['suggested_language']
                # Clear the uncertain detection fields since we're using the suggestion
                detection_result.pop('detected_language', None)
                detection_result.pop('confirmation_message', None)
        
        # Get language name for the result
        primary_language = detection_result.get('language') or detection_result.get('suggested_language', 'en')
        language_name = language_manager.SUPPORTED_LANGUAGES.get(primary_language, "English")
        
        # Add keyword validation if detection was successful
        if detection_result.get('language') and detection_result.get('confidence', 0) > 0.6:
            keyword_validation = language_manager.validate_detection_with_keywords(
                request.text, 
                detection_result['language']
            )
            detection_result.update(keyword_validation)
        
        return {
            "success": True,
            "detection_result": detection_result,
            "primary_language": primary_language,
            "language_name": language_name,
            "input_text": request.text,
            "enhanced_detection": True
        }
    except Exception as e:
        logger.error(f"Error in enhanced language detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to detect language: {str(e)}")

@router.post("/confirm-language")
async def confirm_language(request: LanguageConfirmationRequest):
    """Confirm user's language choice and log telemetry"""
    try:
        # Validate confirmed language is supported
        if request.confirmed_language not in language_manager.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400, 
                detail=f"Language '{request.confirmed_language}' is not supported"
            )
        
        # Log confirmation telemetry
        logger.info(
            "Language confirmation received",
            extra={
                'confirmed_language': request.confirmed_language,
                'text_length': len(request.text),
                'detection_id': request.detection_id,
                'user_confirmation': True
            }
        )
        
        # Re-run detection to compare with user confirmation
        detection_result = language_manager.enhanced_language_detection(request.text)
        was_correct = detection_result.get('language') == request.confirmed_language
        
        return {
            "success": True,
            "confirmed_language": request.confirmed_language,
            "language_name": language_manager.SUPPORTED_LANGUAGES[request.confirmed_language],
            "detection_was_correct": was_correct,
            "original_detection": detection_result.get('language'),
            "confidence_score": detection_result.get('confidence', 0.0),
            "telemetry_logged": True
        }
    except Exception as e:
        logger.error(f"Error confirming language: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm language: {str(e)}")

@router.get("/detection-telemetry")
async def get_detection_telemetry():
    """Get language detection telemetry and performance metrics"""
    try:
        telemetry = language_manager.get_detection_telemetry()
        return {
            "success": True,
            "telemetry": telemetry,
            "timestamp": "2025-09-19T16:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get telemetry: {str(e)}")

@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """Get translation for a specific key and language"""
    try:
        translation = language_manager.get_translation(
            key=request.key,
            language=request.language,
            **(request.variables or {})
        )
        
        return {
            "success": True,
            "translation": translation,
            "language": request.language,
            "key": request.key
        }
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.post("/create-multilingual-reminder")
async def create_multilingual_reminder(request: MultilingualReminderRequest):
    """Create a complete medicine reminder in specified language"""
    try:
        reminder_message = language_manager.create_multilingual_reminder(
            patient_name=request.patient_name,
            medicine_name=request.medicine_name,
            dosage=request.dosage,
            timing_type=request.timing_type,
            language=request.language
        )
        
        language_name = language_manager.get_supported_languages().get(request.language, "Unknown")
        
        return {
            "success": True,
            "reminder_message": reminder_message,
            "language": request.language,
            "language_name": language_name,
            "patient_name": request.patient_name,
            "medicine_name": request.medicine_name
        }
    except Exception as e:
        logger.error(f"Error creating multilingual reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create reminder: {str(e)}")

@router.get("/test-translations/{language}")
async def test_translations(language: str):
    """Test all available translations for a specific language"""
    try:
        if language not in language_manager.get_supported_languages():
            raise HTTPException(status_code=400, detail=f"Language '{language}' not supported")
        
        # Test key translations
        test_translations = {}
        test_keys = [
            'reminder_greeting', 'time_for_medicine', 'take_dosage',
            'timing_morning', 'timing_evening', 'response_options',
            'medicine_taken', 'medicine_skipped', 'footer'
        ]
        
        for key in test_keys:
            test_translations[key] = language_manager.get_translation(
                key, language, 
                patient_name="Test Patient",
                medicine_name="Test Medicine", 
                dosage="500mg"
            )
        
        return {
            "success": True,
            "language": language,
            "language_name": language_manager.get_supported_languages()[language],
            "translations": test_translations
        }
    except Exception as e:
        logger.error(f"Error testing translations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation test failed: {str(e)}")

@router.post("/create-response-confirmation")
async def create_response_confirmation(
    response_type: str,
    language: str = 'en',
    patient_name: Optional[str] = None,
    medicine_name: Optional[str] = None
):
    """Create response confirmation message in specified language"""
    try:
        kwargs = {}
        if patient_name:
            kwargs['patient_name'] = patient_name
        if medicine_name:
            kwargs['medicine_name'] = medicine_name
        
        confirmation_message = language_manager.create_response_confirmation(
            response_type=response_type,
            language=language,
            **kwargs
        )
        
        return {
            "success": True,
            "confirmation_message": confirmation_message,
            "response_type": response_type,
            "language": language
        }
    except Exception as e:
        logger.error(f"Error creating response confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create confirmation: {str(e)}")