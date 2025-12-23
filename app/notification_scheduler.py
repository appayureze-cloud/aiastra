"""
Scheduled Notification System
Proactive check-ins and reminders
"""

import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.redis_cache import redis_cache
from app.notification_service import notification_service

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Manages scheduled notifications for companion"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.enabled = os.getenv("ENABLE_SCHEDULED_NOTIFICATIONS", "true").lower() == "true"
        
        if self.enabled:
            logger.info("✅ Notification Scheduler initialized")
        else:
            logger.info("⚠️ Scheduled notifications disabled")
    
    def start(self):
        """Start scheduler"""
        if not self.enabled:
            return
        
        # Morning check-in (9 AM daily)
        self.scheduler.add_job(
            self.send_morning_checkins,
            CronTrigger(hour=9, minute=0),
            id="morning_checkins",
            name="Send morning check-ins"
        )
        
        # Evening check-in (7 PM daily)
        self.scheduler.add_job(
            self.send_evening_checkins,
            CronTrigger(hour=19, minute=0),
            id="evening_checkins",
            name="Send evening check-ins"
        )
        
        # Medication reminders (every 4 hours)
        self.scheduler.add_job(
            self.send_medication_reminders,
            CronTrigger(hour="8,12,16,20"),
            id="medication_reminders",
            name="Send medication reminders"
        )
        
        self.scheduler.start()
        logger.info("✅ Notification scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Notification scheduler stopped")
    
    async def send_morning_checkins(self):
        """Send morning check-in to active users"""
        logger.info("🌅 Sending morning check-ins...")
        
        try:
            # Get active journeys from cache
            # In production, query from database
            # For now, this is a placeholder
            
            active_journeys = []  # TODO: Fetch from Redis or DB
            
            for journey in active_journeys:
                patient_id = journey.get("user_id")
                
                await notification_service.send_push_notification(
                    patient_id=patient_id,
                    title="🌅 Good Morning!",
                    body="How are you feeling today? Let's check in with Astra.",
                    data={
                        "type": "morning_checkin",
                        "journey_id": journey.get("id")
                    }
                )
            
            logger.info(f"✅ Sent morning check-ins to {len(active_journeys)} users")
            
        except Exception as e:
            logger.error(f"Error sending morning check-ins: {e}")
    
    async def send_evening_checkins(self):
        """Send evening check-in to active users"""
        logger.info("🌆 Sending evening check-ins...")
        
        try:
            # Similar to morning check-ins
            active_journeys = []  # TODO: Fetch from Redis or DB
            
            for journey in active_journeys:
                patient_id = journey.get("user_id")
                
                await notification_service.send_push_notification(
                    patient_id=patient_id,
                    title="🌆 Evening Check-In",
                    body="How was your day? Share your progress with Astra.",
                    data={
                        "type": "evening_checkin",
                        "journey_id": journey.get("id")
                    }
                )
            
            logger.info(f"✅ Sent evening check-ins to {len(active_journeys)} users")
            
        except Exception as e:
            logger.error(f"Error sending evening check-ins: {e}")
    
    async def send_medication_reminders(self):
        """Send medication reminders"""
        logger.info("💊 Sending medication reminders...")
        
        try:
            # TODO: Query users with active medication schedules
            users_with_meds = []  # Fetch from DB
            
            for user_data in users_with_meds:
                patient_id = user_data.get("patient_id")
                med_name = user_data.get("medication_name", "your medicine")
                
                await notification_service.send_push_notification(
                    patient_id=patient_id,
                    title="💊 Medication Reminder",
                    body=f"Time to take {med_name}. Tap to confirm.",
                    data={
                        "type": "medication_reminder",
                        "medication_id": user_data.get("medication_id")
                    }
                )
            
            logger.info(f"✅ Sent medication reminders to {len(users_with_meds)} users")
            
        except Exception as e:
            logger.error(f"Error sending medication reminders: {e}")

# Global instance
notification_scheduler = NotificationScheduler()
