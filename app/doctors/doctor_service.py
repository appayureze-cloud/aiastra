"""
Doctor Service
Handles CRUD operations for doctors using Supabase REST API
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import uuid
import math

logger = logging.getLogger(__name__)

class DoctorService:
    """Doctor service using Supabase REST API"""
    
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
            logger.info("✅ Doctor Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.enabled = False
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def register_doctor(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new doctor"""
        if not self.enabled or not self.supabase:
            raise Exception("Doctor service not available")
        
        try:
            doctor_id = str(uuid.uuid4())
            
            data = {
                "doctor_id": doctor_id,
                "name": doctor_data['name'],
                "email": doctor_data.get('email'),
                "phone": doctor_data.get('phone'),
                "specialization": doctor_data.get('specialization', 'General Physician'),
                "qualifications": doctor_data.get('qualifications', []),
                "experience_years": doctor_data.get('experience_years', 0),
                "consultation_fee": doctor_data.get('consultation_fee', 500),
                "languages": doctor_data.get('languages', ['English']),
                "location": doctor_data.get('location', {}),
                "available_days": doctor_data.get('available_days', []),
                "available_times": doctor_data.get('available_times', {}),
                "rating": 0.0,
                "total_reviews": 0,
                "total_consultations": 0,
                "is_active": True,
                "profile_image": doctor_data.get('profile_image'),
                "bio": doctor_data.get('bio'),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('doctors').insert(data).execute()
            
            logger.info(f"✅ Doctor {doctor_id} registered")
            
            return {
                "success": True,
                "doctor_id": doctor_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error registering doctor: {e}")
            raise
    
    async def get_doctor(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor by ID"""
        if not self.enabled or not self.supabase:
            raise Exception("Doctor service not available")
        
        try:
            response = self.supabase.table('doctors').select('*').eq(
                'doctor_id', doctor_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Doctor not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting doctor: {e}")
            raise
    
    async def search_nearby_doctors(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        specialization: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search for doctors near a location"""
        if not self.enabled or not self.supabase:
            raise Exception("Doctor service not available")
        
        try:
            # Get all active doctors
            query = self.supabase.table('doctors').select('*').eq('is_active', True)
            
            if specialization:
                query = query.eq('specialization', specialization)
            
            response = query.execute()
            
            # Calculate distances and filter
            nearby_doctors = []
            for doctor in response.data:
                if doctor.get('location') and 'latitude' in doctor['location']:
                    doc_lat = doctor['location']['latitude']
                    doc_lon = doctor['location']['longitude']
                    
                    distance = self.haversine_distance(latitude, longitude, doc_lat, doc_lon)
                    
                    if distance <= radius_km:
                        doctor['distance_km'] = round(distance, 2)
                        nearby_doctors.append(doctor)
            
            # Sort by distance
            nearby_doctors.sort(key=lambda x: x['distance_km'])
            
            # Apply limit
            nearby_doctors = nearby_doctors[:limit]
            
            return {
                "success": True,
                "count": len(nearby_doctors),
                "radius_km": radius_km,
                "doctors": nearby_doctors
            }
            
        except Exception as e:
            logger.error(f"Error searching nearby doctors: {e}")
            raise
    
    async def update_doctor(self, doctor_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update doctor profile"""
        if not self.enabled or not self.supabase:
            raise Exception("Doctor service not available")
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('doctors').update(updates).eq(
                'doctor_id', doctor_id
            ).execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None
            }
            
        except Exception as e:
            logger.error(f"Error updating doctor: {e}")
            raise

# Global instance
doctor_service = DoctorService()
