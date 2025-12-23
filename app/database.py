"""
Supabase database integration for chat history management
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages Supabase database operations for chat history"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not found, running without database")
    
    def is_connected(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    async def create_chat_session(self, user_id: str, language: str = "en") -> Optional[str]:
        """Create a new chat session"""
        if not self.client:
            return None
            
        try:
            session_data = {
                "user_id": user_id,
                "language": language,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table("chat_sessions").insert(session_data).execute()
            
            if response.data:
                session_id = response.data[0]["id"]
                logger.info(f"Created chat session: {session_id}")
                return session_id
            return None
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return None
    
    async def save_chat_message(
        self, 
        session_id: str, 
        user_message: str, 
        assistant_response: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save a chat message exchange"""
        if not self.client:
            return False
            
        try:
            message_data = {
                "session_id": session_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "language": language,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table("chat_messages").insert(message_data).execute()
            
            # Update session timestamp
            self.client.table("chat_sessions").update({
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", session_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        if not self.client:
            return []
            
        try:
            response = self.client.table("chat_messages").select("*").eq(
                "session_id", session_id
            ).order("created_at", desc=False).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get chat sessions for a user"""
        if not self.client:
            return []
            
        try:
            response = self.client.table("chat_sessions").select("*").eq(
                "user_id", user_id
            ).order("updated_at", desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and its messages"""
        if not self.client:
            return False
            
        try:
            # Delete messages first
            self.client.table("chat_messages").delete().eq("session_id", session_id).execute()
            
            # Delete session
            response = self.client.table("chat_sessions").delete().eq("id", session_id).eq(
                "user_id", user_id
            ).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

# Global database manager instance
db_manager = SupabaseManager()