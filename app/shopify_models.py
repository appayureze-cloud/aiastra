"""
Shopify Smart Auto-Cart Models for Prescription to Draft Order Pipeline
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class PatientInfo(BaseModel):
    """Enhanced patient information model"""
    name: str = Field(..., description="Patient's full name")
    age: int = Field(..., description="Patient's age")
    sex: Optional[str] = Field(None, description="Patient's gender")
    op_ip_no: Optional[str] = Field(None, description="OP/IP registration number")
    patient_id: Optional[str] = Field(None, description="Unique patient identifier")
    contact: Optional[str] = Field(None, description="Patient's contact number")
    date: Optional[str] = Field(None, description="Prescription date")
    next_review: Optional[str] = Field(None, description="Next review date")
    email: Optional[str] = Field(None, description="Patient's email address")
    
    # Backward compatibility aliases
    @property
    def phone(self) -> Optional[str]:
        return self.contact

class PrescriptionItem(BaseModel):
    """Individual prescription item model"""
    medicine: str = Field(..., description="Medicine name")
    dose: str = Field(..., description="Dosage amount (e.g., '5 g', '2 tablets')")
    schedule: str = Field(..., description="Dosing schedule (e.g., '1-0-1', 'twice daily')")
    timing: str = Field(..., description="When to take (e.g., 'After Food', 'Before Sleep')")
    duration: Optional[str] = Field(None, description="Treatment duration (e.g., '15 days', '1 month')")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    quantity: int = Field(1, description="Number of units for the medicine")

class DoctorInfo(BaseModel):
    """Doctor information model"""
    name: str = Field(..., description="Doctor's full name")
    regn_no: str = Field(..., description="Doctor's registration number")
    contact: Optional[str] = Field(None, description="Doctor's contact number")

class CompanyMeta(BaseModel):
    """Company metadata model"""
    gst: Optional[str] = Field(None, description="GST number")
    reg_office: Optional[str] = Field(None, description="Registered office address")

class PrescriptionRequest(BaseModel):
    """Enhanced prescription request model"""
    patient: PatientInfo = Field(..., description="Patient information")
    diagnosis: str = Field(..., description="Medical diagnosis")
    investigations: Optional[List[str]] = Field(None, description="List of investigations/tests")
    prescriptions: List[PrescriptionItem] = Field(..., description="List of prescribed medicines and therapies")
    doctor: Optional[DoctorInfo] = Field(None, description="Doctor information")
    meta: Optional[CompanyMeta] = Field(None, description="Company metadata")
    external_therapies: Optional[List[str]] = Field(None, description="External therapies (backward compatibility)")
    doctor_notes: Optional[str] = Field(None, description="Additional doctor notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient": {
                    "name": "Ramesh Kumar",
                    "age": 42,
                    "sex": "Male",
                    "op_ip_no": "OP12345",
                    "patient_id": "P98765",
                    "contact": "+91-9876543210",
                    "date": "2025-09-03",
                    "next_review": "2025-09-17"
                },
                "diagnosis": "Sandhigatavata (Osteoarthritis)",
                "investigations": ["X-Ray Knee", "Blood Sugar"],
                "prescriptions": [
                    {
                        "medicine": "Ashwagandha Churna",
                        "dose": "5 g",
                        "schedule": "1-0-1",
                        "timing": "After Food"
                    },
                    {
                        "medicine": "Triphala Tablet",
                        "dose": "2 tablets",
                        "schedule": "0-1-0",
                        "timing": "Before Food"
                    },
                    {
                        "medicine": "Abhyanga with Mahanarayana Taila",
                        "dose": "External",
                        "schedule": "Daily",
                        "timing": "Before Bath"
                    }
                ],
                "doctor": {
                    "name": "Dr. Anil Sharma",
                    "regn_no": "TN123456",
                    "contact": "+91-9876543211"
                },
                "meta": {
                    "gst": "33ABACA2891B1Z6",
                    "reg_office": "Ayurease Healthcare Pvt Ltd, 157E/4, Main Road, Kovilpatti, Tamilnadu"
                }
            }
        }

class ShopifyLineItem(BaseModel):
    """Shopify line item model"""
    variant_id: str = Field(..., description="Shopify product variant ID or SKU")
    quantity: int = Field(1, description="Quantity of the item")
    properties: List[Dict[str, str]] = Field(..., description="Custom properties for dosage info")

class ShopifyDraftOrderResponse(BaseModel):
    """Response model for Shopify draft order creation"""
    draft_order_id: str = Field(..., description="Shopify draft order ID")
    invoice_url: str = Field(..., description="Invoice URL for patient checkout")
    status: str = Field(..., description="Draft order status")
    total_price: Optional[str] = Field(None, description="Total order amount")
    line_items_count: int = Field(..., description="Number of items in the order")
    unmapped_medicines: Optional[List[str]] = Field(None, description="Medicines not found in product mapping")
    
    # Enhanced Smart Auto-Cart fields
    prescription_id: Optional[str] = Field(None, description="Database prescription ID if saved")
    notification_sent: bool = Field(False, description="Whether push notification was sent to patient")
    patient_verified: bool = Field(False, description="Whether patient record was found and verified")
    
class ProductMappingInfo(BaseModel):
    """Product mapping information model"""
    medicine_name: str = Field(..., description="Medicine name as prescribed")
    shopify_variant_id: Optional[str] = Field(None, description="Mapped Shopify variant ID or SKU")
    shopify_product_title: Optional[str] = Field(None, description="Shopify product title")
    is_available: bool = Field(..., description="Whether product is available in Shopify")
    suggested_alternatives: Optional[List[str]] = Field(None, description="Alternative products if not available")

class ValidationError(BaseModel):
    """Prescription validation error model"""
    field: str = Field(..., description="Field that failed validation")
    error: str = Field(..., description="Error message")
    prescription_index: Optional[int] = Field(None, description="Index of prescription item if applicable")