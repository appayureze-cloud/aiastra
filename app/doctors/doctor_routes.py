"""
Doctor API Routes
Handles doctor registration, search, and management
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from .doctor_service import doctor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

# Pydantic Models
class LocationModel(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    pincode: Optional[str] = None

class RegisterDoctorRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: str = "General Physician"
    qualifications: List[str] = []
    experience_years: int = 0
    consultation_fee: float = 500
    languages: List[str] = ["English"]
    location: Optional[LocationModel] = None
    available_days: List[str] = []
    available_times: Dict[str, List[str]] = {}
    profile_image: Optional[str] = None
    bio: Optional[str] = None

class UpdateDoctorRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: Optional[float] = None
    available_days: Optional[List[str]] = None
    available_times: Optional[Dict] = None
    bio: Optional[str] = None

@router.post("/register")
async def register_doctor(request: RegisterDoctorRequest):
    """
    Register a new doctor
    
    Example:
    ```json
    {
        "name": "Dr. Rajesh Kumar",
        "email": "rajesh@ayureze.com",
        "phone": "+919876543210",
        "specialization": "Ayurveda Specialist",
        "qualifications": ["BAMS", "MD Ayurveda"],
        "experience_years": 10,
        "consultation_fee": 800,
        "languages": ["English", "Hindi", "Tamil"],
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "address": "123 MG Road",
            "city": "Bangalore",
            "state": "Karnataka"
        },
        "available_days": ["Monday", "Tuesday", "Wednesday"],
        "bio": "Specialized in stress management and digestive health"
    }
    ```
    """
    try:
        result = await doctor_service.register_doctor(request.dict())
        
        return {
            "success": True,
            "message": "Doctor registered successfully",
            "doctor_id": result['doctor_id'],
            "data": result['data']
        }
        
    except Exception as e:
        logger.error(f"Error registering doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}")
async def get_doctor(doctor_id: str):
    """Get doctor details by ID"""
    try:
        result = await doctor_service.get_doctor(doctor_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nearby/search")
async def search_nearby_doctors(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    limit: int = Query(20, description="Maximum number of results")
):
    """
    Search for doctors near a location
    
    Example:
    ```
    GET /api/doctors/nearby/search?latitude=12.9716&longitude=77.5946&radius_km=5&specialization=Ayurveda%20Specialist
    ```
    """
    try:
        result = await doctor_service.search_nearby_doctors(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            specialization=specialization,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching doctors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{doctor_id}")
async def update_doctor(doctor_id: str, request: UpdateDoctorRequest):
    """Update doctor profile"""
    try:
        # Build updates dict
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = await doctor_service.update_doctor(doctor_id, updates)
        
        return {
            "success": True,
            "message": "Doctor profile updated successfully",
            "data": result['data']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doctor_id}")
async def deactivate_doctor(doctor_id: str):
    """Deactivate a doctor profile"""
    try:
        result = await doctor_service.update_doctor(
            doctor_id,
            {"is_active": False}
        )
        
        return {
            "success": True,
            "message": "Doctor deactivated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deactivating doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
