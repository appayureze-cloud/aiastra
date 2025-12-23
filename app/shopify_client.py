"""
Shopify API Client for Draft Order Management
"""

import os
import logging
from typing import Dict, List, Optional
import requests
from requests.exceptions import RequestException

from .shopify_models import PrescriptionRequest, ShopifyLineItem, ShopifyDraftOrderResponse
from .enhanced_product_mapper import enhanced_product_mapper

# Enhanced Shopify Exception Classes
class ShopifyValidationError(Exception):
    """Enhanced Shopify validation error with field-level details"""
    def __init__(self, message: str, field_errors: List[Dict] = None, error_code: str = None):
        super().__init__(message)
        self.field_errors = field_errors or []
        self.error_code = error_code or "VALIDATION_FAILED"
        self.user_friendly_message = self._generate_user_friendly_message()
    
    def _generate_user_friendly_message(self) -> str:
        """Generate patient-friendly error message"""
        if not self.field_errors:
            return "Please check your prescription details and try again."
        
        error_count = len(self.field_errors)
        if error_count == 1:
            return f"There's an issue with your prescription: {self.field_errors[0].get('user_message', 'Please review and correct.')}"
        else:
            return f"There are {error_count} issues with your prescription that need to be corrected before we can process it."

class ShopifyRateLimitError(Exception):
    """Enhanced Shopify rate limit error with retry information"""
    def __init__(self, message: str, retry_after: int = 60, calls_remaining: int = 0):
        super().__init__(message)
        self.retry_after = retry_after
        self.calls_remaining = calls_remaining
        self.user_friendly_message = f"Our system is temporarily busy. Please try again in {retry_after} seconds."

