"""
Smart Auto-Cart Router - Prescription to Shopify Draft Order Pipeline
Fixed Bug #14: Added rate limiting to prevent abuse
"""

import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .shopify_models import (
    PrescriptionRequest, 
    ShopifyDraftOrderResponse, 
    ProductMappingInfo,
    ValidationError
)
from .shopify_client import shopify_client, ShopifyValidationError, ShopifyRateLimitError, ShopifyAPIError
from .shopify_api_service import shopify_api
from .firebase_utils import firebase_service
from .patient_tokens import patient_token_service
from .prescription_pdf_service import prescription_pdf_service
from .database_models import (
    get_db_dependency, 
    get_patient_by_code, 
    create_prescription_record,
    update_prescription_status
)
from .rate_limiter import rate_limiter, get_client_id

logger = logging.getLogger(__name__)

# Create router for Smart Auto-Cart endpoints
router = APIRouter(prefix="/shopify", tags=["Smart Auto-Cart"])

def _sanitize_patient_id(name: str) -> str:
    """Safely sanitize patient name to create valid ID (fixed Bug #5)"""
    import re
    # Remove all non-alphanumeric characters except underscore
    sanitized = re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_'))
    # Ensure it's not empty
    return sanitized if sanitized else "unknown_patient"


async def _send_prescription_notification(
    prescription: PrescriptionRequest, 
    draft_order_response: ShopifyDraftOrderResponse
):
    """
    Send push notification and WhatsApp message to patient about new prescription (fixed unsafe ID)
    
    Args:
        prescription: The prescription request
        draft_order_response: The created Shopify draft order response
    """
    try:
        # Get patient ID - check different possible fields (fixed with proper sanitization)
        patient_id = getattr(prescription.patient, 'patient_id', None) or \
                    getattr(prescription.patient, 'id', None)
        
        # If no ID, create safe fallback from name
        if not patient_id and hasattr(prescription.patient, 'name') and prescription.patient.name:
            patient_id = _sanitize_patient_id(prescription.patient.name)
            logger.info(f"Generated sanitized patient ID from name: {patient_id}")
        
        if not patient_id:
            logger.warning("No patient ID found, cannot send notification")
            return
        
        # Send push notification (existing Firebase integration)
        fcm_token = patient_token_service.get_fcm_token(patient_id)
        
        if fcm_token:
            success = firebase_service.send_prescription_notification(
                token=fcm_token,
                doctor_name=prescription.doctor.name,
                patient_name=prescription.patient.name,
                invoice_url=draft_order_response.invoice_url,
                draft_order_id=draft_order_response.draft_order_id
            )
            
            if success:
                logger.info(f"Push notification sent successfully to patient: {patient_id}")
            else:
                logger.warning(f"Failed to send push notification to patient: {patient_id}")
        
        # Send WhatsApp order confirmation
        patient_phone = getattr(prescription.patient, 'phone', None)
        if patient_phone:
            try:
                from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
                whatsapp_client = CustomWhatsAppClient()
                
                # Extract medicine names for the message
                medicine_names = [med.medicine_name for med in prescription.prescribed_medicines]
                
                await whatsapp_client.send_order_confirmation(
                    customer_phone=patient_phone,
                    customer_name=prescription.patient.name,
                    order_number=draft_order_response.draft_order_id,
                    order_total=str(draft_order_response.total_price),
                    items=medicine_names,
                    tracking_url=draft_order_response.invoice_url
                )
                
                logger.info(f"WhatsApp order confirmation sent to: {patient_phone}")
            except Exception as wa_error:
                logger.error(f"Failed to send WhatsApp confirmation: {wa_error}")
            
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        # Don't fail the entire request if notification fails

