"""
AI Wellness Companion API Endpoints
Complete REST API for the AI Wellness Companion system
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.companion_system import (
    companion_manager,
    CompanionStatus,
    CaseStatus,
    InterventionType
)
from app.database import db_manager
from app.language_utils import LanguageManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/companion", tags=["AI Wellness Companion"])

# Initialize language manager
lang_manager = LanguageManager()

# ============ REQUEST/RESPONSE MODELS ============

class StartJourneyRequest(BaseModel):
    user_id: str = Field(..., description="Patient's unique ID")
    health_concern: str = Field(..., description="Main health concern")
    language: Optional[str] = Field("en", description="Preferred language (en/hi/ta)")
    initial_symptoms: Optional[List[str]] = Field(None, description="List of initial symptoms")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional user metadata")

class StartJourneyResponse(BaseModel):
    success: bool
    journey_id: Optional[str]
    message: str
    welcome_message: str

class ChatRequest(BaseModel):
    journey_id: str = Field(..., description="Companion journey ID")
    message: str = Field(..., description="Patient's message")
    language: Optional[str] = Field("en", description="Message language")

class ChatResponse(BaseModel):
    success: bool
    response: str
    language: str
    detected_language: str
    intervention_type: str
    metadata: Dict[str, Any]

class CreateCaseRequest(BaseModel):
    journey_id: str
    user_id: str
    doctor_id: str
    diagnosis: str
    prescription_id: Optional[str] = None
    diet_plan: Optional[Dict[str, Any]] = None
    treatment_duration_days: int = 30
    follow_up_schedule: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class CreateCaseResponse(BaseModel):
    success: bool
    case_id: Optional[str]
    message: str

class UpdateProgressRequest(BaseModel):
    case_id: str
    progress_percentage: float
    adherence_score: float
    notes: Optional[str] = None

class MilestoneRequest(BaseModel):
    journey_id: str
    milestone_type: str
    description: str
    metadata: Optional[Dict[str, Any]] = None

# ============ COMPANION JOURNEY ENDPOINTS ============

@router.post("/journey/start", response_model=StartJourneyResponse)
async def start_companion_journey(request: StartJourneyRequest):
    """
    Start a new AI Wellness Companion journey
    
    The companion will stay with the patient throughout their health journey
    until their concern is resolved, providing:
    - Regular check-ins
    - Medicine reminders
    - Diet guidance
    - Symptom tracking
    - Educational content
    - Emotional support
    """
    try:
        # Create companion journey
        journey_id = await companion_manager.start_companion_journey(
            user_id=request.user_id,
            health_concern=request.health_concern,
            language=request.language,
            initial_symptoms=request.initial_symptoms,
            metadata=request.metadata
        )
        
        if not journey_id:
            raise HTTPException(status_code=500, detail="Failed to start companion journey")
        
        # Create Supabase chat session
        session_id = await db_manager.create_chat_session(
            user_id=request.user_id,
            language=request.language
        )
        
        # Generate welcome message
        # Import here to avoid circular dependency
        from main_enhanced import model_inference
        
        welcome_prompt = f"""Welcome a new patient starting their wellness journey for {request.health_concern}. Provide a warm, supportive greeting that introduces yourself as Astra, their AI Wellness Companion."""
        
        if model_inference:
            welcome_message = await model_inference.generate_response(
                prompt=welcome_prompt,
                language=request.language,
                context=f"Health concern: {request.health_concern}"
            )
        else:
            welcome_message = f"Welcome! I'm Astra, your AI Wellness Companion. I'm here to support you with {request.health_concern}. How are you feeling today?"
        
        # Save welcome message
        if session_id:
            await db_manager.save_chat_message(
                session_id=session_id,
                user_message=f"Starting journey for {request.health_concern}",
                assistant_response=welcome_message,
                language=request.language,
                metadata={"journey_id": journey_id, "type": "welcome"}
            )
        
        return StartJourneyResponse(
            success=True,
            journey_id=journey_id,
            message="Companion journey started successfully",
            welcome_message=welcome_message
        )
        
    except Exception as e:
        logger.error(f"Error starting companion journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def companion_chat(request: ChatRequest):
    """
    Chat with AI Wellness Companion with full context awareness
    
    The companion:
    - Remembers conversation history
    - Tracks health progress
    - Provides personalized guidance
    - Detects when escalation is needed
    - Supports multilingual conversations
    """
    try:
        # Get journey details for context
        journey = await companion_manager.get_journey(request.journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        # Detect language if not provided
        detected_lang = request.language
        if not detected_lang or detected_lang == "auto":
            detected_lang = lang_manager.detect_language(request.message)
        
        # Get chat history for context
        chat_history = []
        if hasattr(db_manager, 'client') and db_manager.client:
            # Get Supabase chat history
            sessions = await db_manager.get_user_sessions(journey["user_id"], limit=1)
            if sessions:
                history = await db_manager.get_chat_history(sessions[0]["id"], limit=10)
                chat_history = [
                    {"role": "user", "content": msg["user_message"]}
                    for msg in history
                ] + [
                    {"role": "assistant", "content": msg["assistant_response"]}
                    for msg in history
                ]
        
        # Build context-aware prompt
        # Import here to avoid circular dependency
        from main_enhanced import model_inference
        
        context_prompt = f"""You are Astra, an AI Wellness Companion supporting a patient with {journey['health_concern']}. Patient's message: {request.message}. Provide supportive Ayurvedic guidance in {detected_lang} language."""
        
        # Generate AI response
        if model_inference:
            ai_response = await model_inference.generate_response(
                prompt=context_prompt,
                language=detected_lang,
                context=f"Journey: {journey['health_concern']}"
            )
        else:
            ai_response = "I understand your concern. Let me provide some Ayurvedic guidance to help you feel better."
        
        # Determine intervention type
        intervention_type = InterventionType.CHECK_IN.value
        if any(word in request.message.lower() for word in ["medicine", "medication", "reminder"]):
            intervention_type = InterventionType.MEDICATION_REMINDER.value
        elif any(word in request.message.lower() for word in ["diet", "food", "eat"]):
            intervention_type = InterventionType.DIET_REMINDER.value
        elif any(word in request.message.lower() for word in ["symptom", "pain", "sick", "fever"]):
            intervention_type = InterventionType.SYMPTOM_ASSESSMENT.value
        elif any(word in request.message.lower() for word in ["doctor", "urgent", "emergency", "severe"]):
            intervention_type = InterventionType.ESCALATION.value
        
        # Log interaction
        await companion_manager.log_interaction(
            journey_id=request.journey_id,
            interaction_type=intervention_type,
            content=ai_response,
            language=detected_lang,
            metadata={"user_message": request.message}
        )
        
        # Save to Supabase chat history
        sessions = await db_manager.get_user_sessions(journey["user_id"], limit=1)
        if sessions:
            await db_manager.save_chat_message(
                session_id=sessions[0]["id"],
                user_message=request.message,
                assistant_response=ai_response,
                language=detected_lang,
                metadata={
                    "journey_id": request.journey_id,
                    "intervention_type": intervention_type
                }
            )
        
        return ChatResponse(
            success=True,
            response=ai_response,
            language=request.language or "en",
            detected_language=detected_lang,
            intervention_type=intervention_type,
            metadata={
                "journey_status": journey["status"],
                "interaction_count": journey["interaction_count"] + 1
            }
        )
        
    except Exception as e:
        logger.error(f"Error in companion chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey/{journey_id}")
