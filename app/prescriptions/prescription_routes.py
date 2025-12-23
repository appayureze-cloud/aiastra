"""
Prescription API Routes
Handles prescription creation, management, and automation
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from .prescription_service import prescription_service
from .prescription_automation import prescription_automation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions"])

# Pydantic Models
class MedicineItem(BaseModel):
    name: str = Field(..., description="Medicine name")
    dosage: str = Field(..., description="Dosage (e.g., 500mg, 2 tablets)")
    frequency: str = Field(..., description="Frequency (once_daily, twice_daily, etc.)")
    times: Optional[List[str]] = Field(default=None, description="Specific times (e.g., ['09:00', '21:00'])")
    duration_days: int = Field(default=30, description="Treatment duration in days")
    instructions: Optional[str] = Field(default=None, description="Special instructions")

class CreatePrescriptionRequest(BaseModel):
    patient_id: str
    patient_name: str
    patient_phone: Optional[str] = None
    doctor_id: Optional[str] = None
    consultation_id: Optional[str] = None
    diagnosis: str
    symptoms: Optional[List[str]] = None
    medicines: List[MedicineItem]
    lifestyle_advice: Optional[str] = None
    follow_up_date: Optional[str] = None
    auto_process: bool = True  # Auto-create cart, reminders, etc.

class UpdatePrescriptionRequest(BaseModel):
    diagnosis: Optional[str] = None
    medicines: Optional[List[Dict]] = None
    lifestyle_advice: Optional[str] = None
    follow_up_date: Optional[str] = None
    status: Optional[str] = None

@router.post("/create")
async def create_prescription(request: CreatePrescriptionRequest):
    """
    Create a new prescription with optional automation
    
    Example:
    ```json
    {
        "patient_id": "patient_123",
        "patient_name": "John Doe",
        "patient_phone": "+919876543210",
        "doctor_id": "doctor_456",
        "diagnosis": "Stress and mild anxiety",
        "medicines": [
            {
                "name": "Ashwagandha Capsules",
                "dosage": "500mg",
                "frequency": "twice_daily",
                "times": ["09:00", "21:00"],
                "duration_days": 30,
                "instructions": "Take with warm milk"
            }
        ],
        "lifestyle_advice": "Practice yoga daily, avoid caffeine",
        "auto_process": true
    }
    ```
    """
    try:
        # Create prescription
        result = await prescription_service.create_prescription(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            diagnosis=request.diagnosis,
            medicines=[m.dict() for m in request.medicines],
            symptoms=request.symptoms,
            lifestyle_advice=request.lifestyle_advice,
            follow_up_date=request.follow_up_date,
            consultation_id=request.consultation_id
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail="Failed to create prescription")
        
        prescription_id = result['prescription_id']
        
        # Auto-process if enabled
        automation_result = None
        if request.auto_process:
            logger.info(f"Auto-processing prescription {prescription_id}")
            
            patient_info = {
                "name": request.patient_name,
                "phone": request.patient_phone
            }
            
            automation_result = await prescription_automation.process_prescription(
                prescription_id=prescription_id,
                patient_info=patient_info,
                auto_create_cart=True,
                auto_setup_reminders=True,
                send_whatsapp=bool(request.patient_phone)
            )
        
        return {
            "success": True,
            "prescription_id": prescription_id,
            "message": "Prescription created successfully",
            "data": result['data'],
            "automation": automation_result if request.auto_process else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prescription_id}")
async def get_prescription(prescription_id: str):
    """Get prescription by ID"""
    try:
        result = await prescription_service.get_prescription(prescription_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}")
async def get_patient_prescriptions(
    patient_id: str,
    limit: int = 50,
    active_only: bool = False
):
    """
    Get all prescriptions for a patient
    
    Query params:
    - limit: Maximum number of prescriptions to return (default: 50)
    - active_only: Return only active prescriptions (default: false)
    """
    try:
        result = await prescription_service.get_patient_prescriptions(
            patient_id=patient_id,
            limit=limit,
            active_only=active_only
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting patient prescriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{prescription_id}")
async def update_prescription(
    prescription_id: str,
    request: UpdatePrescriptionRequest
):
    """Update prescription details"""
    try:
        # Build updates dict
        updates = {}
        if request.diagnosis is not None:
            updates['diagnosis'] = request.diagnosis
        if request.medicines is not None:
            updates['medicines'] = request.medicines
        if request.lifestyle_advice is not None:
            updates['lifestyle_advice'] = request.lifestyle_advice
        if request.follow_up_date is not None:
            updates['follow_up_date'] = request.follow_up_date
        if request.status is not None:
            updates['status'] = request.status
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = await prescription_service.update_prescription(
            prescription_id=prescription_id,
            updates=updates
        )
        
        return {
            "success": True,
            "message": "Prescription updated successfully",
            "data": result['data']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{prescription_id}")
async def delete_prescription(prescription_id: str):
    """Delete (deactivate) a prescription"""
    try:
        result = await prescription_service.delete_prescription(prescription_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{prescription_id}/process")
async def process_prescription(
    prescription_id: str,
    patient_name: str,
    patient_phone: Optional[str] = None
):
    """
    Manually trigger prescription automation
    (create cart, setup reminders, send notification)
    """
    try:
        patient_info = {
            "name": patient_name,
            "phone": patient_phone
        }
        
        result = await prescription_automation.process_prescription(
            prescription_id=prescription_id,
            patient_info=patient_info,
            auto_create_cart=True,
            auto_setup_reminders=True,
            send_whatsapp=bool(patient_phone)
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prescription_id}/summary")
async def get_prescription_summary(prescription_id: str):
    """Get prescription summary with Astra explanation"""
    try:
        result = await prescription_service.get_prescription(prescription_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        data = result['data']
        
        return {
            "success": True,
            "prescription_id": prescription_id,
            "diagnosis": data.get('diagnosis'),
            "medicine_count": len(data.get('medicines', [])),
            "cart_created": data.get('cart_created', False),
            "reminders_created": data.get('reminders_created', False),
            "astra_summary": data.get('astra_summary'),
            "status": data.get('status')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
