"""
Buddy Service
Handles CRUD operations for buddy system using Supabase REST API
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import uuid

logger = logging.getLogger(__name__)

class BuddyService:
    """Buddy service using Supabase REST API"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase credentials not found")
            self.supabase = None
            self.enabled = False
            return
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.enabled = True
            logger.info("✅ Buddy Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.enabled = False
    
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create buddy profile"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            profile_id = str(uuid.uuid4())
            
            data = {
                "profile_id": profile_id,
                "user_id": profile_data['user_id'],
                "display_name": profile_data['display_name'],
                "health_goals": profile_data.get('health_goals', []),
                "interests": profile_data.get('interests', []),
                "personality_type": profile_data.get('personality_type'),
                "preferred_language": profile_data.get('preferred_language', 'English'),
                "timezone": profile_data.get('timezone', 'Asia/Kolkata'),
                "age_range": profile_data.get('age_range'),
                "bio": profile_data.get('bio'),
                "avatar_url": profile_data.get('avatar_url'),
                "is_active": True,
                "match_count": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('buddy_profiles').insert(data).execute()
            
            logger.info(f"✅ Buddy profile {profile_id} created")
            
            return {
                "success": True,
                "profile_id": profile_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error creating buddy profile: {e}")
            raise
    
    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get buddy profile by user ID"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            response = self.supabase.table('buddy_profiles').select('*').eq(
                'user_id', user_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Profile not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting buddy profile: {e}")
            raise
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update buddy profile"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('buddy_profiles').update(updates).eq(
                'user_id', user_id
            ).execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None
            }
            
        except Exception as e:
            logger.error(f"Error updating buddy profile: {e}")
            raise
    
    async def create_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create buddy match"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            match_id = str(uuid.uuid4())
            
            data = {
                "match_id": match_id,
                "user1_id": match_data['user1_id'],
                "user2_id": match_data['user2_id'],
                "match_score": match_data.get('match_score', 0.8),
                "status": "pending",
                "matched_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('buddy_matches').insert(data).execute()
            
            logger.info(f"✅ Buddy match {match_id} created")
            
            return {
                "success": True,
                "match_id": match_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error creating buddy match: {e}")
            raise
    
    async def get_my_buddies(self, user_id: str) -> Dict[str, Any]:
        """Get all active buddies for a user"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            # Get matches where user is either user1 or user2
            response1 = self.supabase.table('buddy_matches').select('*').eq(
                'user1_id', user_id
            ).eq('status', 'accepted').execute()
            
            response2 = self.supabase.table('buddy_matches').select('*').eq(
                'user2_id', user_id
            ).eq('status', 'accepted').execute()
            
            buddies = response1.data + response2.data
            
            return {
                "success": True,
                "count": len(buddies),
                "buddies": buddies
            }
            
        except Exception as e:
            logger.error(f"Error getting buddies: {e}")
            raise
    
    async def send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to buddy"""
        if not self.enabled or not self.supabase:
            raise Exception("Buddy service not available")
        
        try:
            message_id = str(uuid.uuid4())
            
            data = {
                "message_id": message_id,
                "match_id": message_data['match_id'],
                "sender_id": message_data['sender_id'],
                "receiver_id": message_data['receiver_id'],
                "message_text": message_data['message_text'],
                "message_type": message_data.get('message_type', 'text'),
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('buddy_messages').insert(data).execute()
            
            return {
                "success": True,
                "message_id": message_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

# Global instance
buddy_service = BuddyService()
