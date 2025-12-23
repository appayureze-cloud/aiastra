"""
AI Wellness Companion System
Provides ongoing support to patients throughout their health journey until concerns are resolved.
Integrates with Supabase for conversation storage and Storj for health records.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class CompanionStatus(str, Enum):
    """Status of companion journey"""
    ACTIVE = "active"  # Actively supporting patient
    MONITORING = "monitoring"  # Monitoring progress
    RESOLVED = "resolved"  # Health concern resolved
    REFERRED = "referred"  # Referred to doctor
    PAUSED = "paused"  # Patient requested pause


class CaseStatus(str, Enum):
    """Status of health case"""
    OPEN = "open"
    IN_TREATMENT = "in_treatment"
    FOLLOW_UP = "follow_up"
    RESOLVED = "resolved"
    CLOSED = "closed"


class InterventionType(str, Enum):
    """Types of companion interventions"""
    CHECK_IN = "check_in"  # Regular check-in
    MEDICATION_REMINDER = "medication_reminder"
    DIET_REMINDER = "diet_reminder"
    SYMPTOM_ASSESSMENT = "symptom_assessment"
    ESCALATION = "escalation"  # Needs doctor attention
    ENCOURAGEMENT = "encouragement"
    EDUCATION = "education"  # Educational content


class CompanionManager:
    """Manages AI Wellness Companion journeys and interactions"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("✅ Companion Manager initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Companion Manager: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not found for Companion Manager")
    
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self.client is not None
    
    # ============ COMPANION JOURNEY MANAGEMENT ============
    
    async def start_companion_journey(
        self,
        user_id: str,
        health_concern: str,
        language: str = "en",
        initial_symptoms: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Start a new companion journey for a patient
        
        Args:
            user_id: Patient's unique ID
            health_concern: Main health concern (e.g., "digestive issues", "stress management")
            language: Patient's preferred language
            initial_symptoms: List of initial symptoms
            metadata: Additional metadata (age, gender, location, etc.)
        
        Returns:
            Companion journey ID
        """
        journey_id = str(uuid.uuid4())
        
        if not self.client:
            # Return journey ID even without database connection
            logger.warning(f"Starting journey {journey_id} without database storage")
            return journey_id
        
        try:
            journey_data = {
                "id": journey_id,
                "user_id": user_id,
                "health_concern": health_concern,
                "status": CompanionStatus.ACTIVE.value,
                "language": language,
                "initial_symptoms": initial_symptoms or [],
                "metadata": metadata or {},
                "started_at": datetime.utcnow().isoformat(),
                "last_interaction": datetime.utcnow().isoformat(),
                "interaction_count": 0,
                "milestones_achieved": [],
                "health_goals": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("companion_journeys").insert(journey_data).execute()
            
            if response.data:
                logger.info(f"✅ Started companion journey: {journey_id} for user {user_id}")
                
                # Create initial interaction
                await self.log_interaction(
                    journey_id=journey_id,
                    interaction_type=InterventionType.CHECK_IN.value,
                    content=f"Welcome! I'm Astra, your AI Wellness Companion. I'm here to support you with {health_concern}.",
                    language=language
                )
                
                return journey_id
            return None
            
        except Exception as e:
            logger.error(f"Error starting companion journey: {e}")
            return None
    
    async def log_interaction(
        self,
        journey_id: str,
        interaction_type: str,
        content: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a companion interaction"""
        if not self.client:
            return False
        
        try:
            interaction_data = {
                "journey_id": journey_id,
                "interaction_type": interaction_type,
                "content": content,
                "language": language,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("companion_interactions").insert(interaction_data).execute()
            
            # Update journey last interaction
            self.client.table("companion_journeys").update({
                "last_interaction": datetime.utcnow().isoformat(),
                "interaction_count": self.client.table("companion_journeys").select("interaction_count").eq("id", journey_id).execute().data[0]["interaction_count"] + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", journey_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error logging companion interaction: {e}")
            return False
    
    async def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get companion journey details"""
        if not self.client:
            return None
        
        try:
            response = self.client.table("companion_journeys").select("*").eq("id", journey_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting journey: {e}")
            return None
    
    async def get_user_journeys(
        self,
        user_id: str,
        status: Optional[CompanionStatus] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all companion journeys for a user"""
        if not self.client:
            return []
        
        try:
            query = self.client.table("companion_journeys").select("*").eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status.value)
            
            response = query.order("started_at", desc=True).limit(limit).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting user journeys: {e}")
            return []
    
    async def update_journey_status(
        self,
        journey_id: str,
        status: CompanionStatus,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Update companion journey status"""
        if not self.client:
            return False
        
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if status == CompanionStatus.RESOLVED and resolution_notes:
                update_data["resolved_at"] = datetime.utcnow().isoformat()
                update_data["resolution_notes"] = resolution_notes
            
            response = self.client.table("companion_journeys").update(update_data).eq("id", journey_id).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating journey status: {e}")
            return False
    
    # ============ CASE MANAGEMENT (Post-Doctor Consultation) ============
    
    async def create_case(
        self,
        journey_id: str,
        user_id: str,
        doctor_id: str,
        diagnosis: str,
        prescription_id: Optional[str] = None,
        diet_plan: Optional[Dict[str, Any]] = None,
        treatment_duration_days: int = 30,
        follow_up_schedule: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a health case after doctor consultation
        
        Args:
            journey_id: Associated companion journey ID
            user_id: Patient ID
            doctor_id: Consulting doctor ID
            diagnosis: Medical diagnosis
            prescription_id: ID of prescription document
            diet_plan: Diet recommendations
            treatment_duration_days: Expected treatment duration
            follow_up_schedule: List of follow-up dates
            metadata: Additional case metadata
        
        Returns:
            Case ID
        """
        if not self.client:
            return None
        
        try:
            case_id = str(uuid.uuid4())
            case_data = {
                "id": case_id,
                "journey_id": journey_id,
                "user_id": user_id,
                "doctor_id": doctor_id,
                "diagnosis": diagnosis,
                "prescription_id": prescription_id,
                "diet_plan": diet_plan or {},
                "treatment_duration_days": treatment_duration_days,
                "follow_up_schedule": follow_up_schedule or [],
                "status": CaseStatus.IN_TREATMENT.value,
                "progress_percentage": 0,
                "adherence_score": 100.0,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("health_cases").insert(case_data).execute()
            
            if response.data:
                logger.info(f"✅ Created health case: {case_id} for journey {journey_id}")
                
                # Update journey status to monitoring
                await self.update_journey_status(journey_id, CompanionStatus.MONITORING)
                
                # Log case creation interaction
                await self.log_interaction(
                    journey_id=journey_id,
                    interaction_type=InterventionType.CHECK_IN.value,
                    content=f"Your case has been created. I'll continue supporting you throughout your {treatment_duration_days}-day treatment.",
                    metadata={"case_id": case_id}
                )
                
                return case_id
            return None
            
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return None
    
    async def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case details"""
        if not self.client:
            return None
        
        try:
            response = self.client.table("health_cases").select("*").eq("id", case_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting case: {e}")
            return None
    
    async def update_case_progress(
        self,
        case_id: str,
        progress_percentage: float,
        adherence_score: float,
        notes: Optional[str] = None
    ) -> bool:
        """Update case progress and adherence"""
        if not self.client:
            return False
        
        try:
            update_data = {
                "progress_percentage": progress_percentage,
                "adherence_score": adherence_score,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if notes:
                update_data["progress_notes"] = notes
            
            # Auto-update status based on progress
            if progress_percentage >= 100:
                update_data["status"] = CaseStatus.RESOLVED.value
                update_data["resolved_at"] = datetime.utcnow().isoformat()
            elif progress_percentage >= 75:
                update_data["status"] = CaseStatus.FOLLOW_UP.value
            
            response = self.client.table("health_cases").update(update_data).eq("id", case_id).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating case progress: {e}")
            return False
    
    # ============ MILESTONE TRACKING ============
    
    async def add_milestone(
        self,
        journey_id: str,
        milestone_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a milestone to the journey"""
        if not self.client:
            return False
        
        try:
            # Get current milestones
            journey = await self.get_journey(journey_id)
            if not journey:
                return False
            
            milestones = journey.get("milestones_achieved", [])
            milestones.append({
                "type": milestone_type,
                "description": description,
                "achieved_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            
            response = self.client.table("companion_journeys").update({
                "milestones_achieved": milestones,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", journey_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error adding milestone: {e}")
            return False
    
    # ============ HEALTH RECORDS INTEGRATION (Storj) ============
    
    async def link_health_record(
        self,
        journey_id: str,
        record_type: str,
        storj_document_id: str,
        description: str
    ) -> bool:
        """Link a Storj health record to the journey"""
        if not self.client:
            return False
        
        try:
            record_data = {
                "journey_id": journey_id,
                "record_type": record_type,  # prescription, lab_report, xray, etc.
                "storj_document_id": storj_document_id,
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("journey_health_records").insert(record_data).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error linking health record: {e}")
            return False
    
    async def get_journey_records(self, journey_id: str) -> List[Dict[str, Any]]:
        """Get all health records linked to a journey"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("journey_health_records").select("*").eq(
                "journey_id", journey_id
            ).order("created_at", desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting journey records: {e}")
            return []


# Global companion manager instance
companion_manager = CompanionManager()
