"""
Patient Management API for Smart Auto-Cart System
Handles patient registration, search, and doctor-patient linking
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import json

from .database_models import (
    get_db_dependency, 
    PatientProfile, 
    Consultation,
    create_patient_profile,
    search_patients,
    get_patient_by_code,
    create_consultation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["Patient Management"])

# Pydantic models for API requests/responses

class PatientRegistration(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

class PatientSearchResult(BaseModel):
    patient_id: str
    patient_code: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    last_consultation: Optional[str] = None

class ConsultationRequest(BaseModel):
    patient_code: str
    doctor_id: str
    doctor_name: str
    doctor_specialization: Optional[str] = None
    consultation_type: str = "online"
    appointment_date: Optional[str] = None
    notes: Optional[str] = None

@router.post("/register")
async def register_patient(
    patient_data: PatientRegistration,
    db: Session = Depends(get_db_dependency)
):
    """
    Register a new patient and generate unique patient code
    Used by patient app during first-time registration
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        # Generate unique patient_id
        import uuid
        patient_id = f"patient_{uuid.uuid4().hex[:12]}"
        
        # Prepare patient data
        patient_info = {
            "patient_id": patient_id,
            "name": patient_data.name,
            "email": patient_data.email,
            "phone": patient_data.phone,
            "age": patient_data.age,
            "gender": patient_data.gender,
            "address": patient_data.address,
            "emergency_contact": patient_data.emergency_contact,
            "medical_conditions": json.dumps(patient_data.medical_conditions or []),
            "allergies": json.dumps(patient_data.allergies or [])
        }
        
        # ✅ ENCRYPT sensitive patient data before saving
        from app.security import field_encryptor
        encrypted_patient_info = field_encryptor.encrypt_fields(patient_info)
        
        # Create patient profile with encrypted data
        patient = create_patient_profile(db, encrypted_patient_info)
        
        logger.info(f"Patient registered: {patient.patient_code} - {patient.name}")
        
        return {
            "success": True,
            "patient_id": patient.patient_id,
            "patient_code": patient.patient_code,
            "name": patient.name,
            "message": f"Patient registered successfully with code: {patient.patient_code}"
        }
        
    except Exception as e:
        logger.error(f"Patient registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/search/{search_term}")
async def search_patients_for_doctor(
    search_term: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Search patients for doctor app
    Doctors can search by name, phone, patient code, or email
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        from app.security import field_encryptor
        
        patients = search_patients(db, search_term)
        
        # Convert to search results with decryption
        results = []
        for patient in patients:
            # Decrypt sensitive fields
            patient_dict = {
                "phone": patient.phone,
                "email": patient.email
            }
            decrypted = field_encryptor.decrypt_fields(patient_dict)
            
            results.append(PatientSearchResult(
                patient_id=patient.patient_id,
                patient_code=patient.patient_code,
                name=patient.name,
                phone=decrypted.get("phone"),
                email=decrypted.get("email"),
                age=patient.age,
                gender=patient.gender
            ))
        
        logger.info(f"Patient search for '{search_term}': {len(results)} results")
        
        return {
            "search_term": search_term,
            "total_results": len(results),
            "patients": results
        }
        
    except Exception as e:
        logger.error(f"Patient search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/verify/{patient_code}")
async def verify_patient_code(
    patient_code: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Verify patient code exists and get patient details
    Used by doctor app before creating prescription
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        patient = get_patient_by_code(db, patient_code.upper())
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient code {patient_code} not found"
            )
        
        # Parse medical conditions and allergies
        medical_conditions = []
        allergies = []
        
        if patient.medical_conditions:
            try:
                medical_conditions = json.loads(patient.medical_conditions)
            except:
                medical_conditions = [patient.medical_conditions]
        
        if patient.allergies:
            try:
                allergies = json.loads(patient.allergies)
            except:
                allergies = [patient.allergies]
        
        return {
            "patient_code": patient.patient_code,
            "patient_id": patient.patient_id,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "medical_conditions": medical_conditions,
            "allergies": allergies,
            "is_active": patient.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patient verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

@router.post("/consultation")
async def create_consultation_record(
    consultation_data: ConsultationRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Create consultation record linking doctor and patient
    Used when doctor starts consultation with patient
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        # Verify patient exists
        patient = get_patient_by_code(db, consultation_data.patient_code.upper())
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient code {consultation_data.patient_code} not found"
            )
        
        # Generate consultation ID
        import uuid
        consultation_id = f"consult_{uuid.uuid4().hex[:12]}"
        
        # Create consultation record
        consultation_info = {
            "consultation_id": consultation_id,
            "patient_id": patient.patient_id,
            "doctor_id": consultation_data.doctor_id,
            "doctor_name": consultation_data.doctor_name,
            "doctor_specialization": consultation_data.doctor_specialization,
            "consultation_type": consultation_data.consultation_type,
            "notes": consultation_data.notes
        }
        
        consultation = create_consultation(db, consultation_info)
        
        logger.info(f"Consultation created: {consultation.consultation_id}")
        
        return {
            "success": True,
            "consultation_id": consultation.consultation_id,
            "patient_name": patient.name,
            "doctor_name": consultation.doctor_name,
            "message": "Consultation record created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consultation creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consultation: {str(e)}"
        )

@router.get("/profile/{patient_id}")
async def get_patient_profile(
    patient_id: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get complete patient profile for patient app
    Used by patient app to show profile information
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        patient = db.query(PatientProfile).filter(
            PatientProfile.patient_id == patient_id,
            PatientProfile.is_active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        # Get recent consultations
        recent_consultations = db.query(Consultation).filter(
            Consultation.patient_id == patient_id
        ).order_by(Consultation.created_at.desc()).limit(5).all()
        
        consultations = []
        for consult in recent_consultations:
            consultations.append({
                "consultation_id": consult.consultation_id,
                "doctor_name": consult.doctor_name,
                "doctor_specialization": consult.doctor_specialization,
                "appointment_date": consult.appointment_date.isoformat() if consult.appointment_date else None,
                "status": consult.status,
                "diagnosis": consult.diagnosis,
                "prescription_sent": consult.prescription_sent,
                "created_at": consult.created_at.isoformat()
            })
        
        return {
            "patient_id": patient.patient_id,
            "patient_code": patient.patient_code,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "medical_conditions": json.loads(patient.medical_conditions or "[]"),
            "allergies": json.loads(patient.allergies or "[]"),
            "recent_consultations": consultations,
            "created_at": patient.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@router.get("/health")
async def patient_management_health():
    """Health check for patient management service"""
    return {
        "service": "Patient Management",
        "status": "healthy",
        "features": [
            "Patient registration with unique codes",
            "Patient search for doctors",
            "Consultation record creation",
            "Patient profile management"
        ]
    }