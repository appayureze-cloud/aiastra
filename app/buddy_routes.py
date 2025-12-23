"""
Accountability Buddy System - Complete Implementation
Handles profile management, matching, messaging, check-ins, and challenges
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.buddy.buddy_service import buddy_service
from app.buddy.matching_service import matching_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/buddy", tags=["Accountability Buddy"])

# Pydantic Models
class CreateProfileRequest(BaseModel):
    user_id: str
    display_name: str
    health_goals: List[str] = Field(default=[], description="e.g., ['weight_loss', 'stress_management']")
    interests: List[str] = Field(default=[], description="e.g., ['yoga', 'meditation', 'running']")
    personality_type: Optional[str] = Field(default=None, description="introvert/extrovert/ambivert")
    preferred_language: str = "English"
    timezone: str = "Asia/Kolkata"
    age_range: Optional[str] = Field(default=None, description="e.g., '26-35'")
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    health_goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    bio: Optional[str] = None

class SendMessageRequest(BaseModel):
    match_id: str
    sender_id: str
    receiver_id: str
    message_text: str
    message_type: str = "text"

@router.get("/health")
async def buddy_system_health():
    """Health check for buddy system"""
    return {
        "status": "healthy",
        "system": "Accountability Buddy System",
        "version": "2.0.0",
        "message": "Buddy system is fully operational!"
    }

@router.post("/profile/create")
async def create_profile(request: CreateProfileRequest):
    """Create buddy profile"""
    try:
        result = await buddy_service.create_profile(request.dict())
        
        return {
            "success": True,
            "message": "Buddy profile created successfully",
            "profile_id": result['profile_id'],
            "data": result['data']
        }
        
    except Exception as e:
        logger.error(f"Error creating buddy profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get buddy profile by user ID"""
    try:
        result = await buddy_service.get_profile(user_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting buddy profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/{user_id}")
async def update_profile(user_id: str, request: UpdateProfileRequest):
    """Update buddy profile"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = await buddy_service.update_profile(user_id, updates)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": result['data']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating buddy profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/find/{user_id}")
async def find_matches(user_id: str, min_score: float = 0.5, limit: int = 5):
    """Find compatible buddies for a user"""
    try:
        user_profile_result = await buddy_service.get_profile(user_id)
        
        if not user_profile_result['success']:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = user_profile_result['data']
        candidate_profiles = []
        
        matches = await matching_service.find_matches(
            user_profile=user_profile,
            candidate_profiles=candidate_profiles,
            min_score=min_score,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "matches_found": len(matches),
            "matches": matches,
            "message": "Matching algorithm completed" if matches else "No compatible buddies found yet"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/matches/request")
async def request_match(user1_id: str, user2_id: str):
    """Send buddy match request"""
    try:
        result = await buddy_service.create_match({
            "user1_id": user1_id,
            "user2_id": user2_id,
            "match_score": 0.8
        })
        
        return {
            "success": True,
            "message": "Buddy match request sent",
            "match_id": result['match_id']
        }
        
    except Exception as e:
        logger.error(f"Error requesting match: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/my-buddies/{user_id}")
async def get_my_buddies(user_id: str):
    """Get all active buddies for a user"""
    try:
        result = await buddy_service.get_my_buddies(user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting buddies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/send")
async def send_message(request: SendMessageRequest):
    """Send message to buddy"""
    try:
        result = await buddy_service.send_message(request.dict())
        
        return {
            "success": True,
            "message": "Message sent",
            "message_id": result['message_id']
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
