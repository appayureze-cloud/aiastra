"""
Order Management API for Smart Auto-Cart System
Handles prescription storage, order tracking, and status updates
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import json

from .database_models import (
    get_db_dependency, 
    PrescriptionRecord,
    PrescribedMedicine,
    OrderStatusHistory,
    create_prescription_record,
    update_prescription_status,
    get_patient_prescriptions
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Order Management"])

# Pydantic models for API requests/responses

class PrescriptionCreateRequest(BaseModel):
    patient_id: str
    doctor_id: str
    consultation_id: Optional[str] = None
    diagnosis: str
    notes: Optional[str] = None
    medicines: List[Dict[str, Any]]

class StatusUpdateRequest(BaseModel):
    prescription_id: str
    new_status: str
    change_reason: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = {}

class OrderHistoryResponse(BaseModel):
    prescription_id: str
    diagnosis: str
    status: str
    payment_status: str
    total_amount: Optional[str]
    prescribed_at: str
    medicines: List[Dict[str, Any]]
    status_history: List[Dict[str, Any]]

@router.post("/prescription/save")
async def save_prescription_record(
    prescription_data: PrescriptionCreateRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Save complete prescription record with medicines
    Called after successful draft order creation
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        # Convert Pydantic model to dict for database function
        prescription_dict = {
            "patient_id": prescription_data.patient_id,
            "doctor_id": prescription_data.doctor_id,
            "consultation_id": prescription_data.consultation_id,
            "diagnosis": prescription_data.diagnosis,
            "notes": prescription_data.notes,
            "medicines": prescription_data.medicines
        }
        
        # Create prescription record
        prescription = create_prescription_record(db, prescription_dict)
        
        logger.info(f"Prescription saved: {prescription.prescription_id}")
        
        return {
            "success": True,
            "prescription_id": prescription.prescription_id,
            "status": prescription.status,
            "message": "Prescription saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save prescription: {str(e)}"
        )

@router.patch("/prescription/status")
async def update_order_status(
    status_update: StatusUpdateRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Update prescription/order status
    Used by webhooks and manual status updates
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        success = update_prescription_status(
            db=db,
            prescription_id=status_update.prescription_id,
            new_status=status_update.new_status,
            changed_by="api_call",
            change_reason=status_update.change_reason,
            additional_data=status_update.additional_data
        )
        
        if success:
            logger.info(f"Status updated: {status_update.prescription_id} -> {status_update.new_status}")
            return {
                "success": True,
                "prescription_id": status_update.prescription_id,
                "new_status": status_update.new_status,
                "message": "Status updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription {status_update.prescription_id} not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )

@router.get("/patient/{patient_id}")
async def get_patient_order_history(
    patient_id: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get complete order history for a patient
    Includes prescriptions, medicines, and status tracking
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        prescriptions = get_patient_prescriptions(db, patient_id)
        
        return {
            "patient_id": patient_id,
            "total_prescriptions": len(prescriptions),
            "prescriptions": prescriptions
        }
        
    except Exception as e:
        logger.error(f"Failed to get patient order history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order history: {str(e)}"
        )

@router.get("/prescription/{prescription_id}")
async def get_prescription_details(
    prescription_id: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get detailed prescription information including status history
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.prescription_id == prescription_id
        ).first()
        
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription {prescription_id} not found"
            )
        
        # Get medicines
        medicines = db.query(PrescribedMedicine).filter(
            PrescribedMedicine.prescription_id == prescription_id
        ).all()
        
        # Get status history
        status_history = db.query(OrderStatusHistory).filter(
            OrderStatusHistory.prescription_id == prescription_id
        ).order_by(OrderStatusHistory.created_at.desc()).all()
        
        return {
            "prescription_id": prescription.prescription_id,
            "patient_id": prescription.patient_id,
            "doctor_id": prescription.doctor_id,
            "consultation_id": prescription.consultation_id,
            "diagnosis": prescription.diagnosis,
            "notes": prescription.notes,
            "status": prescription.status,
            "payment_status": prescription.payment_status,
            "draft_order_id": prescription.draft_order_id,
            "invoice_url": prescription.invoice_url,
            "total_amount": prescription.total_amount,
            "prescribed_at": prescription.prescribed_at.isoformat(),
            "notified_at": prescription.notified_at.isoformat() if prescription.notified_at else None,
            "paid_at": prescription.paid_at.isoformat() if prescription.paid_at else None,
            "medicines": [{
                "medicine_name": med.medicine_name,
                "shopify_variant_id": med.shopify_variant_id,
                "dose": med.dose,
                "schedule": med.schedule,
                "timing": med.timing,
                "duration": med.duration,
                "instructions": med.instructions,
                "quantity": med.quantity,
                "unit_price": med.unit_price,
                "total_price": med.total_price,
                "is_available": med.is_available
            } for med in medicines],
            "status_history": [{
                "previous_status": history.previous_status,
                "new_status": history.new_status,
                "changed_by": history.changed_by,
                "change_reason": history.change_reason,
                "changed_at": history.created_at.isoformat(),
                "tracking_number": history.tracking_number,
                "tracking_url": history.tracking_url
            } for history in status_history]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prescription details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prescription details: {str(e)}"
        )

@router.post("/shopify/webhook")
async def handle_shopify_webhook(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    """
    Handle Shopify webhook notifications for order status updates
    Automatically updates prescription status based on Shopify events
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        # Get webhook data
        webhook_data = await request.json()
        webhook_topic = request.headers.get("X-Shopify-Topic", "")
        
        logger.info(f"Received Shopify webhook: {webhook_topic}")
        
        # Handle different webhook types
        if webhook_topic == "orders/paid":
            await _handle_order_paid(db, webhook_data)
        elif webhook_topic == "orders/fulfilled":
            await _handle_order_shipped(db, webhook_data)
        elif webhook_topic == "orders/cancelled":
            await _handle_order_cancelled(db, webhook_data)
        elif webhook_topic == "draft_orders/completed":
            await _handle_draft_order_completed(db, webhook_data)
        
        return {"success": True, "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Failed to process Shopify webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

async def _handle_order_paid(db: Session, order_data: Dict[str, Any]):
    """Handle order paid webhook"""
    try:
        order_id = str(order_data.get("id"))
        
        # Find prescription by draft order ID (if it was a draft order originally)
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.draft_order_id == order_id
        ).first()
        
        if prescription:
            update_prescription_status(
                db=db,
                prescription_id=prescription.prescription_id,
                new_status="paid",
                changed_by="shopify_webhook",
                change_reason="Payment completed in Shopify",
                additional_data={"shopify_order_id": order_id}
            )
            logger.info(f"Order paid: {prescription.prescription_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle order paid webhook: {e}")

