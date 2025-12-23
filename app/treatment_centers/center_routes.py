"""
Treatment Center API Routes
Handles treatment center search and management
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from .center_service import treatment_center_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/treatment-centers", tags=["Treatment Centers"])

# Pydantic Models
class LocationModel(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    pincode: Optional[str] = None

class CreateCenterRequest(BaseModel):
    name: str
    type: str = "clinic"  # clinic, hospital, wellness_center, pharmacy
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[LocationModel] = None
    services: List[str] = []  # e.g., ["Ayurveda", "Yoga", "Panchakarma"]
    facilities: List[str] = []  # e.g., ["Parking", "Wheelchair Access"]
    working_hours: Dict[str, str] = {}  # e.g., {"Monday": "9:00-18:00"}
    images: List[str] = []
    description: Optional[str] = None
    emergency_services: bool = False
    insurance_accepted: List[str] = []

class UpdateCenterRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    services: Optional[List[str]] = None
    working_hours: Optional[Dict] = None
    description: Optional[str] = None

@router.post("/create")
async def create_center(request: CreateCenterRequest):
    """
    Create a new treatment center
    
    Example:
    ```json
    {
        "name": "Ayureze Wellness Center",
        "type": "wellness_center",
        "phone": "+919876543210",
        "email": "contact@ayureze-wellness.com",
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "address": "456 Wellness Street",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001"
        },
        "services": ["Ayurveda", "Yoga", "Panchakarma", "Meditation"],
        "facilities": ["Parking", "Wheelchair Access", "Cafe"],
        "working_hours": {
            "Monday": "8:00-20:00",
            "Tuesday": "8:00-20:00",
            "Wednesday": "8:00-20:00"
        },
        "emergency_services": false,
        "description": "Complete Ayurvedic wellness center with traditional therapies"
    }
    ```
    """
    try:
        result = await treatment_center_service.create_center(request.dict())
        
        return {
            "success": True,
            "message": "Treatment center created successfully",
            "center_id": result['center_id'],
            "data": result['data']
        }
        
    except Exception as e:
        logger.error(f"Error creating treatment center: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{center_id}")
async def get_center(center_id: str):
    """Get treatment center details by ID"""
    try:
        result = await treatment_center_service.get_center(center_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail="Treatment center not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting treatment center: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nearby/search")
async def search_nearby_centers(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    center_type: Optional[str] = Query(None, description="Filter by type (clinic/hospital/wellness_center)"),
    service: Optional[str] = Query(None, description="Filter by service"),
    limit: int = Query(20, description="Maximum number of results")
):
    """
    Search for treatment centers near a location
    
    Example:
    ```
    GET /api/treatment-centers/nearby/search?latitude=12.9716&longitude=77.5946&radius_km=5&service=Panchakarma
    ```
    """
    try:
        result = await treatment_center_service.search_nearby_centers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            center_type=center_type,
            service=service,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching centers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{center_id}")
async def update_center(center_id: str, request: UpdateCenterRequest):
    """Update treatment center"""
    try:
        # Build updates dict
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = await treatment_center_service.update_center(center_id, updates)
        
        return {
            "success": True,
            "message": "Treatment center updated successfully",
            "data": result['data']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating treatment center: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{center_id}")
async def deactivate_center(center_id: str):
    """Deactivate a treatment center"""
    try:
        result = await treatment_center_service.update_center(
            center_id,
            {"is_active": False}
        )
        
        return {
            "success": True,
            "message": "Treatment center deactivated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deactivating treatment center: {e}")
        raise HTTPException(status_code=500, detail=str(e))
