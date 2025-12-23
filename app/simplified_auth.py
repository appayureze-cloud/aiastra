"""
Simplified Authentication Routes for Frontend Integration
Handles JWT validation and session management for React/Vue/Angular frontends
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.models import SessionResponse, UserInfo, AuthenticatedChatRequest, AuthenticatedChatResponse
from app.database_models import get_db_dependency, save_chat_message
from app.session_manager import session_manager
from app.auth import verify_token
from app.language_utils import language_manager

logger = logging.getLogger(__name__)

# Create simplified router for frontend integration
simple_auth_router = APIRouter(prefix="/api", tags=["frontend-auth"])

@simple_auth_router.post("/auth/validate-token")
async def validate_token(request: Request):
    """Validate JWT token from frontend and return user info"""
    try:
        # Get JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token required"
            )
        
        # Extract and verify the JWT token
        token = auth_header.split(" ")[1]
        user_info = verify_token(token)
        
        return {
            "valid": True,
            "user": {
                "id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "email_verified": user_info.get("email_verified", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return {
            "valid": False,
            "error": "Invalid or expired token"
        }

@simple_auth_router.post("/auth/create-session")
async def create_backend_session(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    """Create a backend session after frontend Auth0 authentication"""
    try:
        # Get JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token required"
            )
        
        # Extract and verify the JWT token
        token = auth_header.split(" ")[1]
        user_info = verify_token(token)
        
        # Create user info dict from JWT payload
        user_data = {
            "user_id": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "email_verified": user_info.get("email_verified", False)
        }
        
        # Create session in database
        session_data = session_manager.create_session(db, user_data)
        
        return {
            "success": True,
            "session_token": session_data["session_token"],
            "session_id": session_data["session_id"],
            "user": session_data["user"],
            "expires_at": session_data["expires_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create session"
        )

@simple_auth_router.post("/chat/send")
async def send_chat_message(
    request: Dict[str, Any],
    session_token: str,
    db: Session = Depends(get_db_dependency)
):
    """Send a chat message with session token authentication"""
    try:
        # Verify session
        session_info = session_manager.get_session(db, session_token)
        if not session_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        
        user_id = session_info["user_id"]
        session_id = session_info["session_id"]
        message = request.get("message", "")
        
        if not message:
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
        
        # Detect language if not provided
        detected_language = request.get("language") or language_manager.detect_language(message)
        
        # Check if question is Ayurveda-related
        is_ayurveda_related = language_manager.is_ayurveda_related(message, detected_language)
        
        # Get the global model inference instance
        from main_enhanced import model_inference
        
        # Generate response with Astra's persona
        if not model_inference or not model_inference.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="Astra is still preparing her knowledge base. Please wait a moment."
            )
        
        response_text = await model_inference.generate_response(
            prompt=message,
            language=detected_language,
            max_length=request.get("max_length", 512),
            temperature=request.get("temperature", 0.7),
            top_p=request.get("top_p", 0.9),
            top_k=request.get("top_k", 50),
            do_sample=request.get("do_sample", True)
        )
        
        # Create model info for database storage
        model_info = {
            "model": f"Astra (unsloth/llama-3.1-8b-bnb-4bit + ayureasehealthcare/llama3-ayurveda-lora-v3)",
            "usage": {
                "prompt_tokens": len(message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(message.split()) + len(response_text.split())
            }
        }
        
        # Language info for database storage
        language_info = {
            "detected_language": detected_language,
            "language_name": language_manager.get_language_name(detected_language),
            "is_ayurveda_related": is_ayurveda_related
        }
        
        # Save chat message to database
        chat_entry = save_chat_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            user_message=message,
            assistant_response=response_text,
            language_info=language_info,
            model_info=model_info,
            metadata=request.get("metadata", {})
        )
        
        return {
            "success": True,
            "response": response_text,
            "session_id": session_id,
            "user_id": user_id,
            "language": detected_language,
            "language_name": language_manager.get_language_name(detected_language),
            "is_ayurveda_related": is_ayurveda_related,
            "model": model_info["model"],
            "usage": model_info["usage"],
            "created_at": chat_entry.created_at.isoformat(),
            "message_id": str(chat_entry.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )

@simple_auth_router.get("/chat/history")
async def get_chat_history(
    session_token: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db_dependency)
):
    """Get chat history for authenticated user"""
    try:
        # Verify session
        session_info = session_manager.get_session(db, session_token)
        if not session_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        
        user_id = session_info["user_id"]
        
        # Get chat history from database
        from app.database_models import get_user_chat_history
        chat_history = get_user_chat_history(
            db=db,
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        # Format history for response
        formatted_history = []
        for entry in chat_history:
            formatted_history.append({
                "id": str(entry.id),
                "user_message": entry.user_message,
                "assistant_response": entry.assistant_response,
                "language": entry.detected_language,
                "language_name": entry.language_name,
                "is_ayurveda_related": entry.is_ayurveda_related,
                "model_name": entry.model_name,
                "created_at": entry.created_at.isoformat(),
                "tokens": {
                    "prompt_tokens": entry.prompt_tokens,
                    "completion_tokens": entry.completion_tokens,
                    "total_tokens": entry.total_tokens
                }
            })
        
        return {
            "success": True,
            "messages": formatted_history,
            "total_count": len(formatted_history),
            "session_info": {
                "user_id": user_id,
                "session_id": session_id,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat history"
        )

@simple_auth_router.post("/auth/logout")
async def logout_session(
    session_token: str,
    db: Session = Depends(get_db_dependency)
):
    """Logout and invalidate session"""
    try:
        success = session_manager.invalidate_session(db, session_token)
        
        return {
            "success": success,
            "message": "Logged out successfully" if success else "Session not found"
        }
            
    except Exception as e:
        logger.error(f"Failed to logout: {e}")
        return {
            "success": False,
            "message": "Logout failed"
        }