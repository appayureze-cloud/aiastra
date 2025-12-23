"""
Astra Rate Limiter - Multi-Level Rate Limiting

This module implements rate limiting at multiple levels:
1. Global rate limits (per user)
2. Capability-specific rate limits
3. GPU quota management
4. Voice vs text differentiation

Rate limits are enforced BEFORE any GPU-intensive operation.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RateLimitWindow:
    """Sliding window rate limit tracker"""
    
    def __init__(self, limit: int, window_seconds: int):
        """
        Initialize rate limit window.
        
        Args:
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = []  # List of request timestamps
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old requests
        self.requests = [ts for ts in self.requests if ts > cutoff]
        
        # Check if under limit
        if len(self.requests) < self.limit:
            self.requests.append(now)
            return True
        
        return False
    
    def get_retry_after(self) -> int:
        """Get seconds until next request is allowed"""
        if not self.requests:
            return 0
        
        oldest = min(self.requests)
        retry_time = oldest + timedelta(seconds=self.window_seconds)
        now = datetime.utcnow()
        
        if retry_time > now:
            return int((retry_time - now).total_seconds())
        
        return 0
    
    def get_remaining(self) -> int:
        """Get remaining requests in current window"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Count recent requests
        recent = [ts for ts in self.requests if ts > cutoff]
        return max(0, self.limit - len(recent))


class RateLimiter:
    """
    Multi-level rate limiter for Astra.
    
    RULES:
    - Enforced BEFORE any GPU operation
    - Per-user and per-capability limits
    - Separate limits for voice vs text
    - Configurable limits from capabilities.yaml
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize rate limiter.
        
        Args:
            db_connection: Optional database connection for persistent tracking
        """
        self.db = db_connection
        
        # In-memory rate limit tracking
        # Structure: {user_id: {profile_id: {capability: RateLimitWindow}}}
        self.user_limits = defaultdict(lambda: defaultdict(dict))
        
        # Global limits (from capabilities.yaml)
        self.global_limits = self._load_global_limits()
        
        # Capability-specific limits
        self.capability_limits = self._load_capability_limits()
        
        logger.info("✅ Rate Limiter initialized")
    
    def _load_global_limits(self) -> Dict:
        """Load global rate limits"""
        return {
            "text_ai_chat": {"limit": 10, "window": 60},  # 10 per minute
            "voice_chat": {"limit": 3, "window": 60},     # 3 per minute
            "translation_only": {"limit": 20, "window": 60},  # 20 per minute
            "document_analysis": {"limit": 5, "window": 3600},  # 5 per hour
        }
    
    def _load_capability_limits(self) -> Dict:
        """Load capability-specific rate limits"""
        # These should be loaded from capabilities.yaml
        # For now, using hardcoded values
        return {
            "GENERAL_WELLNESS_CHAT": {"limit": 10, "window": 60},  # 10/min
            "SYMPTOM_DOCUMENTATION": {"limit": 5, "window": 3600},  # 5/hour
            "MEDICATION_REMINDER_CHAT": {"limit": 20, "window": 3600},  # 20/hour
            "DOCUMENT_INTERPRETATION": {"limit": 3, "window": 3600},  # 3/hour
            "APPOINTMENT_BOOKING": {"limit": 10, "window": 3600},  # 10/hour
            "PRESCRIPTION_VIEW": {"limit": 20, "window": 3600},  # 20/hour
            "REMINDER_MANAGEMENT": {"limit": 15, "window": 3600},  # 15/hour
            "HEALTH_TIMELINE": {"limit": 10, "window": 3600},  # 10/hour
            "EMERGENCY_REDIRECT": {"limit": 999999, "window": 1},  # Unlimited
        }
    
    async def check_limit(
        self,
        user_id: str,
        profile_id: str,
        capability: Optional[str] = None,
        is_voice: bool = False
    ) -> Dict:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User's account ID
            profile_id: Profile ID
            capability: Optional capability being accessed
            is_voice: Whether this is a voice request
        
        Returns:
            {
                "allowed": bool,
                "limit": int,
                "remaining": int,
                "retry_after": int,
                "reason": str
            }
        """
        # Emergency redirect is never rate limited
        if capability == "EMERGENCY_REDIRECT":
            return {
                "allowed": True,
                "limit": 999999,
                "remaining": 999999,
                "retry_after": 0,
                "reason": "emergency"
            }
        
        # Check global limits first
        global_check = await self._check_global_limit(user_id, profile_id, is_voice)
        if not global_check["allowed"]:
            logger.warning("⚠️ Global rate limit exceeded for user %s", user_id)
            return global_check
        
        # Check capability-specific limits
        if capability:
            capability_check = await self._check_capability_limit(
                user_id, profile_id, capability
            )
            if not capability_check["allowed"]:
                logger.warning("⚠️ Capability rate limit exceeded: %s for user %s", 
                             capability, user_id)
                return capability_check
        
        # All checks passed
        logger.info("✅ Rate limit check passed for user %s (capability: %s)", 
                   user_id, capability or "none")
        
        return {
            "allowed": True,
            "limit": global_check["limit"],
            "remaining": global_check["remaining"],
            "retry_after": 0,
            "reason": "allowed"
        }
    
    async def _check_global_limit(
        self,
        user_id: str,
        profile_id: str,
        is_voice: bool
    ) -> Dict:
        """Check global rate limit"""
        # Determine which global limit to use
        if is_voice:
            limit_key = "voice_chat"
        else:
            limit_key = "text_ai_chat"
        
        limit_config = self.global_limits.get(limit_key, {"limit": 10, "window": 60})
        
        # Get or create rate limit window
        window_key = f"global_{limit_key}"
        if window_key not in self.user_limits[user_id][profile_id]:
            self.user_limits[user_id][profile_id][window_key] = RateLimitWindow(
                limit=limit_config["limit"],
                window_seconds=limit_config["window"]
            )
        
        window = self.user_limits[user_id][profile_id][window_key]
        
        if window.is_allowed():
            return {
                "allowed": True,
                "limit": limit_config["limit"],
                "remaining": window.get_remaining(),
                "retry_after": 0,
                "reason": "global_limit_ok"
            }
        else:
            return {
                "allowed": False,
                "limit": limit_config["limit"],
                "remaining": 0,
                "retry_after": window.get_retry_after(),
                "reason": f"global_{limit_key}_exceeded"
            }
    
    async def _check_capability_limit(
        self,
        user_id: str,
        profile_id: str,
        capability: str
    ) -> Dict:
        """Check capability-specific rate limit"""
        limit_config = self.capability_limits.get(
            capability,
            {"limit": 10, "window": 60}  # Default: 10 per minute
        )
        
        # Get or create rate limit window
        window_key = f"capability_{capability}"
        if window_key not in self.user_limits[user_id][profile_id]:
            self.user_limits[user_id][profile_id][window_key] = RateLimitWindow(
                limit=limit_config["limit"],
                window_seconds=limit_config["window"]
            )
        
        window = self.user_limits[user_id][profile_id][window_key]
        
        if window.is_allowed():
            return {
                "allowed": True,
                "limit": limit_config["limit"],
                "remaining": window.get_remaining(),
                "retry_after": 0,
                "reason": "capability_limit_ok"
            }
        else:
            return {
                "allowed": False,
                "limit": limit_config["limit"],
                "remaining": 0,
                "retry_after": window.get_retry_after(),
                "reason": f"capability_{capability}_exceeded"
            }
    
    async def reset_limits(self, user_id: str, profile_id: str):
        """Reset all limits for a user profile (admin function)"""
        if user_id in self.user_limits and profile_id in self.user_limits[user_id]:
            del self.user_limits[user_id][profile_id]
            logger.info("🔄 Rate limits reset for user %s, profile %s", user_id, profile_id)
    
    async def get_limit_status(self, user_id: str, profile_id: str) -> Dict:
        """Get current rate limit status for a user"""
        status = {
            "user_id": user_id,
            "profile_id": profile_id,
            "limits": {}
        }
        
        if user_id in self.user_limits and profile_id in self.user_limits[user_id]:
            for window_key, window in self.user_limits[user_id][profile_id].items():
                status["limits"][window_key] = {
                    "limit": window.limit,
                    "remaining": window.get_remaining(),
                    "retry_after": window.get_retry_after()
                }
        
        return status
    
    def cleanup_old_entries(self):
        """Cleanup old rate limit entries (run periodically)"""
        # Remove empty user entries
        for user_id in list(self.user_limits.keys()):
            for profile_id in list(self.user_limits[user_id].keys()):
                if not self.user_limits[user_id][profile_id]:
                    del self.user_limits[user_id][profile_id]
            
            if not self.user_limits[user_id]:
                del self.user_limits[user_id]
        
        logger.info("🧹 Rate limiter cleanup completed")
