"""
Companion Manager with Redis Integration
Replaces in-memory cache with Redis for production scalability
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import logging

from supabase import create_client, Client
from app.redis_cache import redis_cache
from app.companion_system import CompanionStatus, CaseStatus, InterventionType

logger = logging.getLogger(__name__)

class RedisCompanionManager:
    """Companion Manager with Redis caching for production"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("✅ Redis Companion Manager initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.client = None
        else:
            logger.warning("Supabase not configured - Redis cache only mode")
    
    async def start_companion_journey(
        self,
        user_id: str,
        health_concern: str,
        language: str = "en",
        initial_symptoms: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Start journey with Redis caching"""
        journey_id = str(uuid.uuid4())
        
        journey_data = {
            "id": journey_id,
            "user_id": user_id,
            "health_concern": health_concern,
            "status": CompanionStatus.ACTIVE.value,
            "language": language,
            "initial_symptoms": initial_symptoms or [],
            "metadata": metadata or {},
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "interaction_count": 0,
            "milestones_achieved": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache first (with 24 hour TTL)
        redis_cache.set("companion:journeys", journey_id, journey_data, ttl_seconds=86400)
        
        # Try to persist to database
        if self.client:
            try:
                self.client.table("companion_journeys").insert(journey_data).execute()
                logger.info(f"✅ Journey {journey_id} saved to DB and Redis")
            except Exception as e:
                logger.warning(f"⚠️ Journey {journey_id} in Redis only: {e}")
        
        return journey_id
    
    async def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey with Redis cache"""
        # Try Redis first
        cached = redis_cache.get("companion:journeys", journey_id)
        if cached:
            logger.debug(f"✅ Journey {journey_id} from Redis cache")
            return cached
        
        # Try database
        if self.client:
            try:
                response = self.client.table("companion_journeys").select("*").eq("id", journey_id).execute()
                if response.data:
                    journey = response.data[0]
                    # Cache for next time
                    redis_cache.set("companion:journeys", journey_id, journey, ttl_seconds=86400)
                    return journey
            except Exception as e:
                logger.error(f"Error fetching journey: {e}")
        
        return None
    
    async def log_interaction(
        self,
        journey_id: str,
        interaction_type: str,
        content: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log interaction with Redis"""
        interaction_id = str(uuid.uuid4())
        
        interaction_data = {
            "id": interaction_id,
            "journey_id": journey_id,
            "interaction_type": interaction_type,
            "content": content,
            "language": language,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache interaction
        cache_key = f"{journey_id}:interactions"
        interactions = redis_cache.get("companion", cache_key) or []
        interactions.append(interaction_data)
        redis_cache.set("companion", cache_key, interactions, ttl_seconds=86400)
        
        # Try database
        if self.client:
            try:
                self.client.table("companion_interactions").insert(interaction_data).execute()
            except Exception as e:
                logger.warning(f"Interaction cached only: {e}")
        
        return True
    
    async def get_conversation_history(
        self,
        journey_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history with pruning"""
        # Try Redis first
        cache_key = f"{journey_id}:interactions"
        cached = redis_cache.get("companion", cache_key)
        if cached:
            # Return last N interactions
            return cached[-limit:]
        
        # Try database
        if self.client:
            try:
                response = self.client.table("companion_interactions").select("*").eq("journey_id", journey_id).order("timestamp", desc=True).limit(limit).execute()
                if response.data:
                    interactions = list(reversed(response.data))
                    # Cache for next time
                    redis_cache.set("companion", cache_key, interactions, ttl_seconds=86400)
                    return interactions
            except Exception as e:
                logger.error(f"Error fetching history: {e}")
        
        return []

# Global instance
redis_companion_manager = RedisCompanionManager()