async def _handle_order_shipped(db: Session, order_data: Dict[str, Any]):
    """Handle order fulfilled/shipped webhook"""
    try:
        order_id = str(order_data.get("id"))
        
        # Get tracking information
        fulfillments = order_data.get("fulfillments", [])
        tracking_number = None
        tracking_url = None
        
        if fulfillments:
            fulfillment = fulfillments[0]
            tracking_number = fulfillment.get("tracking_number")
            tracking_urls = fulfillment.get("tracking_urls", [])
            tracking_url = tracking_urls[0] if tracking_urls else None
        
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.draft_order_id == order_id
        ).first()
        
        if prescription:
            update_prescription_status(
                db=db,
                prescription_id=prescription.prescription_id,
                new_status="shipped",
                changed_by="shopify_webhook",
                change_reason="Order fulfilled and shipped",
                additional_data={
                    "shopify_order_id": order_id,
                    "tracking_number": tracking_number,
                    "tracking_url": tracking_url
                }
            )
            logger.info(f"Order shipped: {prescription.prescription_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle order shipped webhook: {e}")

async def _handle_order_cancelled(db: Session, order_data: Dict[str, Any]):
    """Handle order cancelled webhook"""
    try:
        order_id = str(order_data.get("id"))
        cancel_reason = order_data.get("cancel_reason", "Unknown")
        
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.draft_order_id == order_id
        ).first()
        
        if prescription:
            update_prescription_status(
                db=db,
                prescription_id=prescription.prescription_id,
                new_status="cancelled",
                changed_by="shopify_webhook",
                change_reason=f"Order cancelled: {cancel_reason}",
                additional_data={"shopify_order_id": order_id}
            )
            logger.info(f"Order cancelled: {prescription.prescription_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle order cancelled webhook: {e}")

async def _handle_draft_order_completed(db: Session, draft_order_data: Dict[str, Any]):
    """Handle draft order completed (converted to real order) webhook"""
    try:
        draft_order_id = str(draft_order_data.get("id"))
        order_id = draft_order_data.get("order_id")
        
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.draft_order_id == draft_order_id
        ).first()
        
        if prescription:
            update_prescription_status(
                db=db,
                prescription_id=prescription.prescription_id,
                new_status="paid",
                changed_by="shopify_webhook",
                change_reason="Draft order converted to real order",
                additional_data={"shopify_order_id": str(order_id) if order_id else None}
            )
            logger.info(f"Draft order completed: {prescription.prescription_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle draft order completed webhook: {e}")

@router.get("/status/{status}")
async def get_orders_by_status(
    status: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get all orders with specific status
    Useful for admin monitoring and bulk operations
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        prescriptions = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.status == status
        ).order_by(PrescriptionRecord.created_at.desc()).all()
        
        result = []
        for prescription in prescriptions:
            result.append({
                "prescription_id": prescription.prescription_id,
                "patient_id": prescription.patient_id,
                "doctor_id": prescription.doctor_id,
                "diagnosis": prescription.diagnosis,
                "status": prescription.status,
                "payment_status": prescription.payment_status,
                "total_amount": prescription.total_amount,
                "prescribed_at": prescription.prescribed_at.isoformat(),
                "updated_at": prescription.updated_at.isoformat()
            })
        
        return {
            "status": status,
            "total_count": len(result),
            "prescriptions": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get orders by status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )

@router.get("/health")
async def order_management_health():
    """Health check for order management service"""
    return {
        "service": "Order Management",
        "status": "healthy",
        "features": [
            "Prescription storage and tracking",
            "Order status management",
            "Shopify webhook integration",
            "Patient order history",
            "Real-time status updates"
        ]
    }