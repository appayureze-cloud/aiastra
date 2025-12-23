"""
Astra API Routes - FastAPI Endpoints

This module provides REST API endpoints for Astra AI Wellness Companion.

Endpoints:
- POST /astra/chat - Main chat endpoint
- GET /astra/capabilities - List all capabilities
- POST /astra/consent/grant - Grant consent
- POST /astra/consent/revoke - Revoke consent
- GET /astra/consent/{profile_id} - Get all consents
- POST /astra/memory/store - Store memory
- GET /astra/memory/{profile_id} - Retrieve memory
- DELETE /astra/memory/{profile_id} - Clear memory
- GET /astra/health - Health check
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from .pipeline import AstraPipeline
from .capability_agent import CapabilityAgent
from .consent_manager import ConsentManager
from .rag_memory import RAGMemory

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/astra", tags=["astra"])

# Global instances (will be initialized in main app)
pipeline_instance: Optional[AstraPipeline] = None
capability_agent_instance: Optional[CapabilityAgent] = None
consent_manager_instance: Optional[ConsentManager] = None
rag_memory_instance: Optional[RAGMemory] = None


# ==================== Request/Response Models ====================

class AstraChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message", min_length=1, max_length=5000)
    user_id: str = Field(..., description="User's account ID")
    profile_id: str = Field(..., description="Profile ID (for family profiles)")
    language: Optional[str] = Field(None, description="Language code (auto-detected if not provided)")
    is_voice: bool = Field(False, description="Whether input is from voice")
    user_metadata: Optional[dict] = Field(None, description="Optional user metadata")


class AstraChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Astra's response")
    language: str = Field(..., description="Response language")
    capability: str = Field(..., description="Identified capability")
    emotion: Optional[str] = Field(None, description="Detected emotion")
    tone: Optional[str] = Field(None, description="Applied tone")
    audit_log_id: Optional[str] = Field(None, description="Audit log ID")
    correlation_id: str = Field(..., description="Request correlation ID")
    metadata: dict = Field(..., description="Additional metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CapabilityInfo(BaseModel):
    """Capability information"""
    name: str
    description: str
    requires_ai: bool
    requires_consent: bool
    rate_limit: str
    forbidden: bool
    priority: int


class ConsentGrantRequest(BaseModel):
    """Request to grant consent"""
    user_id: str
    profile_id: str
    purpose: str
    duration_days: int = Field(365, description="Consent duration in days")


class ConsentRevokeRequest(BaseModel):
    """Request to revoke consent"""
    user_id: str
    profile_id: str
    purpose: str


class MemoryStoreRequest(BaseModel):
    """Request to store memory"""
    profile_id: str
    memory_type: str
    content: str
    metadata: Optional[dict] = None
    ttl_days: int = Field(90, description="Time-to-live in days")


# ==================== Dependency Injection ====================

def get_pipeline() -> AstraPipeline:
    """Get pipeline instance"""
    if pipeline_instance is None:
        raise HTTPException(status_code=503, detail="Astra pipeline not initialized")
    return pipeline_instance


def get_capability_agent() -> CapabilityAgent:
    """Get capability agent instance"""
    if capability_agent_instance is None:
        raise HTTPException(status_code=503, detail="Capability agent not initialized")
    return capability_agent_instance


def get_consent_manager() -> ConsentManager:
    """Get consent manager instance"""
    if consent_manager_instance is None:
        raise HTTPException(status_code=503, detail="Consent manager not initialized")
    return consent_manager_instance


def get_rag_memory() -> RAGMemory:
    """Get RAG memory instance"""
    if rag_memory_instance is None:
        raise HTTPException(status_code=503, detail="RAG memory not initialized")
    return rag_memory_instance


# ==================== API Endpoints ====================

@router.post("/chat", response_model=AstraChatResponse)
async def astra_chat(
    request: AstraChatRequest,
    pipeline: AstraPipeline = Depends(get_pipeline),
    x_correlation_id: Optional[str] = Header(None)
):
    """
    Main Astra chat endpoint.
    
    Processes user input through the complete 17-step Astra pipeline.
    
    **Safety Guarantees:**
    - Non-bypassable safety checks
    - Legal compliance enforcement
    - Consent verification
    - Full audit logging
    
    **Rate Limiting:**
    - Applied before GPU operations
    - Per-user and per-capability limits
    
    **Example:**
    ```json
    {
        "message": "Tell me about Ayurvedic wellness",
        "user_id": "user_123",
        "profile_id": "profile_456",
        "language": "en"
    }
    ```
    """
    try:
        logger.info("📨 Astra chat request: user=%s, profile=%s, voice=%s", 
                   request.user_id, request.profile_id, request.is_voice)
        
        # Process through pipeline
        result = await pipeline.process(
            user_input=request.message,
            user_id=request.user_id,
            profile_id=request.profile_id,
            input_language=request.language,
            is_voice=request.is_voice,
            user_metadata=request.user_metadata
        )
        
        # Build response
        response = AstraChatResponse(
            response=result["response"],
            language=result["language"],
            capability=result["capability"],
            emotion=result.get("emotion"),
            tone=result.get("tone"),
            audit_log_id=result.get("audit_log_id"),
            correlation_id=result.get("correlation_id", x_correlation_id or "unknown"),
            metadata=result.get("metadata", {})
        )
        
        logger.info("✅ Astra chat response: capability=%s, language=%s", 
                   response.capability, response.language)
        
        return response
        
    except Exception as e:
        logger.error("❌ Astra chat error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Astra encountered an error: {str(e)}"
        )


@router.get("/capabilities", response_model=List[CapabilityInfo])
async def list_capabilities(
    agent: CapabilityAgent = Depends(get_capability_agent)
):
    """
    List all available Astra capabilities.
    
    Returns information about each capability including:
    - Name and description
    - Whether AI is required
    - Whether consent is required
    - Rate limits
    - Whether it's forbidden
    - Priority level
    
    **Example Response:**
    ```json
    [
        {
            "name": "GENERAL_WELLNESS_CHAT",
            "description": "General wellness conversation",
            "requires_ai": true,
            "requires_consent": false,
            "rate_limit": "10_per_minute",
            "forbidden": false,
            "priority": 3
        }
    ]
    ```
    """
    try:
        capabilities = []
        
        for cap_name in agent.list_all_capabilities():
            cap_def = agent.get_capability_definition(cap_name)
            if cap_def:
                capabilities.append(CapabilityInfo(
                    name=cap_name,
                    description=cap_def.get('description', ''),
                    requires_ai=cap_def.get('requires_ai', False),
                    requires_consent=cap_def.get('requires_consent', False),
                    rate_limit=cap_def.get('rate_limit', 'default'),
                    forbidden=cap_def.get('forbidden', False),
                    priority=cap_def.get('priority', 3)
                ))
        
        logger.info("📋 Listed %d capabilities", len(capabilities))
        return capabilities
        
    except Exception as e:
        logger.error("❌ Error listing capabilities: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent/grant")
async def grant_consent(
    request: ConsentGrantRequest,
    consent_manager: ConsentManager = Depends(get_consent_manager)
):
    """
    Grant consent for a specific purpose.
    
    **DISHA Compliance:**
    - Purpose-specific consent
    - Time-stamped
    - Revocable
    - Profile-specific
    
    **Example:**
    ```json
    {
        "user_id": "user_123",
        "profile_id": "profile_456",
        "purpose": "document_upload",
        "duration_days": 365
    }
    ```
    """
    try:
        result = await consent_manager.grant_consent(
            user_id=request.user_id,
            profile_id=request.profile_id,
            purpose=request.purpose,
            duration_days=request.duration_days
        )
        
        if result["success"]:
            logger.info("✅ Consent granted: %s for %s", request.purpose, request.profile_id)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Error granting consent: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent/revoke")
async def revoke_consent(
    request: ConsentRevokeRequest,
    consent_manager: ConsentManager = Depends(get_consent_manager)
):
    """
    Revoke previously granted consent.
    
    **DISHA Compliance:**
    - User can revoke consent at any time
    - Immediate effect
    - Audit logged
    
    **Example:**
    ```json
    {
        "user_id": "user_123",
        "profile_id": "profile_456",
        "purpose": "document_upload"
    }
    ```
    """
    try:
        result = await consent_manager.revoke_consent(
            user_id=request.user_id,
            profile_id=request.profile_id,
            purpose=request.purpose
        )
        
        if result["success"]:
            logger.info("✅ Consent revoked: %s for %s", request.purpose, request.profile_id)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Error revoking consent: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent/{profile_id}")
async def get_consents(
    profile_id: str,
    user_id: str,
    consent_manager: ConsentManager = Depends(get_consent_manager)
):
    """
    Get all consents for a profile.
    
    **Returns:**
    - List of all consents
    - Status (granted, revoked, expired)
    - Expiration dates
    
    **Example:**
    ```
    GET /astra/consent/profile_456?user_id=user_123
    ```
    """
    try:
        consents = await consent_manager.get_all_consents(user_id, profile_id)
        
        logger.info("📋 Retrieved %d consents for profile %s", len(consents), profile_id)
        return {
            "profile_id": profile_id,
            "consents": consents,
            "count": len(consents)
        }
        
    except Exception as e:
        logger.error("❌ Error retrieving consents: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/store")
async def store_memory(
    request: MemoryStoreRequest,
    rag_memory: RAGMemory = Depends(get_rag_memory)
):
    """
    Store memory in RAG system.
    
    **Allowed Memory Types:**
    - chat_history_summary
    - user_preferences
    - doctor_instructions
    - reminders
    - user_stated_goals
    
    **Forbidden Memory Types:**
    - diagnosis_progress
    - treatment_effectiveness
    - emotional_dependency
    - mental_health_inference
    
    **Example:**
    ```json
    {
        "profile_id": "profile_456",
        "memory_type": "user_preferences",
        "content": "User prefers vegetarian diet",
        "ttl_days": 90
    }
    ```
    """
    try:
        result = await rag_memory.store_memory(
            profile_id=request.profile_id,
            memory_type=request.memory_type,
            content=request.content,
            metadata=request.metadata,
            ttl_days=request.ttl_days
        )
        
        if result["success"]:
            logger.info("✅ Memory stored: %s for %s", request.memory_type, request.profile_id)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Error storing memory: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{profile_id}")
async def clear_memory(
    profile_id: str,
    memory_type: Optional[str] = None,
    rag_memory: RAGMemory = Depends(get_rag_memory)
):
    """
    Clear memory for a profile.
    
    **Parameters:**
    - profile_id: Profile to clear
    - memory_type: Optional specific type to clear (if None, clears all)
    
    **Example:**
    ```
    DELETE /astra/memory/profile_456?memory_type=chat_history_summary
    ```
    """
    try:
        result = await rag_memory.clear_profile_memory(profile_id, memory_type)
        
        logger.info("✅ Cleared %d memories for profile %s", 
                   result["deleted_count"], profile_id)
        return result
        
    except Exception as e:
        logger.error("❌ Error clearing memory: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def astra_health_check():
    """
    Astra health check endpoint.
    
    **Returns:**
    - Status of all Astra components
    - Pipeline readiness
    - Component availability
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "components": {
            "pipeline": "operational",
            "capability_agent": "operational",
            "safety_enforcer": "operational",
            "consent_manager": "operational",
            "rag_memory": "operational"
        }
    }
    ```
    """
    try:
        components = {
            "pipeline": "operational" if pipeline_instance else "not_initialized",
            "capability_agent": "operational" if capability_agent_instance else "not_initialized",
            "consent_manager": "operational" if consent_manager_instance else "not_initialized",
            "rag_memory": "operational" if rag_memory_instance else "not_initialized"
        }
        
        # Determine overall status
        all_operational = all(status == "operational" for status in components.values())
        status = "healthy" if all_operational else "degraded"
        
        return {
            "status": status,
            "components": components,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error("❌ Health check error: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ==================== Initialization Function ====================

def initialize_astra_routes(
    pipeline: AstraPipeline,
    capability_agent: CapabilityAgent,
    consent_manager: ConsentManager,
    rag_memory: RAGMemory
):
    """
    Initialize Astra routes with component instances.
    
    Call this from your main FastAPI app startup.
    
    Example:
    ```python
    from app.astra.routes import initialize_astra_routes, router
    
    # In lifespan or startup event
    pipeline = AstraPipeline(...)
    capability_agent = CapabilityAgent()
    consent_manager = ConsentManager(db)
    rag_memory = RAGMemory(db)
    
    initialize_astra_routes(pipeline, capability_agent, consent_manager, rag_memory)
    
    # Include router
    app.include_router(router)
    ```
    """
    global pipeline_instance, capability_agent_instance, consent_manager_instance, rag_memory_instance
    
    pipeline_instance = pipeline
    capability_agent_instance = capability_agent
    consent_manager_instance = consent_manager
    rag_memory_instance = rag_memory
    
    logger.info("✅ Astra routes initialized")
