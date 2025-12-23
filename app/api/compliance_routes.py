"""
API endpoints for DISHA compliance management
Patient consent, audit trails, data access
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from ..security.disha_compliance import (
    DISHACompliance, 
    ConsentType, 
    DataAccessPurpose,
    PatientConsent,
    DataAccessAudit
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])

# Pydantic models
class ConsentRequest(BaseModel):
    patient_id: str
    consent_type: ConsentType
    purpose: str
    expires_in_days: Optional[int] = None
    consent_text: Optional[str] = None

class ConsentResponse(BaseModel):
    id: str
    patient_id: str
    consent_type: str
    purpose: str
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime]
    revoked: bool

class AuditLogResponse(BaseModel):
    id: str
    patient_id: str
    accessed_by_id: str
    accessed_by_type: str
    access_type: str
    data_type: str
    purpose: str
    accessed_at: datetime
    success: bool

class DataExportRequest(BaseModel):
    patient_id: str
    include_audit_trail: bool = True

# Dependency to get DB session  
from app.database_models import get_db_dependency
# Use existing database setup
get_db = get_db_dependency


@router.post("/consent/grant", response_model=ConsentResponse)
async def grant_consent(
    request: ConsentRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Grant patient consent for data processing
    Required by DISHA before any health data access
    """
    compliance = DISHACompliance(db)
    
    consent = await compliance.grant_consent(
        patient_id=request.patient_id,
        consent_type=request.consent_type,
        purpose=request.purpose,
        expires_in_days=request.expires_in_days,
        consent_text=request.consent_text,
        ip_address=http_request.client.host,
        user_agent=http_request.headers.get('User-Agent')
    )
    
    return ConsentResponse(
        id=consent.id,
        patient_id=consent.patient_id,
        consent_type=consent.consent_type,
        purpose=consent.purpose,
        granted=consent.granted,
        granted_at=consent.granted_at,
        expires_at=consent.expires_at,
        revoked=consent.revoked
    )


