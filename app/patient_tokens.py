"""
Patient FCM Token Management using Supabase REST API
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class PatientTokenService:
    """Service for managing patient FCM tokens via Supabase REST API"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase credentials not found")
            self.supabase = None
            self.db_available = False
            return
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.db_available = True
            logger.info("✅ Supabase Patient Token Service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.db_available = False
    
    def _get_db_connection(self):
        """Legacy method for compatibility - no longer used"""
        raise NotImplementedError("Direct database connection deprecated. Using Supabase REST API.")
    
    def create_table_if_not_exists(self):
        """Check if patient_fcm_tokens table exists via Supabase REST API"""
        if not self.db_available or not self.supabase:
            logger.warning("Supabase not available, cannot check table")
            return False
        
        try:
            # Try to query the table - if it exists, this will succeed
            response = self.supabase.table('patient_fcm_tokens').select('*').limit(1).execute()
            logger.info("✅ patient_fcm_tokens table exists and accessible")
            return True
                        
        except Exception as e:
            # Table might not exist or other error
            logger.warning(f"patient_fcm_tokens table check failed: {e}")
            logger.info("💡 You may need to create the table in Supabase")
            return False
    
    def store_fcm_token(
        self,
        patient_id: str,
        fcm_token: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store or update patient's FCM token via Supabase REST API
        
        Args:
            patient_id: Unique patient identifier
            fcm_token: Firebase Cloud Messaging token
            device_info: Optional device information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db_available or not self.supabase:
            logger.error("Supabase not available, cannot store token")
            return False
        
        try:
            data = {
                "patient_id": patient_id,
                "fcm_token": fcm_token,
                "device_info": device_info or {},
                "updated_at": datetime.now().isoformat()
            }
            
            # Use upsert to insert or update if exists
            response = self.supabase.table('patient_fcm_tokens').upsert(
                data,
                on_conflict='patient_id'
            ).execute()
            
            logger.info(f"FCM token stored successfully for patient: {patient_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error storing FCM token for patient {patient_id}: {e}")
            return False
    
    def get_fcm_token(self, patient_id: str) -> Optional[str]:
        """
        Get patient's FCM token via Supabase REST API
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            str: FCM token if found, None otherwise
        """
        if not self.db_available or not self.supabase:
            logger.error("Supabase not available, cannot retrieve token")
            return None
        
        try:
            response = self.supabase.table('patient_fcm_tokens').select('fcm_token').eq(
                'patient_id', patient_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                token = response.data[0].get('fcm_token')
                logger.info(f"FCM token retrieved for patient: {patient_id}")
                return token
            else:
                        logger.warning(f"No FCM token found for patient: {patient_id}")
                        return None
                
        except Exception as e:
            logger.error(f"Error retrieving FCM token for patient {patient_id}: {e}")
            return None
    
    def remove_fcm_token(self, patient_id: str) -> bool:
        """
        Remove patient's FCM token via Supabase REST API
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db_available or not self.supabase:
            logger.error("Supabase not available, cannot remove token")
            return False
        
        try:
            response = self.supabase.table('patient_fcm_tokens').delete().eq(
                'patient_id', patient_id
            ).execute()
            
            logger.info(f"FCM token removed for patient: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing FCM token for patient {patient_id}: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the service is available"""
        return self.db_available

# Global patient token service instance
patient_token_service = PatientTokenService()