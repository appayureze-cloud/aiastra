"""
Unified Prescription Workflow
Orchestrates the complete prescription flow:
1. Generate PDF
2. Send Email  
3. Upload to Storj
4. Create Medicine Reminders
All in one API call!
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database_models import get_db_dependency, PrescriptionRecord
from app.shopify_models import PrescriptionRequest
from app.prescription_pdf_service import PrescriptionPDFService
from app.storj_client import StorjClient
from app.medicine_reminders.reminder_engine import ReminderEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescription-workflow", tags=["Unified Prescription Workflow"])

# Initialize services
pdf_service = PrescriptionPDFService()
reminder_engine = ReminderEngine()

# Initialize Storj (with error handling)
try:
    storj_client = StorjClient()
except Exception as e:
    logger.warning(f"Storj client not available: {e}")
    storj_client = None

class UnifiedPrescriptionRequest(BaseModel):
    prescription_id: str
    patient_email: Optional[str] = None
    doctor_email: Optional[str] = None
    send_email: bool = True
    upload_to_storj: bool = True
    create_reminders: bool = True
    share_via_whatsapp: bool = False
    patient_phone: Optional[str] = None

class WorkflowResult(BaseModel):
    success: bool
    prescription_id: str
    pdf_generated: bool
    email_sent: bool
    storj_uploaded: bool
    reminders_created: bool
    whatsapp_shared: bool
    pdf_url: Optional[str] = None
    document_id: Optional[str] = None
    errors: list = []

@router.post("/execute", response_model=WorkflowResult)
async def execute_unified_prescription_workflow(
    request: UnifiedPrescriptionRequest,
    db: Session = Depends(get_db_dependency)
) -> WorkflowResult:
    """
    Execute the complete prescription workflow in one call.
    
    This endpoint orchestrates:
    1. PDF generation from prescription
    2. Email delivery to patient
    3. Document upload to Storj storage
    4. Medicine reminder creation
    5. Optional WhatsApp sharing
    
    All steps are configurable via request parameters.
    """
    
    result = WorkflowResult(
        success=False,
        prescription_id=request.prescription_id,
        pdf_generated=False,
        email_sent=False,
        storj_uploaded=False,
        reminders_created=False,
        whatsapp_shared=False,
        errors=[]
    )
    
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Step 1: Get prescription from database
        prescription_record = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.prescription_id == request.prescription_id
        ).first()
        
        if not prescription_record:
            raise HTTPException(
                status_code=404, 
                detail=f"Prescription {request.prescription_id} not found"
            )
        
        # Convert to PrescriptionRequest format (needed for PDF service)
        prescription = _convert_to_prescription_request(prescription_record, db)
        
        # Step 2: Generate PDF
        logger.info(f"Generating PDF for prescription {request.prescription_id}")
        try:
            pdf_data = pdf_service.generate_prescription_pdf(prescription)
            result.pdf_generated = True
            logger.info(f"PDF generated successfully: {len(pdf_data)} bytes")
        except Exception as e:
            error_msg = f"PDF generation failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            # Continue workflow even if PDF fails
            pdf_data = None
        
        # Step 3: Send Email (if enabled and PDF generated)
        if request.send_email and pdf_data:
            logger.info(f"Sending prescription email")
            try:
                email_result = pdf_service.send_prescription_email(
                    prescription=prescription,
                    pdf_data=pdf_data,
                    patient_email=request.patient_email,
                    doctor_email=request.doctor_email
                )
                if email_result.get('email_sent'):
                    result.email_sent = True
                    logger.info("Email sent successfully")
                else:
                    result.errors.append(f"Email failed: {email_result.get('error')}")
            except Exception as e:
                error_msg = f"Email sending failed: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        # Step 4: Upload to Storj (if enabled and PDF generated)
        if request.upload_to_storj and pdf_data and storj_client:
            logger.info(f"Uploading prescription to Storj")
            try:
                # Save PDF to temporary file for upload
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.pdf',
                    prefix=f'prescription_{request.prescription_id}_'
                ) as tmp_file:
                    tmp_file.write(pdf_data)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Upload to Storj
                    storj_key = storj_client.upload_document(
                        file_path=tmp_file_path,
                        patient_id=prescription_record.patient_id,
                        doc_type='prescription',
                        metadata={
                            'prescription_id': request.prescription_id,
                            'patient_id': prescription_record.patient_id
                        }
                    )
                    
                    if storj_key:
                        result.storj_uploaded = True
                        result.document_id = storj_key
                        
                        # Generate shareable URL
                        share_url = storj_client.generate_download_url(
                            object_key=storj_key,
                            expiration_hours=24 * 7  # 7 days
                        )
                        result.pdf_url = share_url
                        logger.info(f"Uploaded to Storj: {storj_key}")
                    else:
                        result.errors.append("Storj upload returned empty key")
                        
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
                        
            except Exception as e:
                error_msg = f"Storj upload failed: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        # Step 5: Create Medicine Reminders (if enabled)
        if request.create_reminders:
            logger.info(f"Creating medicine reminders")
            try:
                reminders_created = reminder_engine.create_medicine_schedules_from_prescription(
                    request.prescription_id
                )
                if reminders_created:
                    result.reminders_created = True
                    logger.info("Medicine reminders created successfully")
                else:
                    result.errors.append("Reminder creation returned False")
            except Exception as e:
                error_msg = f"Reminder creation failed: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        # Step 6: Share via WhatsApp (if enabled and we have a URL)
        if request.share_via_whatsapp and result.pdf_url and request.patient_phone:
            logger.info(f"Sharing prescription via WhatsApp")
            try:
                from app.medicine_reminders.meta_whatsapp_client import MetaWhatsAppClient
                whatsapp_client = MetaWhatsAppClient()
                
                message = f"""