async def get_journey(journey_id: str):
    """Get companion journey details"""
    try:
        journey = await companion_manager.get_journey(journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        return {"success": True, "journey": journey}
        
    except Exception as e:
        logger.error(f"Error getting journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey/user/{user_id}")
async def get_user_journeys(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 20
):
    """Get all journeys for a user"""
    try:
        companion_status = CompanionStatus(status) if status else None
        journeys = await companion_manager.get_user_journeys(
            user_id=user_id,
            status=companion_status,
            limit=limit
        )
        
        return {
            "success": True,
            "journeys": journeys,
            "total": len(journeys)
        }
        
    except Exception as e:
        logger.error(f"Error getting user journeys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/journey/{journey_id}/status")
async def update_journey_status(
    journey_id: str,
    status: str,
    resolution_notes: Optional[str] = None
):
    """Update journey status (active, monitoring, resolved, etc.)"""
    try:
        companion_status = CompanionStatus(status)
        success = await companion_manager.update_journey_status(
            journey_id=journey_id,
            status=companion_status,
            resolution_notes=resolution_notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update journey status")
        
        return {
            "success": True,
            "message": f"Journey status updated to {status}"
        }
        
    except Exception as e:
        logger.error(f"Error updating journey status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ CASE MANAGEMENT ENDPOINTS ============

@router.post("/case/create", response_model=CreateCaseResponse)
async def create_health_case(request: CreateCaseRequest):
    """
    Create a health case after doctor consultation
    
    Creates a comprehensive case with:
    - Diagnosis and prescription
    - Diet plan and lifestyle recommendations
    - Treatment timeline and follow-up schedule
    - Ongoing companion support
    """
    try:
        case_id = await companion_manager.create_case(
            journey_id=request.journey_id,
            user_id=request.user_id,
            doctor_id=request.doctor_id,
            diagnosis=request.diagnosis,
            prescription_id=request.prescription_id,
            diet_plan=request.diet_plan,
            treatment_duration_days=request.treatment_duration_days,
            follow_up_schedule=request.follow_up_schedule,
            metadata=request.metadata
        )
        
        if not case_id:
            raise HTTPException(status_code=500, detail="Failed to create case")
        
        return CreateCaseResponse(
            success=True,
            case_id=case_id,
            message=f"Case created successfully. Companion will support patient for {request.treatment_duration_days} days."
        )
        
    except Exception as e:
        logger.error(f"Error creating case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case/{case_id}")
async def get_case(case_id: str):
    """Get case details"""
    try:
        case = await companion_manager.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return {"success": True, "case": case}
        
    except Exception as e:
        logger.error(f"Error getting case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/case/progress")
async def update_case_progress(request: UpdateProgressRequest):
    """
    Update case progress and adherence
    
    Tracks:
    - Treatment progress (0-100%)
    - Medication adherence score
    - Symptom improvement
    - Diet compliance
    """
    try:
        success = await companion_manager.update_case_progress(
            case_id=request.case_id,
            progress_percentage=request.progress_percentage,
            adherence_score=request.adherence_score,
            notes=request.notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update case progress")
        
        # Auto-resolve journey if case is 100% complete
        if request.progress_percentage >= 100:
            case = await companion_manager.get_case(request.case_id)
            if case:
                await companion_manager.update_journey_status(
                    journey_id=case["journey_id"],
                    status=CompanionStatus.RESOLVED,
                    resolution_notes="Treatment completed successfully"
                )
        
        return {
            "success": True,
            "message": f"Progress updated to {request.progress_percentage}%"
        }
        
    except Exception as e:
        logger.error(f"Error updating case progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ MILESTONE & HEALTH RECORDS ENDPOINTS ============

@router.post("/milestone/add")
async def add_milestone(request: MilestoneRequest):
    """Add a milestone achievement to the journey"""
    try:
        success = await companion_manager.add_milestone(
            journey_id=request.journey_id,
            milestone_type=request.milestone_type,
            description=request.description,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add milestone")
        
        return {
            "success": True,
            "message": "Milestone added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding milestone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey/{journey_id}/records")
async def get_journey_health_records(journey_id: str):
    """Get all health records (Storj documents) linked to a journey"""
    try:
        records = await companion_manager.get_journey_records(journey_id)
        
        return {
            "success": True,
            "records": records,
            "total": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error getting journey records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/journey/{journey_id}/link-record")
async def link_health_record(
    journey_id: str,
    record_type: str = Body(...),
    storj_document_id: str = Body(...),
    description: str = Body(...)
):
    """Link a Storj health record to the journey"""
    try:
        success = await companion_manager.link_health_record(
            journey_id=journey_id,
            record_type=record_type,
            storj_document_id=storj_document_id,
            description=description
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link health record")
        
        return {
            "success": True,
            "message": "Health record linked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error linking health record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ CONVERSATION HISTORY ENDPOINTS ============

@router.get("/conversation/{user_id}")
async def get_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50
):
    """
    Get conversation history from Supabase
    
    Returns full chat history with:
    - User messages
    - AI responses
    - Timestamps
    - Language detection
    - Metadata
    """
    try:
        if session_id:
            # Get specific session history
            history = await db_manager.get_chat_history(session_id, limit=limit)
        else:
            # Get all user sessions
            sessions = await db_manager.get_user_sessions(user_id, limit=1)
            if sessions:
                history = await db_manager.get_chat_history(sessions[0]["id"], limit=limit)
            else:
                history = []
        
        return {
            "success": True,
            "conversation": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