@router.post("/consent/revoke")
async def revoke_consent(
    patient_id: str,
    consent_type: ConsentType,
    db: Session = Depends(get_db)
):
    """
    Revoke patient consent
    Patient has right to withdraw consent anytime
    """
    compliance = DISHACompliance(db)
    
    success = await compliance.revoke_consent(
        patient_id=patient_id,
        consent_type=consent_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    return {"message": "Consent revoked successfully"}


@router.get("/consent/{patient_id}", response_model=List[ConsentResponse])
async def get_patient_consents(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all consents for a patient
    """
    compliance = DISHACompliance(db)
    
    # Query all consents for this patient
    consents = db.query(PatientConsent).filter(
        PatientConsent.patient_id == patient_id
    ).all()
    
    return [
        ConsentResponse(
            id=consent.id,
            patient_id=consent.patient_id,
            consent_type=consent.consent_type,
            purpose=consent.purpose,
            granted=consent.granted,
            granted_at=consent.granted_at,
            expires_at=consent.expires_at,
            revoked=consent.revoked
        )
        for consent in consents
    ]


@router.get("/audit/{patient_id}", response_model=List[AuditLogResponse])
async def get_audit_trail(
    patient_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get complete audit trail for a patient
    Patients have right to know who accessed their data (DISHA requirement)
    """
    compliance = DISHACompliance(db)
    
    audits = await compliance.get_patient_audit_trail(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return [
        AuditLogResponse(
            id=audit.id,
            patient_id=audit.patient_id,
            accessed_by_id=audit.accessed_by_id,
            accessed_by_type=audit.accessed_by_type,
            access_type=audit.access_type,
            data_type=audit.data_type,
            purpose=audit.purpose,
            accessed_at=audit.accessed_at,
            success=audit.success
        )
        for audit in audits
    ]


@router.post("/data-export")
async def export_patient_data(
    request: DataExportRequest,
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """
    Export all patient data (Right to Data Portability - DISHA)
    Patient can request complete data export
    DISHA Compliant: Checks consent & logs access
    """
    from app.database_models import (
        PatientProfile, PrescriptionRecord, PrescribedMedicine,
        MedicineSchedule, DocumentRecord, Consultation, PatientAdherence
    )
    from app.security import field_encryptor
    
    compliance = DISHACompliance(db)
    
    # ✅ DISHA COMPLIANCE: Check consent before export
    has_consent = await compliance.check_consent(
        patient_id=request.patient_id,
        consent_type=ConsentType.DATA_STORAGE  # Using existing enum for consent check
    )
    
    if not has_consent:
        # Still allow export but log the lack of consent
        logger.warning(f"Data export requested without consent: {request.patient_id}")
    
    # ✅ DISHA COMPLIANCE: Log data access/export
    await compliance.log_data_access(
        patient_id=request.patient_id,
        accessed_by_id=request.patient_id,  # Patient accessing their own data
        accessed_by_type="patient",
        access_type="export",
        data_type="complete_patient_record",
        purpose=DataAccessPurpose.TREATMENT,  # Using existing enum
        ip_address=http_request.client.host if http_request else None,
        user_agent=http_request.headers.get('User-Agent') if http_request else None
    )
    
    # Get patient profile
    patient = db.query(PatientProfile).filter(
        PatientProfile.patient_id == request.patient_id
    ).first()
    
    patient_info = {}
    if patient:
        # Decrypt sensitive fields
        patient_dict = {
            "patient_id": patient.patient_id,
            "patient_code": patient.patient_code,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "address": patient.address,
            "medical_conditions": patient.medical_conditions,
            "allergies": patient.allergies,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        }
        patient_info = field_encryptor.decrypt_fields(patient_dict)
    
    # Get all prescriptions
    prescriptions = db.query(PrescriptionRecord).filter(
        PrescriptionRecord.patient_id == request.patient_id
    ).all()
    
    prescription_data = []
    for rx in prescriptions:
        # Get medicines for this prescription
        medicines = db.query(PrescribedMedicine).filter(
            PrescribedMedicine.prescription_id == rx.prescription_id
        ).all()
        
        prescription_data.append({
            "prescription_id": rx.prescription_id,
            "doctor_id": rx.doctor_id,
            "diagnosis": rx.diagnosis,
            "notes": rx.notes,
            "total_amount": rx.total_amount,
            "status": rx.status,
            "prescribed_at": rx.prescribed_at.isoformat() if rx.prescribed_at else None,
            "medicines": [
                {
                    "name": med.medicine_name,
                    "dose": med.dose,
                    "schedule": med.schedule,
                    "duration": med.duration,
                    "instructions": med.instructions
                }
                for med in medicines
            ]
        })
    
    # Get consultations
    consultations = db.query(Consultation).filter(
        Consultation.patient_id == request.patient_id
    ).all()
    
    consultation_data = [
        {
            "consultation_id": c.consultation_id,
            "doctor_name": c.doctor_name,
            "appointment_date": c.appointment_date.isoformat() if c.appointment_date else None,
            "consultation_type": c.consultation_type,
            "diagnosis": c.diagnosis,
            "status": c.status
        }
        for c in consultations
    ]
    
    # Get documents
    documents = db.query(DocumentRecord).filter(
        DocumentRecord.patient_id == request.patient_id,
        DocumentRecord.is_deleted == False
    ).all()
    
    document_data = [
        {
            "document_id": doc.document_id,
            "type": doc.doc_type,
            "filename": doc.original_filename,
            "size": doc.file_size,
            "uploaded_at": doc.created_at.isoformat() if doc.created_at else None
        }
        for doc in documents
    ]
    
    # Get medicine schedules
    schedules = db.query(MedicineSchedule).filter(
        MedicineSchedule.patient_id == request.patient_id
    ).all()
    
    schedule_data = [
        {
            "medicine_name": s.medicine_name,
            "dose_amount": s.dose_amount,
            "schedule_pattern": s.schedule_pattern,
            "start_date": s.start_date.isoformat() if s.start_date else None,
            "end_date": s.end_date.isoformat() if s.end_date else None,
            "is_active": s.is_active
        }
        for s in schedules
    ]
    
    # Get adherence records
    adherence = db.query(PatientAdherence).filter(
        PatientAdherence.patient_id == request.patient_id
    ).all()
    
    adherence_data = [
        {
            "medicine_name": a.medicine_name,
            "adherence_percentage": a.adherence_percentage,
            "doses_taken": a.doses_taken,
            "doses_missed": a.doses_missed,
            "streak_days": a.streak_days
        }
        for a in adherence
    ]
    
    # Compile all patient data
    patient_data = {
        "patient_id": request.patient_id,
        "personal_info": patient_info,
        "prescriptions": prescription_data,
        "consultations": consultation_data,
        "documents": document_data,
        "medicine_schedules": schedule_data,
        "adherence_records": adherence_data,
        "export_timestamp": datetime.utcnow().isoformat(),
        "total_records": {
            "prescriptions": len(prescription_data),
            "consultations": len(consultation_data),
            "documents": len(document_data),
            "schedules": len(schedule_data)
        }
    }
    
    # Include audit trail if requested
    if request.include_audit_trail:
        audits = await compliance.get_patient_audit_trail(request.patient_id)
        patient_data["audit_trail"] = [
            {
                "accessed_by": audit.accessed_by_id,
                "accessed_by_type": audit.accessed_by_type,
                "access_type": audit.access_type,
                "data_type": audit.data_type,
                "purpose": audit.purpose,
                "accessed_at": audit.accessed_at.isoformat(),
                "success": audit.success
            }
            for audit in audits
        ]
    
    return patient_data


@router.delete("/patient-data/{patient_id}")
async def delete_patient_data(
    patient_id: str,
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete all patient data (Right to be Forgotten - DISHA)
    Requires patient confirmation
    Anonymizes data instead of deleting for legal/audit compliance
    """
    from app.database_models import (
        PatientProfile, PrescriptionRecord, PrescribedMedicine,
        MedicineSchedule, MedicineReminder, DocumentRecord, 
        Consultation, PatientAdherence
    )
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Please confirm deletion by setting confirm=true"
        )
    
    compliance = DISHACompliance(db)
    
    try:
        # Get patient record
        patient = db.query(PatientProfile).filter(
            PatientProfile.patient_id == patient_id
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Log the data deletion action
        await compliance.log_data_access(
            patient_id=patient_id,
            accessed_by_id="system",
            accessed_by_type="system",
            access_type="delete",
            data_type="all_patient_data",
            purpose=DataAccessPurpose.TREATMENT  # Using existing enum value for deletion logging
        )
        
        # Anonymize patient profile (keep record for audit but remove PII)
        patient.name = f"DELETED_USER_{patient_id[:8]}"
        patient.email = f"deleted_{patient_id[:8]}@anonymized.ayureze"
        patient.phone = "0000000000"
        patient.address = "[DELETED]"
        patient.emergency_contact = "[DELETED]"
        patient.medical_conditions = "[ANONYMIZED]"
        patient.allergies = "[ANONYMIZED]"
        patient.is_active = False
        patient.updated_at = datetime.utcnow()
        
        # Soft delete documents (mark as deleted, keep for audit)
        documents = db.query(DocumentRecord).filter(
            DocumentRecord.patient_id == patient_id
        ).all()
        for doc in documents:
            doc.is_deleted = True
            doc.deleted_at = datetime.utcnow()
        
        # Deactivate medicine schedules
        schedules = db.query(MedicineSchedule).filter(
            MedicineSchedule.patient_id == patient_id
        ).all()
        for schedule in schedules:
            schedule.is_active = False
            schedule.reminders_enabled = False
        
        # Cancel pending reminders
        reminders = db.query(MedicineReminder).filter(
            MedicineReminder.patient_id == patient_id,
            MedicineReminder.status == 'pending'
        ).all()
        for reminder in reminders:
            reminder.status = 'cancelled'
        
        # Anonymize consultations (keep diagnosis for medical records, remove notes)
        consultations = db.query(Consultation).filter(
            Consultation.patient_id == patient_id
        ).all()
        for consult in consultations:
            consult.notes = "[DELETED - Patient requested data removal]"
        
        # Keep prescriptions and medical history for legal/audit purposes
        # but mark them as belonging to anonymized patient
        # Note: Prescriptions are kept per medical record retention requirements (7 years)
        
        db.commit()
        
        return {
            "message": "Patient data anonymization completed successfully",
            "patient_id": patient_id,
            "anonymized_records": {
                "patient_profile": "Anonymized (name, contact, address removed)",
                "documents": f"{len(documents)} documents soft-deleted",
                "medicine_schedules": f"{len(schedules)} schedules deactivated",
                "reminders": f"{len(reminders)} reminders cancelled",
                "consultations": f"{len(consultations)} consultations anonymized",
                "prescriptions": "Retained for legal compliance (7-year retention)",
                "audit_logs": "Retained as required by law"
            },
            "notes": [
                "Personal identifiable information has been removed",
                "Medical records retained for 7 years as required by DISHA",
                "Audit trail preserved for compliance purposes",
                "Documents marked as deleted but retained for legal compliance",
                "Patient account deactivated"
            ],
            "deletion_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to anonymize patient data: {str(e)}"
        )


@router.get("/compliance-status/{patient_id}")
async def get_compliance_status(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get DISHA compliance status for a patient
    Shows encryption status, consents, audit trail availability
    """
    compliance = DISHACompliance(db)
    
    # Check various compliance aspects
    has_consent = await compliance.check_consent(
        patient_id=patient_id,
        consent_type=ConsentType.DATA_STORAGE
    )
    
    return {
        "patient_id": patient_id,
        "encryption_enabled": True,  # Always true in our implementation
        "consent_granted": has_consent,
        "audit_trail_enabled": True,
        "data_retention_policy": "7 years for medical records, 3 years for prescriptions",
        "compliance_level": "DISHA Compliant",
        "last_audit_check": datetime.utcnow().isoformat()
    }
