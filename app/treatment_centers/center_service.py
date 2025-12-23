"""
Treatment Center Service
Handles CRUD operations for treatment centers using Supabase REST API
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import uuid
import math

logger = logging.getLogger(__name__)

class TreatmentCenterService:
    """Treatment center service using Supabase REST API"""
    
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
            logger.info("✅ Treatment Center Service initialized")
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
    
    async def create_center(self, center_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new treatment center"""
        if not self.enabled or not self.supabase:
            raise Exception("Treatment center service not available")
        
        try:
            center_id = str(uuid.uuid4())
            
            data = {
                "center_id": center_id,
                "name": center_data['name'],
                "type": center_data.get('type', 'clinic'),
                "phone": center_data.get('phone'),
                "email": center_data.get('email'),
                "location": center_data.get('location', {}),
                "services": center_data.get('services', []),
                "facilities": center_data.get('facilities', []),
                "working_hours": center_data.get('working_hours', {}),
                "rating": 0.0,
                "total_reviews": 0,
                "is_active": True,
                "images": center_data.get('images', []),
                "description": center_data.get('description'),
                "emergency_services": center_data.get('emergency_services', False),
                "insurance_accepted": center_data.get('insurance_accepted', []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('treatment_centers').insert(data).execute()
            
            logger.info(f"✅ Treatment center {center_id} created")
            
            return {
                "success": True,
                "center_id": center_id,
                "data": response.data[0] if response.data else data
            }
            
        except Exception as e:
            logger.error(f"Error creating treatment center: {e}")
            raise
    
    async def get_center(self, center_id: str) -> Dict[str, Any]:
        """Get treatment center by ID"""
        if not self.enabled or not self.supabase:
            raise Exception("Treatment center service not available")
        
        try:
            response = self.supabase.table('treatment_centers').select('*').eq(
                'center_id', center_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Treatment center not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting treatment center: {e}")
            raise
    
    async def search_nearby_centers(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        center_type: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search for treatment centers near a location"""
        if not self.enabled or not self.supabase:
            raise Exception("Treatment center service not available")
        
        try:
            # Get all active centers
            query = self.supabase.table('treatment_centers').select('*').eq('is_active', True)
            
            if center_type:
                query = query.eq('type', center_type)
            
            response = query.execute()
            
            # Calculate distances and filter
            nearby_centers = []
            for center in response.data:
                if center.get('location') and 'latitude' in center['location']:
                    ctr_lat = center['location']['latitude']
                    ctr_lon = center['location']['longitude']
                    
                    distance = self.haversine_distance(latitude, longitude, ctr_lat, ctr_lon)
                    
                    if distance <= radius_km:
                        # Filter by service if provided
                        if service:
                            if service not in center.get('services', []):
                                continue
                        
                        center['distance_km'] = round(distance, 2)
                        nearby_centers.append(center)
            
            # Sort by distance
            nearby_centers.sort(key=lambda x: x['distance_km'])
            
            # Apply limit
            nearby_centers = nearby_centers[:limit]
            
            return {
                "success": True,
                "count": len(nearby_centers),
                "radius_km": radius_km,
                "centers": nearby_centers
            }
            
        except Exception as e:
            logger.error(f"Error searching nearby centers: {e}")
            raise
    
    async def update_center(self, center_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update treatment center"""
        if not self.enabled or not self.supabase:
            raise Exception("Treatment center service not available")
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('treatment_centers').update(updates).eq(
                'center_id', center_id
            ).execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None
            }
            
        except Exception as e:
            logger.error(f"Error updating treatment center: {e}")
            raise

# Global instance
treatment_center_service = TreatmentCenterService()
