"""
Firebase Email Service for sending prescription PDFs
Uses Firebase Admin SDK for email functionality
"""

import os
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class FirebaseEmailService:
    """Firebase-based email service for sending prescription PDFs"""
    
    def __init__(self):
        self.firebase_initialized = False
        self.db = None
        
        if FIREBASE_AVAILABLE:
            self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.info("Firebase already initialized")
                self.firebase_initialized = True
                self.db = firestore.client()
                return
            
            # Load Firebase service account from environment
            firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if firebase_service_account:
                service_account_info = json.loads(firebase_service_account)
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
                
                self.db = firestore.client()
                self.firebase_initialized = True
                logger.info("Firebase initialized successfully for email service")
            else:
                logger.error("FIREBASE_SERVICE_ACCOUNT environment variable not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.firebase_initialized = False
    
    def send_prescription_email(
        self, 
        recipient_email: str, 
        pdf_content: bytes, 
        patient_name: str,
        doctor_name: str = "Doctor",
        doctor_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send prescription PDF via email using SMTP with Firebase logging
        
        Args:
            recipient_email: Patient's email address
            pdf_content: PDF file content as bytes
            patient_name: Patient's name for personalization
            doctor_name: Doctor's name
            doctor_email: Optional doctor email for CC
        
        Returns:
            Dictionary with email sending status and details
        """
        message_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"Prescription_{patient_name.replace(' ', '_')}_{timestamp}.pdf"
        
        try:
            # Try SMTP email sending first
            smtp_result = self._send_smtp_email(
                recipient_email, pdf_content, patient_name, doctor_name, 
                doctor_email, message_id, filename
            )
            
            if smtp_result['status'] == 'success':
                # Log successful email to Firebase
                email_log = {
                    'message_id': message_id,
                    'recipient': recipient_email,
                    'sender': smtp_result.get('sender', 'noreply@ayureze.com'),
                    'subject': f'Prescription from {doctor_name}',
                    'patient_name': patient_name,
                    'doctor_name': doctor_name,
                    'filename': filename,
                    'pdf_size_bytes': len(pdf_content),
                    'status': 'sent',
                    'sent_at': current_time,
                    'method': 'smtp_email'
                }
                
                if self.firebase_initialized and self.db:
                    self.db.collection('email_logs').document(message_id).set(email_log)
                    logger.info(f"Email log stored in Firebase with ID: {message_id}")
                
                logger.info(f"Email sent successfully to {recipient_email} via SMTP")
                return smtp_result
            
            else:
                # SMTP failed, try Replit Mail fallback
                logger.warning(f"SMTP failed, trying Replit Mail fallback: {smtp_result.get('error')}")
                return self._try_replit_mail_fallback(
                    recipient_email, pdf_content, patient_name, doctor_name, 
                    doctor_email, message_id, filename
                )
                
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            
            # Log failed attempt to Firebase
            email_log = {
                'message_id': message_id,
                'recipient': recipient_email,
                'subject': f'Prescription from {doctor_name}',
                'patient_name': patient_name,
                'doctor_name': doctor_name,
                'filename': filename,
                'pdf_size_bytes': len(pdf_content),
                'status': 'failed',
                'error': str(e),
                'sent_at': current_time,
                'method': 'email_failed'
            }
            
            if self.firebase_initialized and self.db:
                self.db.collection('email_logs').document(message_id).set(email_log)
            
            return {
                'status': 'error',
                'error': str(e),
                'recipient': recipient_email,
                'message_id': message_id,
                'method': 'email_failed'
            }
    
    def _send_smtp_email(
        self, recipient_email: str, pdf_content: bytes, patient_name: str,
        doctor_name: str, doctor_email: Optional[str], message_id: str, filename: str
    ) -> Dict[str, Any]:
        """Send email via SMTP with ayureze.in webmail configuration"""
        try:
            # Use ayureze.in SMTP configuration
            smtp_host = "mail.ayureze.in"
            smtp_port = 465  # SSL port
            smtp_username = "no-reply@ayureze.in"
            smtp_password = "Ayureze@1234"
            smtp_from = "no-reply@ayureze.in"
            
            logger.info(f"Attempting SMTP email via {smtp_host}:{smtp_port} to {recipient_email}")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = recipient_email
            msg['Subject'] = f"Your Ayurvedic Prescription - {patient_name}"
            msg['Message-ID'] = f"<{message_id}@ayureze.com>"
            
            if doctor_email and '@' in doctor_email:
                msg['Reply-To'] = doctor_email
            
            # Email body
            email_body = f"""
Dear {patient_name},

Your Ayurvedic prescription from Dr. {doctor_name} is ready!

Prescription Details:
- Patient: {patient_name}
- Doctor: {doctor_name}
- Date: {datetime.now().strftime('%B %d, %Y')}

Your prescription PDF is attached to this email. Please:
1. Review all medicines and dosages carefully
2. Follow the timing and instructions provided
3. Contact Dr. {doctor_name} if you have any questions

For your health and safety:
- Store medicines in a cool, dry place
- Keep away from direct sunlight and children
- Take medicines only as prescribed

Best regards,
Ayureze Healthcare Team

Note: This is an automated email from your healthcare provider.
            """.strip()
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Attach PDF
            attachment = MIMEBase('application', 'pdf')
            attachment.set_payload(pdf_content)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(attachment)
            
            # Send email via SSL (port 465)
            logger.info(f"Connecting to SMTP SSL server: {smtp_host}:{smtp_port}")
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            
            logger.info(f"Logging in with username: {smtp_username}")
            server.login(smtp_username, smtp_password)
            
            logger.info(f"Sending email to: {recipient_email}")
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully via ayureze.in SMTP to {recipient_email}")
            
            current_time = datetime.now().isoformat()
            
            return {
                'status': 'success',
                'recipient': recipient_email,
                'message_id': message_id,
                'filename': filename,
                'sent_at': current_time,
                'method': 'smtp_email',
                'sender': smtp_from,
                'pdf_size_bytes': len(pdf_content)
            }
            
        except Exception as e:
            logger.error(f"SMTP email failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'method': 'smtp_failed'
            }
    
    def _try_replit_mail_fallback(
        self, recipient_email: str, pdf_content: bytes, patient_name: str,
        doctor_name: str, doctor_email: Optional[str], message_id: str, filename: str
    ) -> Dict[str, Any]:
        """Fallback to Replit Mail if SMTP fails"""
        try:
            # Use the working Replit Mail API approach
            import base64
            import requests
            
            # Get Replit authentication token
            repl_identity = os.getenv("REPL_IDENTITY")
            web_repl_renewal = os.getenv("WEB_REPL_RENEWAL")
            
            auth_token = None
            if repl_identity:
                auth_token = f"repl {repl_identity}"
            elif web_repl_renewal:
                auth_token = f"depl {web_repl_renewal}"
            
            if not auth_token:
                raise Exception("No Replit authentication token found")
            
            # Convert PDF to base64 for Replit Mail
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Email content
            subject = f"Your Ayurvedic Prescription - {patient_name}"
            
            text_content = f"""
Dear {patient_name},

Your Ayurvedic prescription from Dr. {doctor_name} is ready!

Prescription Details:
- Patient: {patient_name}
- Doctor: {doctor_name}
- Date: {datetime.now().strftime('%B %d, %Y')}

Your prescription PDF is attached to this email. Please:
1. Review all medicines and dosages carefully
2. Follow the timing and instructions provided
3. Contact Dr. {doctor_name} if you have any questions

For your health and safety:
- Store medicines in a cool, dry place
- Keep away from direct sunlight and children
- Take medicines only as prescribed

Best regards,
Ayureze Healthcare Team

Note: This is an automated email from your healthcare provider.
            """.strip()
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5530; text-align: center;">Your Ayurvedic Prescription</h2>
                    
                    <p>Dear <strong>{patient_name}</strong>,</p>
                    
                    <p>Your Ayurvedic prescription from <strong>Dr. {doctor_name}</strong> is ready!</p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c5530; margin-top: 0;">Prescription Details:</h3>
                        <ul style="margin: 0;">
                            <li><strong>Patient:</strong> {patient_name}</li>
                            <li><strong>Doctor:</strong> {doctor_name}</li>
                            <li><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <p><strong>Your prescription PDF is attached to this email.</strong> Please:</p>
                    <ol>
                        <li>Review all medicines and dosages carefully</li>
                        <li>Follow the timing and instructions provided</li>
                        <li>Contact Dr. {doctor_name} if you have any questions</li>
                    </ol>
                    
                    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c5530; margin-top: 0;">For your health and safety:</h4>
                        <ul style="margin: 0;">
                            <li>Store medicines in a cool, dry place</li>
                            <li>Keep away from direct sunlight and children</li>
                            <li>Take medicines only as prescribed</li>
                        </ul>
                    </div>
                    
                    <p>Best regards,<br>
                    <strong>Ayureze Healthcare Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            # Prepare email payload
            email_payload = {
                "to": recipient_email,
                "subject": subject,
                "text": text_content,
                "html": html_content,
                "attachments": [{
                    "filename": filename,
                    "content": pdf_base64,
                    "contentType": "application/pdf",
                    "encoding": "base64"
                }]
            }
            
            # Add CC to doctor if provided
            if doctor_email and '@' in doctor_email:
                email_payload["cc"] = doctor_email
            
            # Send email via Replit Mail API
            response = requests.post(
                "https://connectors.replit.com/api/v2/mailer/send",
                headers={
                    "Content-Type": "application/json",
                    "X_REPLIT_TOKEN": auth_token,
                },
                json=email_payload,
                timeout=30
            )
            
            if not response.ok:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                raise Exception(f"Replit Mail API error: {error_data}")
            
            result = response.json()
            current_time = datetime.now().isoformat()
            
            # Log successful email to Firebase
            if self.firebase_initialized and self.db:
                email_log = {
                    'message_id': message_id,
                    'recipient': recipient_email,
                    'sender': 'replit-mail-api',
                    'subject': subject,
                    'patient_name': patient_name,
                    'doctor_name': doctor_name,
                    'filename': filename,
                    'pdf_size_bytes': len(pdf_content),
                    'status': 'sent',
                    'sent_at': current_time,
                    'method': 'replit_mail_api',
                    'replit_message_id': result.get("messageId")
                }
                self.db.collection('email_logs').document(message_id).set(email_log)
                logger.info(f"Email log stored in Firebase with ID: {message_id}")
            
            logger.info(f"Email sent successfully via Replit Mail API to {recipient_email}")
            
            return {
                'status': 'success',
                'recipient': recipient_email,
                'message_id': message_id,
                'filename': filename,
                'sent_at': current_time,
                'method': 'replit_mail_api',
                'pdf_size_bytes': len(pdf_content),
                'replit_message_id': result.get("messageId")
            }
            
        except Exception as e:
            logger.error(f"Replit Mail fallback failed: {e}")
            return self._fallback_email_log(recipient_email, patient_name)
    
    def _fallback_email_log(self, recipient_email: str, patient_name: str) -> Dict[str, Any]:
        """Fallback when Firebase is not available"""
        message_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        logger.warning(f"Firebase not available, logging email attempt locally")
        logger.info(f"Would send prescription PDF to: {recipient_email}")
        logger.info(f"Patient: {patient_name}")
        logger.info(f"Message ID: {message_id}")
        
        return {
            'status': 'logged_locally',
            'recipient': recipient_email,
            'message_id': message_id,
            'sent_at': current_time,
            'method': 'firebase_fallback',
            'note': 'Firebase not available, email logged locally'
        }
    
    def get_email_logs(self, limit: int = 10) -> list:
        """Retrieve recent email logs from Firebase"""
        try:
            if not self.firebase_initialized or not self.db:
                return []
            
            # Get recent email logs
            docs = self.db.collection('email_logs').order_by('sent_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            logs = []
            for doc in docs:
                log_data = doc.to_dict()
                log_data['id'] = doc.id
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving email logs: {e}")
            return []

# Global Firebase email service instance
firebase_email_service = FirebaseEmailService()