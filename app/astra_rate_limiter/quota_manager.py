"""
GPU Quota Manager - Daily GPU Usage Tracking

This module tracks daily GPU quota usage to control costs.
Each user has a daily limit of GPU-intensive operations.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class GPUQuotaManager:
    """
    GPU quota management for cost control.
    
    RULES:
    - Daily limit per user
    - Tracks GPU-intensive operations
    - Priority capabilities get higher quota
    - Resets daily at midnight UTC
    """
    
    def __init__(self, db_connection=None, daily_limit: int = 100):
        """
        Initialize GPU quota manager.
        
        Args:
            db_connection: Optional database connection
            daily_limit: Default daily GPU quota per user
        """
        self.db = db_connection
        self.daily_limit = daily_limit
        
        # In-memory quota tracking
        # Structure: {user_id: {profile_id: {"date": date, "used": int}}}
        self.quota_usage = defaultdict(lambda: defaultdict(dict))
        
        # Priority capabilities (get higher effective quota)
        self.priority_capabilities = [
            "EMERGENCY_REDIRECT",
            "MEDICATION_REMINDER_CHAT",
            "SYMPTOM_DOCUMENTATION"
        ]
        
        logger.info("✅ GPU Quota Manager initialized (daily limit: %d)", daily_limit)
    
    async def check_quota(
        self,
        user_id: str,
        profile_id: str,
        capability: str,
        gpu_cost: int = 1
    ) -> Dict:
        """
        Check if user has sufficient GPU quota.
        
        Args:
            user_id: User's account ID
            profile_id: Profile ID
            capability: Capability being accessed
            gpu_cost: GPU cost of this operation (default: 1)
        
        Returns:
            {
                "allowed": bool,
                "quota_limit": int,
                "quota_used": int,
                "quota_remaining": int,
                "resets_at": str
            }
        """
        # Emergency redirect never consumes quota
        if capability == "EMERGENCY_REDIRECT":
            return {
                "allowed": True,
                "quota_limit": self.daily_limit,
                "quota_used": 0,
                "quota_remaining": self.daily_limit,
                "resets_at": self._get_next_reset_time().isoformat()
            }
        
        # Get current usage
        today = datetime.utcnow().date()
        usage = self._get_usage(user_id, profile_id, today)
        
        # Check if quota available
        if usage["used"] + gpu_cost <= self.daily_limit:
            # Update usage
            usage["used"] += gpu_cost
            self.quota_usage[user_id][profile_id] = usage
            
            # Save to database if available
            await self._save_usage_to_db(user_id, profile_id, usage)
            
            logger.info("✅ GPU quota check passed: user=%s, used=%d/%d", 
                       user_id, usage["used"], self.daily_limit)
            
            return {
                "allowed": True,
                "quota_limit": self.daily_limit,
                "quota_used": usage["used"],
                "quota_remaining": self.daily_limit - usage["used"],
                "resets_at": self._get_next_reset_time().isoformat()
            }
        else:
            logger.warning("⚠️ GPU quota exceeded: user=%s, used=%d/%d", 
                         user_id, usage["used"], self.daily_limit)
            
            return {
                "allowed": False,
                "quota_limit": self.daily_limit,
                "quota_used": usage["used"],
                "quota_remaining": 0,
                "resets_at": self._get_next_reset_time().isoformat()
            }
    
    async def consume_quota(
        self,
        user_id: str,
        profile_id: str,
        capability: str,
        gpu_cost: int = 1
    ) -> bool:
        """
        Consume GPU quota (after operation completes).
        
        Args:
            user_id: User's account ID
            profile_id: Profile ID
            capability: Capability that was accessed
            gpu_cost: GPU cost of the operation
        
        Returns:
            True if quota was consumed, False if quota exceeded
        """
        result = await self.check_quota(user_id, profile_id, capability, gpu_cost)
        return result["allowed"]
    
    async def get_quota_status(self, user_id: str, profile_id: str) -> Dict:
        """
        Get current quota status for a user.
        
        Args:
            user_id: User's account ID
            profile_id: Profile ID
        
        Returns:
            {
                "quota_limit": int,
                "quota_used": int,
                "quota_remaining": int,
                "resets_at": str,
                "percentage_used": float
            }
        """
        today = datetime.utcnow().date()
        usage = self._get_usage(user_id, profile_id, today)
        
        remaining = max(0, self.daily_limit - usage["used"])
        percentage = (usage["used"] / self.daily_limit) * 100 if self.daily_limit > 0 else 0
        
        return {
            "quota_limit": self.daily_limit,
            "quota_used": usage["used"],
            "quota_remaining": remaining,
            "resets_at": self._get_next_reset_time().isoformat(),
            "percentage_used": round(percentage, 2)
        }
    
    async def reset_quota(self, user_id: str, profile_id: str):
        """Reset quota for a user (admin function)"""
        if user_id in self.quota_usage and profile_id in self.quota_usage[user_id]:
            del self.quota_usage[user_id][profile_id]
            logger.info("🔄 GPU quota reset for user %s, profile %s", user_id, profile_id)
    
    def _get_usage(self, user_id: str, profile_id: str, date: datetime.date) -> Dict:
        """Get usage for a specific date"""
        if user_id in self.quota_usage and profile_id in self.quota_usage[user_id]:
            usage = self.quota_usage[user_id][profile_id]
            
            # Check if usage is for today
            if usage.get("date") == date:
                return usage
        
        # Create new usage entry for today
        return {
            "date": date,
            "used": 0
        }
    
    def _get_next_reset_time(self) -> datetime:
        """Get next quota reset time (midnight UTC)"""
        now = datetime.utcnow()
        tomorrow = now.date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time())
    
    async def _save_usage_to_db(self, user_id: str, profile_id: str, usage: Dict):
        """Save usage to database (for persistence)"""
        if not self.db:
            return
        
        try:
            # Save to database
            # Implementation depends on your database
            # This is a placeholder
            pass
        except Exception as e:
            logger.error("❌ Error saving GPU quota to database: %s", e)
    
    def cleanup_old_entries(self):
        """Cleanup old quota entries (run daily)"""
        today = datetime.utcnow().date()
        
        for user_id in list(self.quota_usage.keys()):
            for profile_id in list(self.quota_usage[user_id].keys()):
                usage = self.quota_usage[user_id][profile_id]
                
                # Remove entries older than today
                if usage.get("date") < today:
                    del self.quota_usage[user_id][profile_id]
            
            # Remove empty user entries
            if not self.quota_usage[user_id]:
                del self.quota_usage[user_id]
        
        logger.info("🧹 GPU quota cleanup completed")
    
    async def get_global_stats(self) -> Dict:
        """Get global GPU quota statistics (admin function)"""
        total_users = len(self.quota_usage)
        total_usage = 0
        today = datetime.utcnow().date()
        
        for user_id in self.quota_usage:
            for profile_id in self.quota_usage[user_id]:
                usage = self.quota_usage[user_id][profile_id]
                if usage.get("date") == today:
                    total_usage += usage.get("used", 0)
        
        return {
            "total_users": total_users,
            "total_gpu_usage_today": total_usage,
            "average_usage_per_user": total_usage / total_users if total_users > 0 else 0,
            "date": today.isoformat()
        }
