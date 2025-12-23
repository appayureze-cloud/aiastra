"""
Dedicated endpoint for manual prescription PDF sending
"""

import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, status
from types import SimpleNamespace

from .shopify_client import shopify_client
from .prescription_pdf_service import prescription_pdf_service

logger = logging.getLogger(__name__)

# Create router for PDF endpoints
router = APIRouter(prefix="/prescription-pdf", tags=["Prescription PDF"])

@router.post("/send")
async def send_prescription_pdf_manually(request: Dict):
    """
    Manually send prescription PDF when doctor clicks "Send Prescription"
    
    This endpoint allows doctors to generate and send prescription PDFs
    after creating a prescription.
    
    Required fields:
    - draft_order_id: The Shopify draft order ID
    - patient_email: Valid email address for the patient
    - doctor_email: (Optional) Doctor's email for CC
    """
    try:
        # Extract required fields
        draft_order_id = request.get("draft_order_id")
        patient_email = request.get("patient_email")
        doctor_email = request.get("doctor_email")
        
        if not draft_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="draft_order_id is required"
            )
        
        if not patient_email or '@' not in patient_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid patient_email is required"
            )
        
        # Get order details from Shopify to reconstruct prescription
        order_details = shopify_client.get_draft_order(str(draft_order_id))
        
        # Parse prescription data from order
        notes = order_details.get("note", "")
        
        # Extract structured data from notes
        patient_info = {"name": "Patient", "patient_id": "Unknown", "age": 30, "contact": patient_email}
        doctor_info = {"name": "Doctor", "license": "Unknown", "hospital": "Unknown"}
        diagnosis = "Medical consultation"
        
        if "Patient:" in notes:
            try:
                patient_part = notes.split("Patient:")[1].split("|")[0].strip()
                patient_name = patient_part.split(",")[0].strip()
                if "ID:" in patient_part:
                    patient_id = patient_part.split("ID:")[1].split(")")[0].strip()
                    patient_info.update({"name": patient_name, "patient_id": patient_id})
            except:
                pass
        
        if "Doctor:" in notes:
            try:
                doctor_part = notes.split("Doctor:")[1].split("|")[0].strip()
                doctor_name = doctor_part.split("(")[0].strip()
                doctor_info.update({"name": doctor_name})
            except:
                pass
        
        if "PRESCRIPTION -" in notes:
            try:
                diagnosis = notes.split("PRESCRIPTION -")[1].split("|")[0].strip()
            except:
                pass
        
        # Extract medicines from line items
        prescriptions = []
        for item in order_details.get("line_items", []):
            properties = {prop.get("name"): prop.get("value") for prop in item.get("properties", [])}
            
            prescription_item = {
                "medicine": item.get("name", ""),
                "dose": properties.get("Dose", "As directed"),
                "schedule": properties.get("Schedule", "As needed"),
                "timing": properties.get("Timing", "With meals"),
                "duration": properties.get("Duration", "As needed"),
                "instructions": properties.get("Instructions", "Follow doctor's advice")
            }
            prescriptions.append(prescription_item)
        
        # Create mock prescription request for PDF generation
        mock_prescription = SimpleNamespace()
        mock_prescription.patient = SimpleNamespace(**patient_info)
        mock_prescription.doctor = SimpleNamespace(**doctor_info)
        mock_prescription.diagnosis = diagnosis
        mock_prescription.prescriptions = [SimpleNamespace(**item) for item in prescriptions]
        
        # Generate and send prescription PDF
        pdf_result = prescription_pdf_service.generate_and_send_prescription(
            prescription=mock_prescription,
            patient_email=patient_email,
            doctor_email=doctor_email
        )
        
        logger.info(f"Manual prescription PDF sent for order: {draft_order_id}")
        
        return {
            "status": "success",
            "message": "Prescription PDF sent successfully",
            "draft_order_id": draft_order_id,
            "recipient_email": patient_email,
            "pdf_details": pdf_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending prescription PDF manually: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send prescription PDF: {str(e)}"
        )