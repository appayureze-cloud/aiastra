"""
Advanced Notification System API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from .escalation_system import escalation_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-notifications", tags=["Advanced Notifications"])

class SmartScheduleRequest(BaseModel):
    patient_id: str = Field(..., description="Patient ID")
    patient_name: str = Field(..., description="Patient name")
    patient_phone: str = Field(..., description="Patient phone number")
    medicines: List[Dict] = Field(..., description="List of medicines")
    lifestyle: Optional[Dict] = Field(default={}, description="Patient lifestyle data")

@router.post("/check-missed-doses")
async def check_missed_doses():
    """Check for missed doses and trigger escalations"""
    try:
        result = escalation_system.check_missed_doses()
        return {
            "success": True,
            "escalation_results": result,
            "timestamp": result.get('checked_at')
        }
    except Exception as e:
        logger.error(f"Error checking missed doses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check missed doses: {str(e)}")

@router.post("/create-smart-schedule")
async def create_smart_schedule(request: SmartScheduleRequest):
    """Create intelligent medicine schedule"""
    try:
        patient_data = request.dict()
        smart_schedule = escalation_system.create_smart_schedule(patient_data)
        
        return {
            "success": True,
            "smart_schedule": smart_schedule,
            "patient_id": request.patient_id
        }
    except Exception as e:
        logger.error(f"Error creating smart schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create smart schedule: {str(e)}")

@router.get("/escalation-status")
async def get_escalation_status():
    """Get current escalation system status"""
    try:
        return {
            "success": True,
            "escalation_system": "active",
            "rules": escalation_system.escalation_rules,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting escalation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")