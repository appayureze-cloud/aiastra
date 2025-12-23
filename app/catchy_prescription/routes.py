"""
Catchy Prescription API Routes
Endpoints for generating attractive prescriptions from PDF templates or structured data
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response
from typing import Optional
from datetime import datetime, timedelta

from .extractor import template_analyzer
from .renderer import catchy_renderer
from ..shopify_models import PrescriptionRequest
from ..firebase_email_service import firebase_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescriptions", tags=["Catchy Prescriptions"])

@router.post("/catchy-from-upload")
async def generate_catchy_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email_to: Optional[str] = None,
    patient_name: Optional[str] = None,
    doctor_name: Optional[str] = None
):
    """
    Generate catchy prescription from uploaded PDF template
    Extracts content and creates an attractive, professional prescription
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('application/pdf'):
            raise HTTPException(status_code=415, detail="Only PDF files are supported")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        logger.info(f"Processing uploaded PDF: {file.filename} ({len(file_content)} bytes)")
        
        # Extract prescription data from PDF
        prescription_data = template_analyzer.extract_prescription_from_pdf(file_content)
        
        # Override with provided parameters if available
        if patient_name:
            prescription_data.patient.name = patient_name
        if doctor_name and prescription_data.doctor:
            prescription_data.doctor.name = doctor_name
        
        # Generate catchy prescription PDF
        catchy_pdf_bytes = catchy_renderer.generate_catchy_prescription(prescription_data)
        
        # Send email if requested
        if email_to:
            background_tasks.add_task(
                _send_catchy_prescription_email,
                catchy_pdf_bytes,
                email_to,
                prescription_data.patient.name
            )
        
        # Return PDF as response
        filename = f"Catchy_Prescription_{prescription_data.patient.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=catchy_pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(catchy_pdf_bytes))
            }
        )
        
    except ValueError as e:
        logger.error(f"PDF processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating catchy prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate catchy prescription")

@router.post("/catchy-from-data")
async def generate_catchy_from_data(
    prescription: PrescriptionRequest,
    background_tasks: BackgroundTasks,
    email_to: Optional[str] = None
):
    """
    Generate catchy prescription from structured prescription data
    Creates an attractive, professional prescription PDF
    """
    try:
        logger.info(f"Generating catchy prescription for patient: {prescription.patient.name}")
        
        # Generate catchy prescription PDF
        catchy_pdf_bytes = catchy_renderer.generate_catchy_prescription(prescription)
        
        # Send email if requested
        if email_to:
            background_tasks.add_task(
                _send_catchy_prescription_email,
                catchy_pdf_bytes,
                email_to,
                prescription.patient.name
            )
        
        # Return PDF as response
        filename = f"Catchy_Prescription_{prescription.patient.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=catchy_pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(catchy_pdf_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate catchy prescription from data: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate catchy prescription")

@router.post("/auto-generate-catchy")
async def auto_generate_catchy_prescription(
    background_tasks: BackgroundTasks,
    patient_name: str = "Wellness Seeker",
    patient_age: int = 35,
    doctor_name: str = "Dr. Ayurveda Specialist",
    email_to: Optional[str] = None
):
    """
    Auto-generate a sample catchy prescription with attractive content
    Perfect for demonstrating the catchy prescription system
    """
    try:
        logger.info(f"Auto-generating catchy prescription for demo: {patient_name}")
        
        # Create sample attractive prescription data
        sample_prescription = _create_sample_catchy_prescription(patient_name, patient_age, doctor_name)
        
        # Generate catchy prescription PDF
        catchy_pdf_bytes = catchy_renderer.generate_catchy_prescription(sample_prescription)
        
        # Send email if requested
        if email_to:
            background_tasks.add_task(
                _send_catchy_prescription_email,
                catchy_pdf_bytes,
                email_to,
                patient_name
            )
        
        # Return PDF as response
        filename = f"Auto_Catchy_Prescription_{patient_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=catchy_pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(catchy_pdf_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to auto-generate catchy prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-generate catchy prescription")