class ShopifyAPIError(Exception):
    """Enhanced Shopify API error with structured details"""
    def __init__(self, message: str, status_code: int = None, shopify_errors: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.shopify_errors = shopify_errors or {}
        self.user_friendly_message = self._generate_user_friendly_message()
    
    def _generate_user_friendly_message(self) -> str:
        """Generate patient-friendly error message based on status code"""
        if self.status_code == 401:
            return "There's a temporary authentication issue. Please contact support."
        elif self.status_code == 403:
            return "This action is not permitted. Please contact support."
        elif self.status_code == 404:
            return "The requested item could not be found in our catalog."
        elif self.status_code == 422:
            return "The prescription contains invalid information. Please review and correct."
        elif self.status_code and self.status_code >= 500:
            return "Our pharmacy system is temporarily unavailable. Please try again in a few minutes."
        else:
            return "An unexpected error occurred. Please contact support if this continues."

logger = logging.getLogger(__name__)

class ShopifyClient:
    """Client for interacting with Shopify Admin API"""
    
    def __init__(self):
        self.shop_url = os.getenv("SHOPIFY_SHOP_URL")
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = "2024-07"
        self.sku_to_variant_map = {}  # Cache for SKU to variant ID mapping
        
        # Check if running in production environment
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        
        if not self.shop_url or not self.access_token:
            if self.is_production:
                # ✅ SECURITY: Fail in production if credentials missing
                error_msg = "Shopify credentials not configured in PRODUCTION. Set SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN."
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                # Development: warn and use mock mode
                logger.warning("Shopify credentials not configured. Running in MOCK MODE (development only).")
                self.mock_mode = True
        elif "admin.shopify.com" in self.shop_url or not self.shop_url.endswith(".myshopify.com"):
            if self.is_production:
                # ✅ SECURITY: Fail in production if URL is invalid
                error_msg = f"Invalid Shopify URL in PRODUCTION: '{self.shop_url}'. Expected: your-store.myshopify.com"
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                logger.warning(f"Invalid Shopify URL format. Running in MOCK MODE (development only).")
                self.mock_mode = True
        else:
            self.mock_mode = False
            # Clean up shop URL - remove protocol and ensure proper format
            clean_shop_url = self.shop_url.replace("https://", "").replace("http://", "")
            if not clean_shop_url.endswith(".myshopify.com"):
                clean_shop_url = f"{clean_shop_url}.myshopify.com"
            
            self.base_url = f"https://{clean_shop_url}/admin/api/{self.api_version}"
            self.headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token
            }
            
            # Initialize SKU to variant ID mapping
            if not self.mock_mode:
                self._initialize_variant_mapping()
    
    def validate_prescription(self, prescription: PrescriptionRequest) -> List[Dict]:
        """Enhanced prescription validation with user-friendly messages"""
        errors = []
        
        # Validate patient info with enhanced messaging
        if not prescription.patient.name.strip():
            errors.append({
                "field": "patient.name",
                "error": "Patient name is required",
                "user_message": "Please enter the patient's full name",
                "error_type": "required_field",
                "severity": "error"
            })
        
        if prescription.patient.age <= 0 or prescription.patient.age > 150:
            errors.append({
                "field": "patient.age",
                "error": "Invalid patient age",
                "user_message": f"Patient age should be between 1 and 150 years (entered: {prescription.patient.age})",
                "error_type": "invalid_value",
                "severity": "error"
            })
        
        # Validate patient contact if provided
        if hasattr(prescription.patient, 'contact') and prescription.patient.contact:
            contact = prescription.patient.contact.strip()
            if contact and not (contact.startswith('+') or contact.isdigit() or '@' in contact):
                errors.append({
                    "field": "patient.contact",
                    "error": "Invalid contact format",
                    "user_message": "Contact should be a valid phone number or email address",
                    "error_type": "invalid_format",
                    "severity": "warning"
                })
        
        # Validate prescriptions
        if not prescription.prescriptions:
            errors.append({
                "field": "prescriptions",
                "error": "At least one prescription is required",
                "user_message": "Please add at least one medicine to the prescription",
                "error_type": "required_field",
                "severity": "error"
            })
        
        # Enhanced prescription item validation
        for i, item in enumerate(prescription.prescriptions):
            if not item.medicine.strip():
                errors.append({
                    "field": "prescriptions.medicine",
                    "error": "Medicine name is required",
                    "user_message": f"Please enter the medicine name for item {i+1}",
                    "prescription_index": i,
                    "error_type": "required_field",
                    "severity": "error"
                })
            
            if not item.dose.strip():
                errors.append({
                    "field": "prescriptions.dose",
                    "error": "Dose is required",
                    "user_message": f"Please specify the dosage for {item.medicine or f'medicine {i+1}'}",
                    "prescription_index": i,
                    "error_type": "required_field",
                    "severity": "error"
                })
            
            if not item.schedule.strip():
                errors.append({
                    "field": "prescriptions.schedule",
                    "error": "Schedule is required",
                    "user_message": f"Please specify when to take {item.medicine or f'medicine {i+1}'} (e.g., '1-0-1', 'twice daily')",
                    "prescription_index": i,
                    "error_type": "required_field",
                    "severity": "error"
                })
            
            # Enhanced dose validation
            if item.dose and item.dose.strip():
                dose_lower = item.dose.lower().strip()
                if dose_lower not in ['external'] and not any(unit in dose_lower for unit in ['mg', 'g', 'ml', 'tablet', 'drop', 'spoon', 'tsp', 'tbsp']):
                    errors.append({
                        "field": "prescriptions.dose",
                        "error": "Dose format unclear",
                        "user_message": f"Please specify dose units for {item.medicine} (e.g., '5g', '2 tablets', '1 tsp')",
                        "prescription_index": i,
                        "error_type": "format_suggestion",
                        "severity": "warning"
                    })
        
        return errors
    
    def _initialize_variant_mapping(self):
        """Fetch all products and build SKU to numeric variant ID mapping using pagination"""
        try:
            logger.info("Fetching all product variants from Shopify (with pagination)...")
            url = f"{self.base_url}/products.json"
            params = {"fields": "id,variants", "limit": 250}
            
            total_products = 0
            while url:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params if not "page_info" in url else {},
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"Could not fetch products for variant mapping: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                products = data.get('products', [])
                total_products += len(products)
                logger.info(f"Fetched {len(products)} products (Total: {total_products})")
                
                for product in products:
                    for variant in product.get('variants', []):
                        sku = variant.get('sku')
                        variant_id = variant.get('id')
                        if sku and variant_id:
                            self.sku_to_variant_map[sku] = str(variant_id)
                
                # Check for next page
                url = self._extract_next_page_url(response)
                # After the first page, we don't need params because page_info in URL includes everything
                params = {}
            
            logger.info(f"Successfully loaded {len(self.sku_to_variant_map)} SKU to variant ID mappings from {total_products} products")
            
            # Log first few mappings for verification
            if self.sku_to_variant_map:
                sample_mappings = list(self.sku_to_variant_map.items())[:3]
                logger.info(f"Sample mappings: {sample_mappings}")
                
        except Exception as e:
            logger.error(f"Failed to initialize variant mapping: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _extract_next_page_url(self, response: requests.Response) -> Optional[str]:
        """Extract next page URL from Shopify Link header"""
        link_header = response.headers.get("Link")
        if not link_header:
            return None
            
        links = link_header.split(",")
        for link in links:
            if 'rel="next"' in link:
                return link.split(";")[0].strip("<> ")
        return None
    
    def get_variant_id_from_sku(self, sku: str) -> Optional[int]:
        """
        Get numeric variant ID from SKU (fixed Bug #11: type confusion)
        
        Args:
            sku: Product SKU
            
        Returns:
            Integer variant ID or None if not found
        """
        variant_str = self.sku_to_variant_map.get(sku)
        if variant_str:
            try:
                return int(variant_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid variant ID for SKU '{sku}': {variant_str} - {e}")
                return None
        return None
    
    def map_prescription_to_line_items(self, prescription: PrescriptionRequest) -> tuple[List[ShopifyLineItem], List[str]]:
        """Convert prescription items to Shopify line items"""
        line_items = []
        unmapped_medicines = []
        external_therapies = []
        
        for item in prescription.prescriptions:
            # Check if it's an external therapy (no variant ID needed)
            if item.dose.lower() == "external" or "external" in item.medicine.lower():
                external_therapies.append(f"{item.medicine} - {item.schedule} ({item.timing})")
                continue
            
            variant_id = enhanced_product_mapper.get_variant_id(item.medicine)
            
            if variant_id:
                # Create properties for dosage instructions
                properties = [
                    {"name": "Dose", "value": item.dose},
                    {"name": "Schedule", "value": item.schedule},
                    {"name": "Timing", "value": item.timing}
                ]
                
                if item.duration:
                    properties.append({"name": "Duration", "value": item.duration})
                
                if item.instructions:
                    properties.append({"name": "Instructions", "value": item.instructions})
                
                line_items.append(ShopifyLineItem(
                    variant_id=variant_id,
                    quantity=1,
                    properties=properties
                ))
            else:
                unmapped_medicines.append(item.medicine)
                logger.warning(f"No Shopify mapping found for medicine: {item.medicine}")
        
        # Add external therapies to prescription for notes
        if external_therapies:
            if prescription.external_therapies:
                prescription.external_therapies.extend(external_therapies)
            else:
                prescription.external_therapies = external_therapies
        
        return line_items, unmapped_medicines
    
    def create_draft_order_payload(self, prescription: PrescriptionRequest, line_items: List[ShopifyLineItem]) -> Dict:
        """Create enhanced Shopify draft order payload"""
        # Build comprehensive order notes
        notes = []
        
        # Prescription header
        notes.append(f"PRESCRIPTION - {prescription.diagnosis}")
        
        # Patient details
        patient_info = f"Patient: {prescription.patient.name}, Age: {prescription.patient.age}"
        if prescription.patient.sex:
            patient_info += f", {prescription.patient.sex}"
        if prescription.patient.patient_id:
            patient_info += f" (ID: {prescription.patient.patient_id})"
        if prescription.patient.op_ip_no:
            patient_info += f" (OP/IP: {prescription.patient.op_ip_no})"
        notes.append(patient_info)
        
        # Contact information
        if prescription.patient.contact:
            notes.append(f"Contact: {prescription.patient.contact}")
        
        # Prescription date and review
        if prescription.patient.date:
            notes.append(f"Date: {prescription.patient.date}")
        if prescription.patient.next_review:
            notes.append(f"Next Review: {prescription.patient.next_review}")
        
        # Doctor information
        if prescription.doctor:
            doctor_info = f"Doctor: {prescription.doctor.name} (Reg: {prescription.doctor.regn_no})"
            if prescription.doctor.contact:
                doctor_info += f" | Contact: {prescription.doctor.contact}"
            notes.append(doctor_info)
        
        # Investigations
        if prescription.investigations:
            notes.append(f"Investigations: {', '.join(prescription.investigations)}")
        
        # External therapies
        if prescription.external_therapies:
            notes.append(f"External Therapies: {' | '.join(prescription.external_therapies)}")
        
        # Doctor's notes
        if prescription.doctor_notes:
            notes.append(f"Notes: {prescription.doctor_notes}")
        
        # Company metadata
        if prescription.meta and prescription.meta.gst:
            notes.append(f"GST: {prescription.meta.gst}")
        
        # Convert line items to Shopify format (fixed: no double conversion)
        shopify_line_items = []
        for item in line_items:
            # Get numeric variant ID from SKU (already returns int)
            numeric_variant_id = self.get_variant_id_from_sku(item.variant_id)
            
            if numeric_variant_id:
                shopify_line_items.append({
                    "variant_id": numeric_variant_id,  # Already int, no conversion needed
                    "quantity": item.quantity,
                    "properties": item.properties
                })
            else:
                logger.warning(f"Could not find numeric variant ID for SKU: {item.variant_id}")
        
        # Build payload
        payload = {
            "draft_order": {
                "line_items": shopify_line_items,
                "note": " | ".join(notes),
                "tags": "Prescription,Smart-Auto-Cart,Ayurveda",
                "email": prescription.patient.email if prescription.patient.email else None
            }
        }
        
        # Add shipping address if contact available
        if prescription.patient.contact:
            name_parts = prescription.patient.name.split()
            payload["draft_order"]["shipping_address"] = {
                "first_name": name_parts[0] if name_parts else "",
                "last_name": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
                "phone": prescription.patient.contact
            }
        
        return payload
    
    def create_draft_order(self, prescription: PrescriptionRequest) -> ShopifyDraftOrderResponse:
        """Enhanced draft order creation with comprehensive error handling"""
        # Enhanced validation with user-friendly error handling
        validation_errors = self.validate_prescription(prescription)
        if validation_errors:
            raise ShopifyValidationError(
                message="Prescription validation failed",
                field_errors=validation_errors,
                error_code="PRESCRIPTION_VALIDATION_FAILED"
            )
        
        # Map prescription to line items with enhanced error details
        line_items, unmapped_medicines = self.map_prescription_to_line_items(prescription)
        
        if not line_items:
            medicine_names = [item.medicine for item in prescription.prescriptions]
            raise ShopifyValidationError(
                message="No medicines could be mapped to Shopify products",
                field_errors=[{
                    "field": "prescriptions",
                    "error": "No available products found",
                    "user_message": f"None of the prescribed medicines ({', '.join(medicine_names[:3])}{'...' if len(medicine_names) > 3 else ''}) are currently available in our online pharmacy. Please contact us for alternative options.",
                    "error_type": "product_unavailable",
                    "severity": "error",
                    "unmapped_medicines": medicine_names
                }],
                error_code="ALL_PRODUCTS_UNAVAILABLE"
            )
        
        # Create draft order payload
        payload = self.create_draft_order_payload(prescription, line_items)
        
        if self.mock_mode:
            # Return mock response for testing
            return self._create_mock_draft_order(prescription, line_items, unmapped_medicines)
        
        try:
            # Log the payload for debugging
            logger.info(f"Creating draft order with payload: {payload}")
            
            # Make API call to Shopify with enhanced error handling
            response = requests.post(
                f"{self.base_url}/draft_orders.json",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Enhanced error handling based on status codes
            if response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                calls_remaining = int(response.headers.get('X-Shopify-Shop-Api-Call-Limit', '0/40').split('/')[0])
                raise ShopifyRateLimitError(
                    message=f"Shopify API rate limit exceeded. Retry after {retry_after} seconds.",
                    retry_after=retry_after,
                    calls_remaining=calls_remaining
                )
            
            elif response.status_code == 422:
                # Validation error from Shopify
                try:
                    error_data = response.json()
                    shopify_errors = error_data.get('errors', {})
                    raise ShopifyAPIError(
                        message="Shopify validation failed",
                        status_code=422,
                        shopify_errors=shopify_errors
                    )
                except (ValueError, KeyError):
                    raise ShopifyAPIError(
                        message="Shopify validation failed",
                        status_code=422
                    )
            
            elif response.status_code != 201:
                # Other API errors
                logger.error(f"Shopify API response ({response.status_code}): {response.text}")
                raise ShopifyAPIError(
                    message=f"Shopify API error: {response.status_code}",
                    status_code=response.status_code
                )
            
            # Success - parse response
            try:
                draft_order_data = response.json()["draft_order"]
            except (ValueError, KeyError) as e:
                raise ShopifyAPIError(
                    message="Invalid response format from Shopify",
                    status_code=response.status_code
                )
            
            return ShopifyDraftOrderResponse(
                draft_order_id=str(draft_order_data["id"]),
                invoice_url=draft_order_data["invoice_url"],
                status=draft_order_data["status"],
                total_price=draft_order_data.get("total_price"),
                line_items_count=len(draft_order_data["line_items"]),
                unmapped_medicines=unmapped_medicines if unmapped_medicines else None
            )
            
        except (ShopifyValidationError, ShopifyRateLimitError, ShopifyAPIError):
            # Re-raise our custom exceptions
            raise
        except requests.exceptions.Timeout:
            raise ShopifyAPIError(
                message="Request to Shopify timed out",
                status_code=408
            )
        except requests.exceptions.ConnectionError:
            raise ShopifyAPIError(
                message="Could not connect to Shopify",
                status_code=503
            )
        except RequestException as e:
            logger.error(f"Shopify API error: {e}")
            raise ShopifyAPIError(
                message=f"Shopify API communication error: {str(e)}",
                status_code=500
            )
    
    def _create_mock_draft_order(self, prescription: PrescriptionRequest, 
                               line_items: List[ShopifyLineItem], 
                               unmapped_medicines: List[str]) -> ShopifyDraftOrderResponse:
        """Create mock draft order response for testing"""
        import random
        
        mock_draft_order_id = random.randint(7891000, 7891999)
        mock_shop_domain = self.shop_url or "your-ayurveda-shop.myshopify.com"
        
        return ShopifyDraftOrderResponse(
            draft_order_id=str(mock_draft_order_id),
            invoice_url=f"https://{mock_shop_domain}/draft_orders/{mock_draft_order_id}/invoice",
            status="open",
            total_price="₹1,247.00",
            line_items_count=len(line_items),
            unmapped_medicines=unmapped_medicines if unmapped_medicines else None
        )
    
    def get_draft_order(self, draft_order_id: int) -> Optional[Dict]:
        """Get draft order details by ID"""
        if self.mock_mode:
            return {
                "id": draft_order_id,
                "status": "open",
                "invoice_url": f"https://your-ayurveda-shop.myshopify.com/draft_orders/{draft_order_id}/invoice"
            }
        
        try:
            response = requests.get(
                f"{self.base_url}/draft_orders/{draft_order_id}.json",
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()["draft_order"]
            
        except RequestException as e:
            logger.error(f"Error fetching draft order {draft_order_id}: {e}")
            return None

# Global Shopify client instance
shopify_client = ShopifyClient()