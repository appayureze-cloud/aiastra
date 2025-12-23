"""
Notification management endpoints for FCM token storage and push notifications
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .firebase_utils import firebase_service
from .patient_tokens import patient_token_service

logger = logging.getLogger(__name__)

# Create router for notification endpoints
router = APIRouter(prefix="/notifications", tags=["Push Notifications"])

class FCMTokenRequest(BaseModel):
    """Request model for storing FCM token"""
    patient_id: str = Field(..., description="Unique patient identifier")
    fcm_token: str = Field(..., description="Firebase Cloud Messaging token")
    device_info: Optional[Dict] = Field(None, description="Optional device information")

class NotificationResponse(BaseModel):
    """Response model for notification operations"""
    status: str
    message: str
    patient_id: Optional[str] = None

@router.post("/store-fcm-token", response_model=NotificationResponse)
async def store_fcm_token(request: FCMTokenRequest):
    """
    Store or update patient's FCM token for push notifications
    
    This endpoint allows patient apps to register their FCM token
    so they can receive prescription notifications.
    """
    try:
        logger.info(f"Storing FCM token for patient: {request.patient_id}")
        
        # Validate that Firebase service is available
        if not firebase_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase service is not available"
            )
        
        # Store the token in Supabase
        success = patient_token_service.store_fcm_token(
            patient_id=request.patient_id,
            fcm_token=request.fcm_token,
            device_info=request.device_info
        )
        
        if success:
            logger.info(f"FCM token stored successfully for patient: {request.patient_id}")
            return NotificationResponse(
                status="success",
                message="FCM token stored successfully",
                patient_id=request.patient_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store FCM token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing FCM token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/remove-fcm-token/{patient_id}", response_model=NotificationResponse)
async def remove_fcm_token(patient_id: str):
    """
    Remove patient's FCM token
    
    This endpoint allows removing the FCM token when a patient
    logs out or no longer wants to receive notifications.
    """
    try:
        logger.info(f"Removing FCM token for patient: {patient_id}")
        
        success = patient_token_service.remove_fcm_token(patient_id)
        
        if success:
            logger.info(f"FCM token removed successfully for patient: {patient_id}")
            return NotificationResponse(
                status="success",
                message="FCM token removed successfully",
                patient_id=patient_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FCM token not found for this patient"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing FCM token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/test-notification/{patient_id}")
async def test_notification(patient_id: str):
    """
    Test push notification for a patient
    
    This endpoint sends a test notification to verify the
    FCM token is working correctly.
    """
    try:
        logger.info(f"Sending test notification to patient: {patient_id}")
        
        # Get patient's FCM token
        fcm_token = patient_token_service.get_fcm_token(patient_id)
        
        if not fcm_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FCM token not found for this patient"
            )
        
        # Send test notification
        success = firebase_service.send_push_notification(
            token=fcm_token,
            title="Test Notification",
            body="This is a test notification from Smart Auto-Cart system.",
            data={"type": "test", "timestamp": str(logger.name)}
        )
        
        if success:
            return NotificationResponse(
                status="success",
                message="Test notification sent successfully",
                patient_id=patient_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/service-status")
async def get_service_status():
    """
    Get notification service status
    
    Returns the status of Firebase and Supabase services
    used for push notifications.
    """
    firebase_status = firebase_service.is_available()
    supabase_status = patient_token_service.is_available()
    
    return {
        "firebase_service": "available" if firebase_status else "unavailable",
        "supabase_service": "available" if supabase_status else "unavailable",
        "notification_system": "operational" if (firebase_status and supabase_status) else "degraded"
    }