async def _send_catchy_prescription_email(pdf_bytes: bytes, email_to: str, patient_name: str):
    """Background task to send catchy prescription via email"""
    try:
        filename = f"Catchy_Prescription_{patient_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        subject = f"🌿 Your Ayurvedic Prescription - {patient_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="background: linear-gradient(90deg, #2E8B57, #3CB371); padding: 20px; text-align: center; color: white;">
                <h1>🌿 AYUREZE HEALTHCARE</h1>
                <p>Empowering Health through Authentic Ayurveda</p>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #2E8B57;">Dear {patient_name},</h2>
                
                <p>Your personalized Ayurvedic prescription is ready! Our team has carefully crafted this wellness plan to support your health journey.</p>
                
                <div style="background: #F5F5F5; padding: 15px; border-left: 4px solid #FFD700; margin: 20px 0;">
                    <h3 style="color: #2E8B57; margin: 0;">📋 Your Prescription Includes:</h3>
                    <ul style="margin: 10px 0;">
                        <li>🌿 Personalized Ayurvedic medicines</li>
                        <li>📅 Detailed dosage and timing schedule</li>
                        <li>🎯 Targeted wellness recommendations</li>
                        <li>📞 Follow-up consultation guidance</li>
                    </ul>
                </div>
                
                <p><strong>Important:</strong> Please follow the prescribed regimen carefully for optimal results. Feel free to contact us if you have any questions.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; font-size: 14px;">
                        📞 +91-89689 68156 | 🌐 www.ayureze.in | ✉️ support@ayureze.in
                    </p>
                </div>
                
                <p style="color: #666; font-size: 12px; text-align: center;">
                    This prescription was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email with PDF attachment
        result = await firebase_email_service.send_prescription_email(
            to_email=email_to,
            subject=subject,
            body=body,
            pdf_attachment=pdf_bytes,
            filename=filename
        )
        
        if result.get("status") == "success":
            logger.info(f"Catchy prescription email sent successfully to {email_to}")
        else:
            logger.error(f"Failed to send catchy prescription email: {result}")
            
    except Exception as e:
        logger.error(f"Failed to send catchy prescription email: {e}")

def _create_sample_catchy_prescription(patient_name: str, patient_age: int, doctor_name: str) -> PrescriptionRequest:
    """Create a sample catchy prescription with attractive content"""
    from ..shopify_models import PatientInfo, DoctorInfo, PrescriptionItem
    
    # Create attractive sample data
    sample_patient = PatientInfo(
        name=patient_name,
        age=patient_age,
        patient_id=f"AY{datetime.now().strftime('%Y%m%d')}{patient_age}",
        contact="+91-9876543210",
        date=datetime.now().strftime("%d/%m/%Y"),
        next_review=(datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
    )
    
    sample_doctor = DoctorInfo(
        name=doctor_name,
        regn_no=f"AY{datetime.now().year}",
        contact="+91-89689 68156"
    )
    
    # Attractive sample medicines
    sample_medicines = [
        PrescriptionItem(
            medicine="Ashwagandha Capsules",
            dose="2 capsules",
            schedule="Twice daily",
            timing="After breakfast and dinner",
            duration="30 days",
            instructions="Take with warm milk for enhanced absorption and stress relief",
            quantity=1
        ),
        PrescriptionItem(
            medicine="Triphala Churna",
            dose="1 teaspoon",
            schedule="Once daily",
            timing="Before breakfast",
            duration="21 days",
            instructions="Mix with honey on empty stomach for digestive wellness",
            quantity=1
        ),
        PrescriptionItem(
            medicine="Brahmi Ghrita",
            dose="5ml",
            schedule="Twice daily",
            timing="After lunch and dinner",
            duration="45 days",
            instructions="Take with warm water for mental clarity and cognitive support",
            quantity=1
        )
    ]
    
    return PrescriptionRequest(
        patient=sample_patient,
        diagnosis="Comprehensive Ayurvedic wellness consultation for stress management, digestive health, and cognitive enhancement",
        prescriptions=sample_medicines,
        doctor=sample_doctor,
        external_therapies=[
            "Daily Pranayama (breathing exercises) - 15 minutes morning and evening",
            "Abhyanga (self-massage) with warm sesame oil - 3 times per week",
            "Meditation and mindfulness practice - 20 minutes daily"
        ],
        doctor_notes="Follow the prescribed Ayurvedic regimen consistently for optimal wellness results. Maintain regular sleep schedule, balanced nutrition, and gentle physical activity. Return for follow-up consultation as scheduled."
    )