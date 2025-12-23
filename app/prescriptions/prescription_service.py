"""
Prescription Service
Handles CRUD operations for prescriptions using Supabase REST API
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import uuid

logger = logging.getLogger(__name__)

class PrescriptionService:
    """Prescription service using Supabase REST API"""
    
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
            logger.info("✅ Prescription Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.enabled = False
    
    async def create_prescription(
        self,
        patient_id: str,
        doctor_id: Optional[str],
        diagnosis: str,
        medicines: List[Dict],
        symptoms: Optional[List[str]] = None,
        lifestyle_advice: Optional[str] = None,
        follow_up_date: Optional[str] = None,
        consultation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new prescription
        
        Args:
            patient_id: Patient identifier
            doctor_id: Doctor identifier (optional)
            diagnosis: Diagnosis text
            medicines: List of medicine objects
            symptoms: List of symptoms (optional)
            lifestyle_advice: Lifestyle recommendations (optional)
            follow_up_date: Follow-up date (optional)
            consultation_id: Related consultation ID (optional)
        
        Returns:
            Created prescription data
        """
        if not self.enabled or not self.supabase:
            raise Exception("Prescription service not available")
        
        try:
            prescription_id = str(uuid.uuid4())
            
            data = {
                "prescription_id": prescription_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "consultation_id": consultation_id,
                "diagnosis": diagnosis,
                "symptoms": symptoms or [],
                "medicines": medicines,
                "lifestyle_advice": lifestyle_advice,
                "follow_up_date": follow_up_date,
                "status": "active",
                "is_active": True,
                "cart_created": False,
                "reminders_created": False,
                "astra_explained": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('prescriptions').insert(data).execute()
            
            logger.info(f"✅ Prescription {prescription_id} created for patient {patient_id}")
            
            return {
                "success": True,
                "prescription_id": prescription_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error creating prescription: {e}")
            raise
    
    async def get_prescription(self, prescription_id: str) -> Dict[str, Any]:
        """Get prescription by ID"""
        if not self.enabled or not self.supabase:
            raise Exception("Prescription service not available")
        
        try:
            response = self.supabase.table('prescriptions').select('*').eq(
                'prescription_id', prescription_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Prescription not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting prescription: {e}")
            raise
    
    async def get_patient_prescriptions(
        self,
        patient_id: str,
        limit: int = 50,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """Get all prescriptions for a patient"""
        if not self.enabled or not self.supabase:
            raise Exception("Prescription service not available")
        
        try:
            query = self.supabase.table('prescriptions').select('*').eq(
                'patient_id', patient_id
            )
            
            if active_only:
                query = query.eq('is_active', True)
            
            query = query.order('created_at', desc=True).limit(limit)
            
            response = query.execute()
            
            return {
                "success": True,
                "patient_id": patient_id,
                "count": len(response.data),
                "prescriptions": response.data
            }
            
        except Exception as e:
            logger.error(f"Error getting patient prescriptions: {e}")
            raise
    
    async def update_prescription(
        self,
        prescription_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update prescription"""
        if not self.enabled or not self.supabase:
            raise Exception("Prescription service not available")
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('prescriptions').update(updates).eq(
                'prescription_id', prescription_id
            ).execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None
            }
            
        except Exception as e:
            logger.error(f"Error updating prescription: {e}")
            raise
    
    async def delete_prescription(self, prescription_id: str) -> Dict[str, Any]:
        """Soft delete prescription"""
        if not self.enabled or not self.supabase:
            raise Exception("Prescription service not available")
        
        try:
            response = self.supabase.table('prescriptions').update({
                'is_active': False,
                'status': 'deleted',
                'updated_at': datetime.now().isoformat()
            }).eq('prescription_id', prescription_id).execute()
            
            return {
                "success": True,
                "message": "Prescription deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting prescription: {e}")
            raise

# Global instance
prescription_service = PrescriptionService()
