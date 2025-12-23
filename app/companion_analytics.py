"""
Companion Analytics Service
Track usage, engagement, and health outcomes
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import os

from supabase import create_client, Client
from app.redis_cache import redis_cache

logger = logging.getLogger(__name__)

class CompanionAnalytics:
    """Analytics service for companion system"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("✅ Companion Analytics initialized")
            except Exception as e:
                logger.error(f"Failed to initialize analytics: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            stats = {
                "total_journeys": 0,
                "active_journeys": 0,
                "total_interactions": 0,
                "total_cases": 0,
                "avg_interactions_per_journey": 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            if not self.client:
                return stats
            
            # Total journeys
            response = self.client.table("companion_journeys").select("id", count="exact").execute()
            stats["total_journeys"] = response.count if hasattr(response, 'count') else 0
            
            # Active journeys
            response = self.client.table("companion_journeys").select("id", count="exact").eq("status", "active").execute()
            stats["active_journeys"] = response.count if hasattr(response, 'count') else 0
            
            # Total interactions
            response = self.client.table("companion_interactions").select("id", count="exact").execute()
            stats["total_interactions"] = response.count if hasattr(response, 'count') else 0
            
            # Total cases
            response = self.client.table("companion_cases").select("id", count="exact").execute()
            stats["total_cases"] = response.count if hasattr(response, 'count') else 0
            
            # Calculate averages
            if stats["total_journeys"] > 0:
                stats["avg_interactions_per_journey"] = round(stats["total_interactions"] / stats["total_journeys"], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    async def get_user_engagement(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get engagement metrics for a user"""
        try:
            if not self.client:
                return {"error": "Database not configured"}
            
            # Get user's journeys
            response = self.client.table("companion_journeys").select("*").eq("user_id", user_id).execute()
            journeys = response.data or []
            
            # Calculate metrics
            total_journeys = len(journeys)
            active_journeys = sum(1 for j in journeys if j.get("status") == "active")
            
            # Get interaction count
            journey_ids = [j["id"] for j in journeys]
            if journey_ids:
                response = self.client.table("companion_interactions").select("id", count="exact").in_("journey_id", journey_ids).execute()
                total_interactions = response.count if hasattr(response, 'count') else 0
            else:
                total_interactions = 0
            
            return {
                "user_id": user_id,
                "total_journeys": total_journeys,
                "active_journeys": active_journeys,
                "total_interactions": total_interactions,
                "avg_interactions_per_journey": round(total_interactions / total_journeys, 2) if total_journeys > 0 else 0,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement: {e}")
            return {"error": str(e)}
    
    async def get_language_distribution(self) -> Dict[str, int]:
        """Get distribution of languages used"""
        try:
            if not self.client:
                return {}
            
            response = self.client.table("companion_journeys").select("language").execute()
            journeys = response.data or []
            
            distribution = {}
            for journey in journeys:
                lang = journey.get("language", "en")
                distribution[lang] = distribution.get(lang, 0) + 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting language distribution: {e}")
            return {}
    
    async def get_health_outcomes(self) -> Dict[str, Any]:
        """Get health outcome metrics"""
        try:
            if not self.client:
                return {"error": "Database not configured"}
            
            # Get resolved journeys
            response = self.client.table("companion_journeys").select("*").eq("status", "resolved").execute()
            resolved = response.data or []
            
            # Get cases by status
            response = self.client.table("companion_cases").select("status", count="exact").execute()
            cases = response.data or []
            
            case_status_count = {}
            for case in cases:
                status = case.get("status", "unknown")
                case_status_count[status] = case_status_count.get(status, 0) + 1
            
            return {
                "resolved_journeys": len(resolved),
                "case_status_distribution": case_status_count,
                "success_rate": round(len(resolved) / max(1, len(cases)) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting health outcomes: {e}")
            return {"error": str(e)}

# Global instance
companion_analytics = CompanionAnalytics()
