"""
AI Wellness Companion API Endpoints - HARDENED VERSION
Production-ready with ModelService integration and context-aware AI
Fixed Bug #20: Added input sanitization
"""

from fastapi import APIRouter, HTTPException, Body, Depends, Request
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
from app.model_service import model_service, ChatMessage
from app.auth_middleware import rate_limit_check, get_current_user
from app.input_sanitizer import sanitize_message, sanitize_text, sanitize_patient_id

logger = logging.getLogger(__name__)

# Router with automatic rate limiting dependency
router = APIRouter(
    prefix="/api/companion", 
    tags=["AI Wellness Companion"],
    dependencies=[Depends(rate_limit_check)]  # Apply rate limiting to all endpoints
)

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
async def start_companion_journey(
    data: StartJourneyRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Start a new AI Wellness Companion journey - HARDENED
    
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
        # Create companion journey (always succeeds, even without DB)
        journey_id = await companion_manager.start_companion_journey(
            user_id=data.user_id,
            health_concern=data.health_concern,
            language=data.language,
            initial_symptoms=data.initial_symptoms,
            metadata=data.metadata
        )
        
        if not journey_id:
            raise HTTPException(status_code=500, detail="Failed to start companion journey")
        
        # Create Supabase chat session (may fail gracefully)
        session_id = None
        try:
            session_id = await db_manager.create_chat_session(
                user_id=data.user_id,
                language=data.language
            )
        except Exception as e:
            logger.warning(f"Could not create chat session (continuing anyway): {e}")
        
        # Generate welcome message with AI
        welcome_prompt = f"Welcome a new patient starting their wellness journey for {data.health_concern}. Introduce yourself as Astra, their AI Wellness Companion, and ask how they're feeling."
        
        context = f"Health concern: {data.health_concern}"
        if data.initial_symptoms:
            context += f". Initial symptoms: {', '.join(data.initial_symptoms)}"
        
        welcome_message = await model_service.generate_response(
            prompt=welcome_prompt,
            language=data.language,
            context=context,
            max_length=300
        )
        
        # Save welcome message (if we have a session)
        if session_id:
            try:
                await db_manager.save_chat_message(
                    session_id=session_id,
                    user_message=f"Starting journey for {data.health_concern}",
                    assistant_response=welcome_message,
                    language=data.language,
                    metadata={"journey_id": journey_id, "type": "welcome"}
                )
            except Exception as e:
                logger.warning(f"Could not save welcome message: {e}")
        
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
async def companion_chat(
    data: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Chat with AI Wellness Companion - HARDENED with FULL CONTEXT AWARENESS
    
    The companion:
    - ✅ Remembers full conversation history (last 10 messages)
    - ✅ Tracks health progress from journey
    - ✅ Provides personalized, context-aware guidance
    - ✅ Detects when escalation is needed
    - ✅ Supports multilingual conversations
    - ✅ Works even when database is offline (cached responses)
    """
    try:
        # Sanitize user input (Bug #20 fix)
        sanitized_message = sanitize_message(data.message, max_length=5000)
        
        if not sanitized_message:
            raise HTTPException(status_code=400, detail="Invalid or empty message")
        
        # Get journey details for context
        journey = await companion_manager.get_journey(data.journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        # Detect language if not provided
        detected_lang = data.language
        if not detected_lang or detected_lang == "auto":
            detected_lang = lang_manager.detect_language(sanitized_message)
        
        # ============ BUILD CONVERSATION CONTEXT ============
        # Get chat history for context-aware responses
        chat_history: List[ChatMessage] = []
        
        try:
            if hasattr(db_manager, 'client') and db_manager.client:
                # Get Supabase chat history
                sessions = await db_manager.get_user_sessions(journey["user_id"], limit=1)
                if sessions:
                    history = await db_manager.get_chat_history(sessions[0]["id"], limit=10)
                    
                    # Fixed: Add NULL check before iterating
                    if history:
                        # Build proper chat history with alternating user/assistant messages
                        for msg in history:
                            chat_history.append(ChatMessage(role="user", content=msg["user_message"]))
                            chat_history.append(ChatMessage(role="assistant", content=msg["assistant_response"]))
        except Exception as e:
            logger.warning(f"Could not load chat history (continuing with empty history): {e}")
        
        # Build journey context
        journey_context = f"""
Journey Information:
- Health Concern: {journey['health_concern']}
- Status: {journey['status']}
- Journey Started: {journey['started_at']}
- Interactions: {journey['interaction_count']}
"""
        
        if journey.get('initial_symptoms'):
            journey_context += f"- Initial Symptoms: {', '.join(journey['initial_symptoms'])}\n"
        
        if journey.get('milestones_achieved'):
            journey_context += f"- Milestones Achieved: {len(journey['milestones_achieved'])}\n"
        
        # ============ GENERATE CONTEXT-AWARE AI RESPONSE ============
        # Use sanitized message for AI (Bug #20 fix)
        ai_response = await model_service.generate_response(
            prompt=sanitized_message,
            language=detected_lang,
            context=journey_context,
            chat_history=chat_history,  # Pass conversation history!
            max_length=500
        )
        
        # Determine intervention type based on message content
        intervention_type = InterventionType.CHECK_IN.value
        message_lower = sanitized_message.lower()
        
        if any(word in message_lower for word in ["medicine", "medication", "reminder", "pill"]):
            intervention_type = InterventionType.MEDICATION_REMINDER.value
        elif any(word in message_lower for word in ["diet", "food", "eat", "meal"]):
            intervention_type = InterventionType.DIET_REMINDER.value
        elif any(word in message_lower for word in ["symptom", "pain", "sick", "fever", "hurt"]):
            intervention_type = InterventionType.SYMPTOM_ASSESSMENT.value
        elif any(word in message_lower for word in ["doctor", "urgent", "emergency", "severe", "worse"]):
            intervention_type = InterventionType.ESCALATION.value
        elif any(word in message_lower for word in ["thank", "better", "good", "great", "happy"]):
            intervention_type = InterventionType.ENCOURAGEMENT.value
        elif any(word in message_lower for word in ["why", "how", "what", "learn", "tell me about"]):
            intervention_type = InterventionType.EDUCATION.value
        
        # Log interaction to companion system
        await companion_manager.log_interaction(
            journey_id=data.journey_id,
            interaction_type=intervention_type,
            content=ai_response,
            language=detected_lang,
            metadata={"user_message": data.message}
        )
        
        # Save to Supabase chat history
        try:
            sessions = await db_manager.get_user_sessions(journey["user_id"], limit=1)
            if sessions:
                await db_manager.save_chat_message(
                    session_id=sessions[0]["id"],
                    user_message=data.message,
                    assistant_response=ai_response,
                    language=detected_lang,
                    metadata={
                        "journey_id": data.journey_id,
                        "intervention_type": intervention_type
                    }
                )
        except Exception as e:
            logger.warning(f"Could not save chat message to Supabase: {e}")
        
        return ChatResponse(
            success=True,
            response=ai_response,
            language=data.language or "en",
            detected_language=detected_lang,
            intervention_type=intervention_type,
            metadata={
                "journey_status": journey["status"],
                "interaction_count": journey.get("interaction_count", 0) + 1,
                "conversation_history_loaded": len(chat_history) > 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in companion chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey/{journey_id}")
async def get_journey(
    journey_id: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get companion journey details - HARDENED"""
    try:
        journey = await companion_manager.get_journey(journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        return {"success": True, "journey": journey}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey/user/{user_id}")
async def get_user_journeys(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 20
):
    """Get all journeys for a user - HARDENED"""
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
    """Update journey status (active, monitoring, resolved, etc.) - HARDENED"""
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
async def create_health_case(
    data: CreateCaseRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Create a health case after doctor consultation - HARDENED
    
    Creates a comprehensive case with:
    - Diagnosis and prescription
    - Diet plan and lifestyle recommendations
    - Treatment timeline and follow-up schedule
    - Ongoing companion support
    """
    try:
        case_id = await companion_manager.create_case(
            journey_id=data.journey_id,
            user_id=data.user_id,
            doctor_id=data.doctor_id,
            diagnosis=data.diagnosis,
            prescription_id=data.prescription_id,
            diet_plan=data.diet_plan,
            treatment_duration_days=data.treatment_duration_days,
            follow_up_schedule=data.follow_up_schedule,
            metadata=data.metadata
        )
        
        if not case_id:
            raise HTTPException(status_code=500, detail="Failed to create case")
        
        return CreateCaseResponse(
            success=True,
            case_id=case_id,
            message=f"Case created successfully. Companion will support patient for {data.treatment_duration_days} days."
        )
        
    except Exception as e:
        logger.error(f"Error creating case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case/{case_id}")
async def get_case(case_id: str):
    """Get case details - HARDENED"""
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
    Update case progress and adherence - HARDENED
    
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
    """Add a milestone achievement to the journey - HARDENED"""
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
    """Get all health records (Storj documents) linked to a journey - HARDENED"""
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
    """Link a Storj health record to the journey - HARDENED"""
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
    Get conversation history from Supabase - HARDENED
    
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
