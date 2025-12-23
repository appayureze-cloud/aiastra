"""
Session Management for Astra - Ayurvedic Wellness Assistant
Handles persistent sessions and session tokens
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database_models import User, UserSession, upsert_user, create_user_session, get_user_session
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and session tokens"""
    
    def __init__(self, session_duration_hours: int = 24 * 7):  # 1 week default
        self.session_duration_hours = session_duration_hours
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, db: Session, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user session after Auth0 authentication"""
        try:
            # Upsert user in database
            user = upsert_user(db, user_info)
            
            # Generate session token and expiry
            session_token = self.generate_session_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.session_duration_hours)
            
            # Create session in database
            session = create_user_session(db, user.id, session_token, expires_at)
            
            logger.info(f"Created session for user {user.id}")
            
            return {
                "session_token": session_token,
                "session_id": str(session.id),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture,
                    "email_verified": user.email_verified
                },
                "expires_at": expires_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, db: Session, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session information by token"""
        try:
            session = get_user_session(db, session_token)
            
            if not session:
                return None
            
            # Check if session has expired
            if session.expires_at and datetime.now(timezone.utc) > session.expires_at:
                logger.info(f"Session {session.id} has expired")
                session.is_active = False
                db.commit()
                return None
            
            # Update last accessed time
            session.last_accessed = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "session_id": str(session.id),
                "user_id": session.user_id,
                "user": {
                    "id": session.user.id,
                    "email": session.user.email,
                    "name": session.user.name,
                    "picture": session.user.picture,
                    "email_verified": session.user.email_verified
                },
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None
            }
        
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def invalidate_session(self, db: Session, session_token: str) -> bool:
        """Invalidate a session (logout)"""
        try:
            session = get_user_session(db, session_token)
            
            if session:
                session.is_active = False
                db.commit()
                logger.info(f"Invalidated session {session.id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions from database"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Find expired sessions
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < current_time,
                UserSession.is_active == True
            ).all()
            
            # Mark as inactive
            for session in expired_sessions:
                session.is_active = False
            
            db.commit()
            
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

# Global session manager instance
session_manager = SessionManager()