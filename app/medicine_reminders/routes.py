"""
Medicine Reminder API Routes
Handles medicine reminder creation, management, and patient responses
"""

import logging
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from .reminder_engine import ReminderEngine
from .custom_whatsapp_client import CustomWhatsAppClient
from .prescription_analyzer import PrescriptionAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/medicine-reminders", tags=["Medicine Reminders"])

# Initialize components
reminder_engine = ReminderEngine()
prescription_analyzer = PrescriptionAnalyzer()

# Pydantic models
class CreateRemindersRequest(BaseModel):
    prescription_id: str

class WhatsAppWebhookVerification(BaseModel):
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str

class PatientResponseRequest(BaseModel):
    patient_phone: str
    response: str
    message_timestamp: Optional[str] = None

class StopRemindersRequest(BaseModel):
    patient_id: str
    medicine_name: Optional[str] = None  # If None, stops all reminders

@router.post("/create-from-prescription")
async def create_reminders_from_prescription(request: CreateRemindersRequest):
    """Create medicine reminders from a prescription"""
    try:
        logger.info(f"Creating reminders for prescription: {request.prescription_id}")
        
        success = reminder_engine.create_medicine_schedules_from_prescription(request.prescription_id)
        
        if success:
            return {
                "success": True,
                "message": f"Medicine reminders created for prescription {request.prescription_id}",
                "prescription_id": request.prescription_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create reminders for prescription {request.prescription_id}"
            )
    
    except Exception as e:
        logger.error(f"Error creating reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/send-pending")
async def send_pending_reminders(background_tasks: BackgroundTasks):
    """Send all pending medicine reminders (fixed duplicate exception handler)"""
    try:
        # Run in background to avoid blocking
        background_tasks.add_task(reminder_engine.send_pending_reminders)
        
        return {
            "success": True,
            "message": "Pending reminders are being sent in background"
        }
    
    except Exception as e:
        logger.error(f"Error triggering reminder sending: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")