@router.post("/draft-order", response_model=ShopifyDraftOrderResponse)
async def create_prescription_draft_order(
    prescription: PrescriptionRequest, 
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    """
    Create Shopify draft order from doctor's prescription (with rate limiting)
    
    Rate Limit: 10 requests per minute per IP
    
    This endpoint:
    1. Validates prescription JSON against schema
    2. Maps medicines to Shopify product variant IDs
    3. Creates draft order with dosage instructions as properties
    4. Returns invoice URL for patient checkout
    """
    # Apply rate limiting (Bug #14 fix)
    client_ip = get_client_id(request)
    allowed, remaining = rate_limiter.is_allowed(
        client_id=client_ip,
        max_requests=10,
        window_seconds=60
    )
    
    if not allowed:
        logger.warning(f"⚠️ Rate limit exceeded for {client_ip} on draft order creation")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many draft order requests. Max 10 per minute.",
                "retry_after": 60
            }
        )
    
    try:
        logger.info(f"Creating draft order for patient: {prescription.patient.name} (remaining: {remaining} requests)")
        
        # Step 1: Verify patient if database is available
        verified_patient_id = prescription.patient.patient_id
        if db and prescription.patient.patient_id:
            patient_profile = get_patient_by_code(db, prescription.patient.patient_id.upper())
            if patient_profile:
                verified_patient_id = patient_profile.patient_id
                logger.info(f"✅ Patient verified: {patient_profile.name} (Code: {patient_profile.patient_code})")
        elif not prescription.patient.patient_id:
            logger.info("No patient ID provided, proceeding without database verification")
        
        # Step 2: Create draft order via Shopify client
        draft_order_response = shopify_client.create_draft_order(prescription)
        
        logger.info(f"Draft order created successfully: {draft_order_response.draft_order_id}")
        
        # Step 3: Save prescription record to database
        prescription_id = None
        if db:
            try:
                # Prepare medicine data for database storage
                medicines_data = []
                for rx_item in prescription.prescriptions:
                    medicine_data = {
                        "medicine_name": rx_item.medicine,
                        "dose": rx_item.dose,
                        "schedule": rx_item.schedule,
                        "timing": rx_item.timing,
                        "duration": rx_item.duration,
                        "instructions": rx_item.instructions,
                        "quantity": rx_item.quantity
                    }
                    medicines_data.append(medicine_data)
                
                # Create prescription record
                prescription_data = {
                    "patient_id": verified_patient_id,
                    "doctor_id": prescription.doctor.id,
                    "diagnosis": prescription.diagnosis,
                    "notes": prescription.notes,
                    "draft_order_id": str(draft_order_response.draft_order_id),
                    "invoice_url": draft_order_response.invoice_url,
                    "total_amount": str(draft_order_response.total_price),
                    "medicines": medicines_data
                }
                
                prescription_record = create_prescription_record(db, prescription_data)
                prescription_id = prescription_record.prescription_id
                
                logger.info(f"✅ Prescription saved: {prescription_id}")
                
            except Exception as e:
                logger.error(f"Failed to save prescription to database: {e}")
                # Continue without failing the entire process
        
        # Step 4: Generate and send prescription PDF
        try:
            pdf_result = prescription_pdf_service.generate_and_send_prescription(
                prescription=prescription,
                patient_email=prescription.patient.contact if (
                    hasattr(prescription.patient, 'contact') and 
                    prescription.patient.contact and 
                    '@' in prescription.patient.contact
                ) else None
            )
            logger.info(f"Prescription PDF result: {pdf_result}")
        except Exception as e:
            logger.warning(f"Failed to send prescription PDF (non-blocking): {e}")
        
        # Step 5: Send push notification if patient has FCM token
        notification_sent = False
        try:
            await _send_prescription_notification(prescription, draft_order_response)
            notification_sent = True
            
            # Update prescription status to "notified" if database available
            if db and prescription_id:
                update_prescription_status(
                    db=db,
                    prescription_id=prescription_id,
                    new_status="notified",
                    change_reason="Push notification sent to patient"
                )
                
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        
        # Step 6: Enhance response with prescription tracking
        enhanced_response = draft_order_response
        if prescription_id:
            enhanced_response.prescription_id = prescription_id
        enhanced_response.notification_sent = notification_sent
        enhanced_response.patient_verified = db is not None
        
        return enhanced_response
        
    except ShopifyValidationError as e:
        logger.error(f"Shopify validation error: {e}")
        # Return detailed validation errors with user-friendly messages
        error_details = {
            "error_type": "validation_failed",
            "user_message": e.user_friendly_message,
            "error_code": e.error_code,
            "field_errors": e.field_errors,
            "total_errors": len(e.field_errors),
            "recovery_suggestions": [
                "Please review the highlighted fields and correct any errors",
                "Ensure all required information is provided",
                "Contact support if you need help with the prescription format"
            ]
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_details
        )
    
    except ShopifyRateLimitError as e:
        logger.warning(f"Shopify rate limit exceeded: {e}")
        error_details = {
            "error_type": "rate_limit_exceeded",
            "user_message": e.user_friendly_message,
            "retry_after": e.retry_after,
            "calls_remaining": e.calls_remaining,
            "recovery_suggestions": [
                f"Please wait {e.retry_after} seconds and try again",
                "Our system is temporarily busy processing many requests",
                "Your prescription will be saved and you can retry shortly"
            ]
        }
        response = HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_details
        )
        response.headers = {"Retry-After": str(e.retry_after)}
        raise response
    
    except ShopifyAPIError as e:
        logger.error(f"Shopify API error: {e}")
        error_details = {
            "error_type": "shopify_api_error",
            "user_message": e.user_friendly_message,
            "status_code": e.status_code,
            "shopify_errors": e.shopify_errors,
            "recovery_suggestions": [
                "Please try again in a few moments",
                "If the problem persists, contact our support team",
                "Your prescription has been saved and can be processed later"
            ]
        }
        
        # Map status codes to appropriate HTTP status codes (fixed Bug #6)
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        if e.status_code == 401:
            http_status = status.HTTP_401_UNAUTHORIZED  # Fixed: was 503
        elif e.status_code == 403:
            http_status = status.HTTP_403_FORBIDDEN  # Fixed: was 503
        elif e.status_code == 404:
            http_status = status.HTTP_404_NOT_FOUND  # Fixed: was 422
        elif e.status_code == 422:
            http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif e.status_code and e.status_code >= 500:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        
        raise HTTPException(
            status_code=http_status,
            detail=error_details
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        # Legacy validation error handling
        error_details = {
            "error_type": "validation_error",
            "user_message": "There's an issue with your prescription information. Please review and correct it.",
            "technical_details": str(e),
            "recovery_suggestions": [
                "Please check all required fields are filled",
                "Ensure medicine names and dosages are correct",
                "Contact support if you need assistance"
            ]
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_details
        )
    
    except Exception as e:
        logger.error(f"Unexpected error creating draft order: {e}")
        # Generic error with user-friendly message
        error_details = {
            "error_type": "unexpected_error",
            "user_message": "An unexpected error occurred while processing your prescription. Our team has been notified.",
            # Error tracking ID will be handled by middleware
            "recovery_suggestions": [
                "Please try submitting your prescription again",
                "If the problem continues, contact our support team",
                "Include the error ID when contacting support for faster assistance"
            ]
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_details
        )

@router.post("/validate-prescription")
async def validate_prescription_only(prescription: PrescriptionRequest):
    """
    Validate prescription without creating draft order
    
    Returns validation results and product mapping information
    """
    try:
        # Validate prescription format
        validation_errors = shopify_client.validate_prescription(prescription)
        
        # Check product mappings
        medicine_names = [item.medicine for item in prescription.prescriptions]
        # Get product information for all medicines from Shopify API
        mapping_results = []
        for medicine_name in medicine_names:
            product_info = shopify_api.get_product_info(medicine_name)
            mapping_results.append(product_info)
        
        # Count available vs unavailable medicines
        available_count = sum(1 for result in mapping_results if result["is_available"])
        total_count = len(medicine_names)
        
        return {
            "validation_status": "valid" if not validation_errors else "invalid",
            "validation_errors": validation_errors,
            "product_mapping": mapping_results,
            "summary": {
                "total_medicines": total_count,
                "available_in_shopify": available_count,
                "unavailable_medicines": total_count - available_count,
                "can_create_draft_order": not validation_errors and available_count > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

@router.get("/products/search/{medicine_name}", response_model=ProductMappingInfo)
async def search_medicine_product(medicine_name: str):
    """
    Search for Shopify product mapping by medicine name
    
    Returns product information and alternatives if available
    """
    try:
        product_info = shopify_api.get_product_info(medicine_name)
        
        return ProductMappingInfo(
            medicine_name=product_info["medicine_name"],
            shopify_variant_id=product_info["shopify_variant_id"],
            shopify_product_title=product_info["shopify_product_title"],
            is_available=product_info["is_available"],
            suggested_alternatives=product_info["suggested_alternatives"]
        )
        
    except Exception as e:
        logger.error(f"Error searching medicine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/products/available")
async def get_available_medicines():
    """
    Get list of all medicines available in Shopify catalog
    
    Returns complete product catalog for frontend reference
    """
    try:
        medicines = shopify_api.format_medicine_catalog()
        
        return {
            "total_count": len(medicines),
            "medicines": medicines,
            "last_updated": "2024-09-04",  # In production, this would be dynamic
            "catalog_version": "1.0"
        }
        
    except Exception as e:
        logger.error(f"Error fetching available medicines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch medicines: {str(e)}"
        )

@router.get("/draft-order/{draft_order_id}")
async def get_draft_order_status(draft_order_id: int):
    """
    Get draft order status and details
    
    Useful for checking order status after creation
    """
    try:
        draft_order = shopify_client.get_draft_order(draft_order_id)
        
        if not draft_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Draft order {draft_order_id} not found"
            )
        
        return {
            "draft_order_id": draft_order["id"],
            "status": draft_order["status"],
            "invoice_url": draft_order.get("invoice_url"),
            "total_price": draft_order.get("total_price"),
            "line_items_count": len(draft_order.get("line_items", [])),
            "created_at": draft_order.get("created_at"),
            "updated_at": draft_order.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching draft order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch draft order: {str(e)}"
        )

@router.get("/health")
async def smart_auto_cart_health():
    """
    Health check for Smart Auto-Cart service
    
    Returns service status and configuration
    """
    try:
        # Check if Shopify is configured
        shopify_configured = not shopify_client.mock_mode
        
        # Check product mapping
        available_medicines_count = len(shopify_api.format_medicine_catalog())
        
        return {
            "service": "Smart Auto-Cart",
            "status": "healthy",
            "shopify_integration": "configured" if shopify_configured else "mock_mode",
            "product_catalog": {
                "available_medicines": available_medicines_count,
                "last_updated": "2024-09-04"
            },
            "features": [
                "Prescription validation",
                "Medicine to Shopify mapping",
                "Draft order creation",
                "Dosage instructions as properties",
                "External therapy notes"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"service": "Smart Auto-Cart", "status": "unhealthy", "error": str(e)}
        )

@router.get("/order-details/{draft_order_id}")
async def get_order_details_for_app(draft_order_id: int):
    """
    Get detailed order information for Flutter app display (fixed type mismatch)
    
    Returns prescription details, medicines, patient info, and payment link
    """
    try:
        # Get draft order from Shopify (fixed: now expects int consistently)
        draft_order = shopify_client.get_draft_order(draft_order_id)
        
        if not draft_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {draft_order_id} not found"
            )
        
        # Extract medicines and details from line items
        medicines = []
        total_amount = 0
        
        if 'line_items' in draft_order:
            for item in draft_order['line_items']:
                medicine_info = {
                    "name": item.get('title', 'Unknown Medicine'),
                    "quantity": item.get('quantity', 1),
                    "price": float(item.get('price', 0)),
                    "total_price": float(item.get('price', 0)) * item.get('quantity', 1),
                    "properties": {}
                }
                
                # Extract dosage instructions from properties
                if 'properties' in item:
                    for prop in item['properties']:
                        medicine_info['properties'][prop.get('name', '')] = prop.get('value', '')
                
                medicines.append(medicine_info)
                total_amount += medicine_info['total_price']
        
        # Extract prescription details from order notes
        order_notes = draft_order.get('note', '')
        
        # Parse prescription info from notes
        patient_name = ""
        doctor_name = ""
        diagnosis = ""
        
        # Simple parsing of order notes
        if "Patient:" in order_notes:
            patient_part = order_notes.split("Patient:")[1].split("|")[0].strip()
            if "," in patient_part:
                patient_name = patient_part.split(",")[0].strip()
        
        if "Doctor:" in order_notes:
            doctor_part = order_notes.split("Doctor:")[1].split("(")[0].strip()
            doctor_name = doctor_part
        
        if "PRESCRIPTION -" in order_notes:
            diagnosis = order_notes.split("PRESCRIPTION -")[1].split("|")[0].strip()
        
        # Construct response for Flutter app
        order_details = {
            "order_id": draft_order_id,
            "status": draft_order.get('status', 'open'),
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "diagnosis": diagnosis,
            "medicines": medicines,
            "total_amount": total_amount,
            "currency": "INR",
            "invoice_url": draft_order.get('invoice_url', ''),
            "created_at": draft_order.get('created_at', ''),
            "payment_status": "pending",
            "prescription_notes": order_notes
        }
        
        logger.info(f"Order details retrieved for Flutter app: {draft_order_id}")
        return order_details
        
    except Exception as e:
        logger.error(f"Error fetching order details for app {draft_order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order details: {str(e)}"
        )