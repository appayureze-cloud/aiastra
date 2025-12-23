"""
Prescription PDF Generation and Email Service
Automatically generates and sends prescription PDFs when doctors save prescriptions
"""

import os
import logging
import base64
import requests
from typing import Dict, List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, navy, darkgray
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

from .shopify_models import PrescriptionRequest
from .firebase_email_service import firebase_email_service
from .pdf_form_filler import PrescriptionPDFFiller

logger = logging.getLogger(__name__)

class PrescriptionPDFService:
    """Service for generating prescription PDFs and sending via email"""
    
    def __init__(self):
        self.repl_identity = os.getenv("REPL_IDENTITY")
        self.web_repl_renewal = os.getenv("WEB_REPL_RENEWAL")
        
        # Set authentication token for Replit Mail
        self.auth_token = None
        if self.repl_identity:
            self.auth_token = f"repl {self.repl_identity}"
        elif self.web_repl_renewal:
            self.auth_token = f"depl {self.web_repl_renewal}"
        
        if not self.auth_token:
            logger.warning("No Replit authentication token found - email functionality disabled")
    
    def generate_prescription_pdf(self, prescription: PrescriptionRequest) -> bytes:
        """Fill the actual Ayureze Healthcare PDF template with prescription data"""
        try:
            # Use the actual uploaded PDF and fill it with prescription data
            pdf_filler = PrescriptionPDFFiller()
            pdf_data = pdf_filler.fill_prescription_pdf(prescription)
            
            logger.info(f"Filled actual Ayureze PDF for patient: {getattr(prescription.patient, 'name', 'Unknown')}")
            return pdf_data
            
        except Exception as e:
            logger.error(f"Failed to generate prescription PDF: {e}")
            raise
    
    def send_prescription_email(
        self, 
        prescription: PrescriptionRequest, 
        pdf_data: bytes,
        patient_email: Optional[str] = None,
        doctor_email: Optional[str] = None
    ) -> Dict:
        """Send prescription PDF via email using Firebase Email Service"""
        try:
            # Determine recipient email
            recipient_email = patient_email or prescription.patient.contact
            if not recipient_email or '@' not in recipient_email:
                raise Exception("Valid patient email required for sending prescription")
            
            # Get patient and doctor names
            patient_name = getattr(prescription.patient, 'name', 'Patient')
            doctor_name = getattr(prescription.doctor, 'name', 'Doctor')
            
            # Use Firebase email service to send prescription
            email_result = firebase_email_service.send_prescription_email(
                recipient_email=recipient_email,
                pdf_content=pdf_data,
                patient_name=patient_name,
                doctor_name=doctor_name,
                doctor_email=doctor_email
            )
            
            logger.info(f"Prescription email sent successfully to {recipient_email}")
            
            return {
                'status': 'success',
                'email_sent': True,
                'email_details': email_result
            }
            
        except Exception as e:
            logger.error(f"Failed to send prescription email: {e}")
            return {
                'status': 'error',
                'email_sent': False,
                'error': str(e)
            }
    
    def generate_and_send_prescription(
        self, 
        prescription: PrescriptionRequest,
        patient_email: Optional[str] = None,
        doctor_email: Optional[str] = None
    ) -> Dict:
        """Complete workflow: Generate PDF and send via email"""
        try:
            patient_name = getattr(prescription.patient, 'name', 'Unknown')
            logger.info(f"Starting prescription PDF generation and email for patient: {patient_name}")
            
            # Generate PDF
            pdf_data = self.generate_prescription_pdf(prescription)
            
            # Send email with PDF attachment
            email_result = self.send_prescription_email(
                prescription=prescription,
                pdf_data=pdf_data,
                patient_email=patient_email,
                doctor_email=doctor_email
            )
            
            return {
                "status": "success",
                "pdf_generated": True,
                "email_sent": True,
                "email_details": email_result,
                "pdf_size_bytes": len(pdf_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate and send prescription: {e}")
            return {
                "status": "error",
                "error": str(e),
                "pdf_generated": False,
                "email_sent": False
            }

# Global instance
prescription_pdf_service = PrescriptionPDFService()