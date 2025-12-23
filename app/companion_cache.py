"""
In-Memory Cache for Companion System
Provides graceful degradation when Supabase is unavailable
Fixed: Added TTL cache to prevent memory leaks (Bug #9)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from threading import Lock

logger = logging.getLogger(__name__)

# Try to import cachetools for TTL cache, fallback to basic dict
try:
    from cachetools import TTLCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    logger.warning("cachetools not available, using basic dict cache (may cause memory leak)")
    CACHETOOLS_AVAILABLE = False


class CompanionCache:
    """
    Thread-safe in-memory cache for companion journeys
    Used as fallback when database is unavailable
    Fixed: Added TTL (Time-To-Live) to prevent memory leaks
    """
    
    def __init__(self, ttl_hours: int = 24, max_size: int = 1000):
        """
        Initialize cache with TTL and max size limits
        
        Args:
            ttl_hours: Time-to-live in hours (default: 24)
            max_size: Maximum number of items (default: 1000)
        """
        self._lock = Lock()
        
        if CACHETOOLS_AVAILABLE:
            # Use TTL cache with automatic expiration
            ttl_seconds = ttl_hours * 3600
            self._journeys = TTLCache(maxsize=max_size, ttl=ttl_seconds)
            self._interactions = TTLCache(maxsize=max_size, ttl=ttl_seconds)
            self._cases = TTLCache(maxsize=max_size, ttl=ttl_seconds)
            logger.info(f"✅ CompanionCache initialized with TTL={ttl_hours}h, maxsize={max_size}")
        else:
            # Fallback to basic dict (manual cleanup required)
            self._journeys: Dict[str, Dict[str, Any]] = {}
            self._interactions: Dict[str, List[Dict[str, Any]]] = {}
            self._cases: Dict[str, Dict[str, Any]] = {}
            self._last_cleanup = datetime.now(timezone.utc)
            self._ttl_hours = ttl_hours
            self._max_size = max_size
            logger.info("✅ CompanionCache initialized (basic mode - manual cleanup)")
    
    # ============ JOURNEY OPERATIONS ============
    
    def set_journey(self, journey_id: str, journey_data: Dict[str, Any]) -> None:
        """Store journey in cache (with automatic cleanup)"""
        with self._lock:
            self._manual_cleanup()  # Trigger cleanup if needed
            self._journeys[journey_id] = journey_data
            logger.info(f"📦 Cached journey {journey_id}")
    
    def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey from cache"""
        with self._lock:
            return self._journeys.get(journey_id)
    
    def get_user_journeys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all journeys for a user"""
        with self._lock:
            return [
                journey for journey in self._journeys.values()
                if journey.get("user_id") == user_id
            ]
    
    def update_journey(self, journey_id: str, updates: Dict[str, Any]) -> bool:
        """Update journey in cache"""
        with self._lock:
            if journey_id in self._journeys:
                self._journeys[journey_id].update(updates)
                self._journeys[journey_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
                return True
            return False
    
    # ============ INTERACTION OPERATIONS ============
    
    def add_interaction(self, journey_id: str, interaction: Dict[str, Any]) -> None:
        """Add interaction to cache"""
        with self._lock:
            if journey_id not in self._interactions:
                self._interactions[journey_id] = []
            self._interactions[journey_id].append(interaction)
            
            # Update journey interaction count
            if journey_id in self._journeys:
                self._journeys[journey_id]["interaction_count"] = len(self._interactions[journey_id])
                self._journeys[journey_id]["last_interaction"] = datetime.now(timezone.utc).isoformat()
    
    def get_interactions(self, journey_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a journey"""
        with self._lock:
            interactions = self._interactions.get(journey_id, [])
            return interactions[-limit:] if len(interactions) > limit else interactions
    
    # ============ CASE OPERATIONS ============
    
    def set_case(self, case_id: str, case_data: Dict[str, Any]) -> None:
        """Store case in cache"""
        with self._lock:
            self._cases[case_id] = case_data
            logger.info(f"📦 Cached case {case_id}")
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case from cache"""
        with self._lock:
            return self._cases.get(case_id)
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """Update case in cache"""
        with self._lock:
            if case_id in self._cases:
                self._cases[case_id].update(updates)
                self._cases[case_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
                return True
            return False
    
    # ============ CACHE STATS & CLEANUP ============
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                "journeys_count": len(self._journeys),
                "interactions_count": sum(len(i) for i in self._interactions.values()),
                "cases_count": len(self._cases),
                "ttl_enabled": CACHETOOLS_AVAILABLE
            }
    
    def _manual_cleanup(self) -> None:
        """Manual cleanup for basic mode (when cachetools not available)"""
        if CACHETOOLS_AVAILABLE:
            return  # TTL cache handles cleanup automatically
        
        now = datetime.now(timezone.utc)
        
        # Only run cleanup once per hour
        if (now - self._last_cleanup).total_seconds() < 3600:
            return
        
        cutoff_time = now - timedelta(hours=self._ttl_hours)
        
        # Cleanup old journeys
        old_journeys = [
            jid for jid, journey in self._journeys.items()
            if datetime.fromisoformat(journey.get("created_at", now.isoformat())) < cutoff_time
        ]
        for jid in old_journeys:
            del self._journeys[jid]
            if jid in self._interactions:
                del self._interactions[jid]
        
        # Cleanup old cases
        old_cases = [
            cid for cid, case in self._cases.items()
            if datetime.fromisoformat(case.get("created_at", now.isoformat())) < cutoff_time
        ]
        for cid in old_cases:
            del self._cases[cid]
        
        # Enforce max size limits
        if len(self._journeys) > self._max_size:
            # Remove oldest items
            sorted_journeys = sorted(
                self._journeys.items(),
                key=lambda x: x[1].get("created_at", "")
            )
            for jid, _ in sorted_journeys[:len(self._journeys) - self._max_size]:
                del self._journeys[jid]
                if jid in self._interactions:
                    del self._interactions[jid]
        
        self._last_cleanup = now
        logger.info(f"🧹 Manual cache cleanup: removed {len(old_journeys)} journeys, {len(old_cases)} cases")
    
    def clear(self) -> None:
        """Clear all cache (use with caution)"""
        with self._lock:
            self._journeys.clear()
            self._interactions.clear()
            self._cases.clear()
            logger.warning("🗑️ CompanionCache cleared")


# Global cache instance
companion_cache = CompanionCache()
