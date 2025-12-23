"""
Medicine Reminder API Routes - Supabase Version
Works with Supabase REST API instead of PostgreSQL
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .supabase_reminder_service import supabase_reminder_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["Medicine Reminders (Supabase)"])

# Pydantic Models
class CreateReminderRequest(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None  # Optional - will fetch from patient_id if not provided
    patient_phone: Optional[str] = None  # Optional - will fetch from patient_id if not provided
    medicine_name: str
    dosage: str  # e.g., "500mg", "2 tablets"
    frequency: str  # daily, twice_daily, thrice_daily
    times: List[str]  # e.g., ["09:00", "21:00"]
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    instructions: Optional[str] = None
    enable_whatsapp: bool = True

class UpdateReminderRequest(BaseModel):
    is_active: Optional[bool] = None
    dosage: Optional[str] = None
    times: Optional[List[str]] = None
    instructions: Optional[str] = None

class LogAdherenceRequest(BaseModel):
    reminder_id: str
    taken: bool  # True if medicine was taken, False if missed
    timestamp: Optional[str] = None  # ISO format, defaults to now

@router.post("/create")
async def create_medicine_reminder(request: CreateReminderRequest):
    """
    Create a new medicine reminder
    
    Example (with patient details):
    ```json
    {
        "patient_id": "patient_123",
        "patient_name": "John Doe",
        "patient_phone": "919876543210",
        "medicine_name": "Ashwagandha",
        "dosage": "500mg",
        "frequency": "twice_daily",
        "times": ["09:00", "21:00"],
        "start_date": "2024-12-10",
        "end_date": "2024-12-30",
        "instructions": "Take with warm water after meals",
        "enable_whatsapp": true
    }
    ```
    
    Example (minimal - auto-fetch patient details):
    ```json
    {
        "patient_id": "patient_123",
        "medicine_name": "Ashwagandha",
        "dosage": "500mg",
        "frequency": "twice_daily",
        "times": ["09:00", "21:00"],
        "start_date": "2024-12-10",
        "end_date": "2024-12-30"
    }
    ```
    """
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Medicine reminder service not available (Supabase not configured)"
            )
        
        # Auto-fetch patient details if not provided
        patient_name = request.patient_name
        patient_phone = request.patient_phone
        
        if not patient_name or not patient_phone:
            logger.info(f"Fetching patient details for patient_id: {request.patient_id}")
            try:
                # Try to fetch from Supabase patients table
                import httpx
                import os
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_KEY')
                
                if supabase_url and supabase_key:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{supabase_url}/rest/v1/patient_profiles?patient_id=eq.{request.patient_id}",
                            headers={
                                "apikey": supabase_key,
                                "Authorization": f"Bearer {supabase_key}"
                            },
                            timeout=10.0
                        )
                        
                        if response.status_code == 200:
                            patients = response.json()
                            if patients and len(patients) > 0:
                                patient = patients[0]
                                if not patient_name:
                                    patient_name = patient.get('name') or patient.get('patient_name') or f"Patient {request.patient_id}"
                                if not patient_phone:
                                    patient_phone = patient.get('phone') or patient.get('contact_number') or "0000000000"
                                logger.info(f"Fetched patient details: {patient_name}")
                            else:
                                logger.warning(f"Patient not found in database: {request.patient_id}")
                        else:
                            logger.warning(f"Failed to fetch patient: {response.status_code}")
            except Exception as fetch_error:
                logger.warning(f"Could not fetch patient details: {fetch_error}")
            
            # Fallback if still not available
            if not patient_name:
                patient_name = f"Patient {request.patient_id}"
                logger.info(f"Using fallback patient name: {patient_name}")
            if not patient_phone:
                patient_phone = "0000000000"
                logger.warning(f"Using fallback phone number (WhatsApp disabled)")
        
        result = supabase_reminder_service.create_reminder(
            patient_id=request.patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            medicine_name=request.medicine_name,
            dosage=request.dosage,
            frequency=request.frequency,
            times=request.times,
            start_date=request.start_date,
            end_date=request.end_date,
            instructions=request.instructions,
            enable_whatsapp=request.enable_whatsapp and patient_phone != "0000000000"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Check if medicine reminder service is operational"""
    return {
        'status': 'healthy' if supabase_reminder_service.enabled else 'unavailable',
        'service': 'Medicine Reminders (Supabase)',
        'supabase_connected': supabase_reminder_service.enabled,
        'features': {
            'create_reminders': supabase_reminder_service.enabled,
            'whatsapp_notifications': supabase_reminder_service.enabled,
            'adherence_tracking': supabase_reminder_service.enabled
        }
    }

@router.get("/pending/now")
async def get_pending_reminders():
    """
    Get reminders that should be sent right now
    Used by scheduler to send reminders
    """
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        pending = supabase_reminder_service.get_pending_reminders()
        
        return {
            'success': True,
            'count': len(pending),
            'reminders': pending,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}")
async def get_patient_reminders(patient_id: str):
    """
    Get all medicine reminders for a patient
    
    Returns list of reminders with adherence statistics
    """
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Medicine reminder service not available"
            )
        
        reminders = supabase_reminder_service.get_patient_reminders(patient_id)
        
        return {
            'success': True,
            'patient_id': patient_id,
            'count': len(reminders),
            'reminders': reminders
        }
        
    except Exception as e:
        logger.error(f"Error fetching reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{reminder_id}")
async def get_reminder(reminder_id: str):
    """Get a specific reminder by ID"""
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        reminder = supabase_reminder_service.get_reminder_by_id(reminder_id)
        
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {
            'success': True,
            'reminder': reminder
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{reminder_id}")
async def update_reminder(reminder_id: str, request: UpdateReminderRequest):
    """Update a medicine reminder"""
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Build updates dict
        updates = {}
        if request.is_active is not None:
            updates['is_active'] = request.is_active
        if request.dosage is not None:
            updates['dosage'] = request.dosage
        if request.times is not None:
            updates['reminder_times'] = request.times
        if request.instructions is not None:
            updates['instructions'] = request.instructions
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = supabase_reminder_service.update_reminder(reminder_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found or update failed")
        
        return {
            'success': True,
            'message': 'Reminder updated successfully',
            'reminder_id': reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """Delete (deactivate) a medicine reminder"""
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        success = supabase_reminder_service.delete_reminder(reminder_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {
            'success': True,
            'message': 'Reminder deleted successfully',
            'reminder_id': reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adherence/log")
async def log_medicine_adherence(request: LogAdherenceRequest):
    """
    Log when patient takes or misses their medicine
    
    Example:
    ```json
    {
        "reminder_id": "reminder_uuid",
        "taken": true,
        "timestamp": "2024-12-10T09:05:00"
    }
    ```
    """
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        success = supabase_reminder_service.log_adherence(
            reminder_id=request.reminder_id,
            taken=request.taken,
            timestamp=request.timestamp
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {
            'success': True,
            'message': f'Adherence logged: {"taken" if request.taken else "missed"}',
            'reminder_id': request.reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging adherence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending/now")
async def get_pending_reminders():
    """
    Get reminders that should be sent right now
    Used by scheduler to send reminders
    """
    try:
        if not supabase_reminder_service.enabled:
            raise HTTPException(status_code=503, detail="Service not available")
        
        pending = supabase_reminder_service.get_pending_reminders()
        
        return {
            'success': True,
            'count': len(pending),
            'reminders': pending,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
