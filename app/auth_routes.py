"""
Authentication Routes for Astra - Ayurvedic Wellness Assistant
Handles Auth0 login, session management, and authenticated chat
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
import os

from app.models import (
    AuthRequest, SessionResponse, AuthenticatedChatRequest, 
    AuthenticatedChatResponse, ChatHistoryRequest, UserInfo
)
from app.auth import verify_token
from app.auth import get_current_user, get_optional_user
from app.database_models import (
    get_db_dependency, create_tables, save_chat_message, 
    get_user_chat_history, ChatHistory
)
from app.session_manager import session_manager
from app.enhanced_inference import AstraModelInference
from app.language_utils import language_manager

logger = logging.getLogger(__name__)

# Create router for authentication routes
auth_router = APIRouter(prefix="/auth", tags=["authentication"])
chat_router = APIRouter(prefix="/chat", tags=["authenticated-chat"])

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@auth_router.get("/login")
async def login():
    """Redirect to Auth0 login page"""
    auth_url = f"https://{AUTH0_DOMAIN}/authorize?response_type=code&client_id={AUTH0_CLIENT_ID}&redirect_uri={FRONTEND_URL}/callback&scope=openid%20profile%20email&connection=gmail"
    return RedirectResponse(url=auth_url)

@auth_router.post("/session", response_model=SessionResponse)
async def create_session(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    """Create a persistent session after frontend Auth0 authentication"""
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
        
        return SessionResponse(**session_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=401,
            detail="Failed to authenticate with Auth0"
        )

@auth_router.get("/user", response_model=UserInfo)
async def get_user_info(request: Request):
    """Get current user information from JWT token"""
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
        
        return UserInfo(
            id=user_info.get("sub"),
            email=user_info.get("email"),
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            email_verified=user_info.get("email_verified", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=401,
            detail="Failed to authenticate"
        )

@auth_router.post("/logout")
async def logout(
    session_token: str,
    db: Session = Depends(get_db_dependency)
):
    """Logout and invalidate session"""
    try:
        success = session_manager.invalidate_session(db, session_token)
        
        if success:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Failed to logout: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@chat_router.post("/message", response_model=AuthenticatedChatResponse)
async def authenticated_chat(
    request: AuthenticatedChatRequest,
    db: Session = Depends(get_db_dependency)
):
    """Send a chat message with persistent session and history"""
    try:
        # Get session information
        if not request.session_token:
            raise HTTPException(
                status_code=401,
                detail="Session token is required for authenticated chat"
            )
        
        session_info = session_manager.get_session(db, request.session_token)
        if not session_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        
        user_id = session_info["user_id"]
        session_id = session_info["session_id"]
        
        # Detect language if not provided
        detected_language = request.language or language_manager.detect_language(request.message)
        
        # Check if question is Ayurveda-related
        is_ayurveda_related = language_manager.is_ayurveda_related(request.message, detected_language)
        
        # Get the global model inference instance
        from main_enhanced import model_inference
        
        # Generate response with Astra's persona
        if not model_inference or not model_inference.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="Astra is still preparing her knowledge base. Please wait a moment."
            )
        
        response_text = await model_inference.generate_response(
            prompt=request.message,
            language=detected_language,
            max_length=request.max_length or 512,
            temperature=request.temperature or 0.7,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 50,
            do_sample=request.do_sample if request.do_sample is not None else True
        )
        
        # Create model info for database storage
        model_info = {
            "model": f"Astra (unsloth/llama-3.1-8b-bnb-4bit + ayureasehealthcare/llama3-ayurveda-lora-v3)",
            "usage": {
                "prompt_tokens": len(request.message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.message.split()) + len(response_text.split())
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
            user_message=request.message,
            assistant_response=response_text,
            language_info=language_info,
            model_info=model_info,
            metadata={
                "model_params": {
                    "temperature": request.temperature,
                    "max_length": request.max_length,
                    "top_p": request.top_p,
                    "top_k": request.top_k
                }
            }
        )
        
        return AuthenticatedChatResponse(
            response=response_text,
            session_id=session_id,
            user_id=user_id,
            language=detected_language,
            is_ayurveda_related=is_ayurveda_related,
            model=model_info["model"],
            usage=model_info["usage"],
            created_at=chat_entry.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during authenticated chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Astra encountered an issue: {str(e)}"
        )

@chat_router.post("/history", response_model=List[Dict[str, Any]])
async def get_chat_history(
    request: ChatHistoryRequest,
    db: Session = Depends(get_db_dependency)
):
    """Get chat history for authenticated user"""
    try:
        # Verify session
        session_info = session_manager.get_session(db, request.session_token)
        if not session_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        
        user_id = session_info["user_id"]
        session_id = request.session_id if request.session_id else None
        
        # Get chat history from database
        chat_history = get_user_chat_history(
            db=db,
            user_id=user_id,
            session_id=session_id,
            limit=request.limit or 50
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
        
        return formatted_history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat history"
        )

@chat_router.get("/sessions")
async def get_user_sessions(
    session_token: str,
    db: Session = Depends(get_db_dependency)
):
    """Get all chat sessions for authenticated user"""
    try:
        # Verify session
        session_info = session_manager.get_session(db, session_token)
        if not session_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        
        user_id = session_info["user_id"]
        
        # Get user's sessions from database
        from app.database_models import UserSession
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).order_by(UserSession.created_at.desc()).all()
        
        # Format sessions for response
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "session_id": str(session.id),
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "metadata": session.session_metadata
            })
        
        return {
            "sessions": formatted_sessions,
            "total_count": len(formatted_sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user sessions"
        )