📋 *Your Prescription is Ready!*

Your prescription has been generated and is ready for download.

🔗 *Download Link:*
{result.pdf_url}

⏱️ *Link expires in 7 days*

Click the link above to download your prescription PDF.

- AyurEze Healthcare Team 🌿
                """.strip()
                
                whatsapp_result = whatsapp_client.send_text_message(
                    to=request.patient_phone,
                    message=message
                )
                
                result.whatsapp_shared = True
                logger.info("WhatsApp message sent successfully")
                
            except Exception as e:
                error_msg = f"WhatsApp sharing failed: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        # Determine overall success
        result.success = (
            result.pdf_generated and 
            (not request.send_email or result.email_sent) and
            (not request.upload_to_storj or result.storj_uploaded) and
            (not request.create_reminders or result.reminders_created)
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _convert_to_prescription_request(prescription_record, db: Session) -> PrescriptionRequest:
    """Convert database Prescription to PrescriptionRequest for PDF service"""
    from app.shopify_models import PatientInfo, DoctorInfo, MedicineItem
    
    # Get patient info
    from app.database_models import Patient
    patient = db.query(Patient).filter(Patient.patient_id == prescription_record.patient_id).first()
    
    patient_info = PatientInfo(
        name=patient.name if patient else "Unknown Patient",
        contact=patient.email if patient else "",
        age=patient.age if patient else 0,
        gender=getattr(patient, 'gender', 'Not Specified')
    )
    
    # Get doctor info (if available)
    doctor_info = DoctorInfo(
        name=getattr(prescription_record, 'doctor_name', 'Dr. AyurEze'),
        specialization=getattr(prescription_record, 'doctor_specialization', 'Ayurveda'),
        registration_number=getattr(prescription_record, 'doctor_license', 'AY12345'),
        phone=getattr(prescription_record, 'doctor_phone', '+91 98765 43210'),
        email=getattr(prescription_record, 'doctor_email', 'doctor@ayureze.com')
    )
    
    # Get medicines from prescription
    medicines = []
    if hasattr(prescription_record, 'medicines') and prescription_record.medicines:
        import json
        medicine_list = prescription_record.medicines
        if isinstance(medicine_list, str):
            medicine_list = json.loads(medicine_list)
        
        for med in medicine_list:
            medicines.append(MedicineItem(
                name=med.get('name', ''),
                dosage=med.get('dosage', ''),
                frequency=med.get('frequency', ''),
                duration=med.get('duration', ''),
                timing=med.get('timing', ''),
                quantity=med.get('quantity', 1),
                instructions=med.get('instructions', '')
            ))
    
    return PrescriptionRequest(
        patient=patient_info,
        doctor=doctor_info,
        medicines=medicines,
        diagnosis=getattr(prescription_record, 'diagnosis', ''),
        notes=getattr(prescription_record, 'notes', '')
    )

@router.get("/status/{prescription_id}")
async def check_workflow_status(
    prescription_id: str,
    db: Session = Depends(get_db_dependency)
):
    """Check the status of a prescription workflow execution"""
    
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        from app.database_models import DocumentRecord, MedicineSchedule
        
        # Check if prescription exists
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.prescription_id == prescription_id
        ).first()
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Check for associated documents (PDF uploaded to Storj)
        documents = db.query(DocumentRecord).filter(
            DocumentRecord.related_prescription_id == prescription_id
        ).all()
        
        # Check for medicine schedules (reminders created)
        schedules = db.query(MedicineSchedule).filter(
            MedicineSchedule.prescription_id == prescription_id
        ).all()
        
        return {
            "prescription_id": prescription_id,
            "prescription_exists": True,
            "documents_count": len(documents),
            "has_pdf": len(documents) > 0,
            "medicine_schedules_count": len(schedules),
            "has_reminders": len(schedules) > 0,
            "documents": [
                {
                    "document_id": doc.document_id,
                    "filename": doc.original_filename,
                    "uploaded_at": doc.created_at.isoformat()
                }
                for doc in documents
            ],
            "schedules": [
                {
                    "schedule_id": sched.schedule_id,
                    "medicine_name": sched.medicine_name,
                    "times_per_day": sched.times_per_day
                }
                for sched in schedules
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
