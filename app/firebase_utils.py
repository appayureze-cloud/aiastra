"""
Firebase Cloud Messaging utilities for push notifications
"""

import os
import json
import logging
from typing import Dict, Optional
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

class FirebaseNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    def __init__(self):
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.initialized = True
                logger.info("Firebase already initialized")
                return
            
            # Get service account from environment variable
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
            
            if not service_account_json:
                logger.error("FIREBASE_SERVICE_ACCOUNT environment variable not set")
                return
            
            # Parse the JSON string (fixed: added validation)
            service_account_info = json.loads(service_account_json)
            
            # Validate required fields (fixed Bug #7)
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in service_account_info]
            
            if missing_fields:
                logger.error(f"Missing required fields in FIREBASE_SERVICE_ACCOUNT: {', '.join(missing_fields)}")
                return
            
            # Validate type is service_account
            if service_account_info.get('type') != 'service_account':
                logger.error(f"Invalid type in FIREBASE_SERVICE_ACCOUNT: expected 'service_account', got '{service_account_info.get('type')}'")
                return
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            
            self.initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    
    def send_push_notification(
        self, 
        token: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send push notification to a specific device
        
        Args:
            token: FCM registration token
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialized:
            logger.error("Firebase not initialized, cannot send notification")
            return False
        
        try:
            # Create the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Push notification sent successfully: {response}")
            return True
            
        except Exception as e:
            # Handle specific Firebase messaging errors
            error_msg = str(e)
            if "invalid" in error_msg.lower() or "argument" in error_msg.lower():
                logger.error(f"Invalid FCM token or message format: {e}")
            elif "unregistered" in error_msg.lower():
                logger.error(f"FCM token is unregistered: {e}")
            else:
                logger.error(f"Firebase messaging error: {e}")
            return False
    
    def send_prescription_notification(
        self,
        token: str,
        doctor_name: str,
        patient_name: str,
        invoice_url: str,
        draft_order_id: str
    ) -> bool:
        """
        Send prescription-specific push notification
        
        Args:
            token: FCM registration token
            doctor_name: Name of the prescribing doctor
            patient_name: Name of the patient
            invoice_url: Shopify invoice URL for payment
            draft_order_id: Shopify draft order ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        title = f"New Prescription from Dr. {doctor_name}"
        body = f"Hi {patient_name}, your prescription is ready. Tap to view and order medicines."
        
        data = {
            "type": "prescription",
            "invoice_url": invoice_url,
            "draft_order_id": draft_order_id,
            "doctor_name": doctor_name
        }
        
        return self.send_push_notification(token, title, body, data)
    
    def is_available(self) -> bool:
        """Check if Firebase service is available"""
        return self.initialized

# Global Firebase service instance
firebase_service = FirebaseNotificationService()