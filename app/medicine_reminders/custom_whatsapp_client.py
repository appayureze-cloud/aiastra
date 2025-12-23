"""
Custom WhatsApp API Client
Integrates with your own WhatsApp server API
API Documentation: https://documenter.getpostman.com/view/17404097/2sA35D4hpx
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomWhatsAppClient:
    """Custom WhatsApp client for your own WhatsApp server API"""
    
    def __init__(self):
        # Load credentials from environment
        self.api_base_url = os.getenv("CUSTOM_WA_API_BASE_URL")
        self.bearer_token = os.getenv("CUSTOM_WA_BEARER_TOKEN")
        self.vendor_uid = os.getenv("CUSTOM_WA_VENDOR_UID")
        self.from_phone_number_id = os.getenv("CUSTOM_WA_FROM_PHONE_ID", "")  # Optional
        
        if not all([self.api_base_url, self.bearer_token, self.vendor_uid]):
            logger.error("Custom WhatsApp API credentials missing")
            raise ValueError(
                "Required: CUSTOM_WA_API_BASE_URL, CUSTOM_WA_BEARER_TOKEN, CUSTOM_WA_VENDOR_UID"
            )
        
        # Setup headers with Bearer token
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        logger.info("✅ Custom WhatsApp client initialized successfully")
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number to clean international format"""
        clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        
        # Add India country code if missing
        if not clean.startswith("91"):
            if len(clean) == 10:
                clean = "91" + clean
        
        return clean
    
    async def send_text_message(
        self,
        phone_number: str,
        message_body: str,
        contact_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send text message via custom WhatsApp API
        
        Args:
            phone_number: Recipient phone number (e.g., "919876543210")
            message_body: Text message to send
            contact_info: Optional contact details (first_name, last_name, email, etc.)
        
        Returns:
            Response from API or None if failed
        """
        try:
            phone_number = self._format_phone(phone_number)
            
            # Construct URL with vendor UID and token
            url = f"{self.api_base_url}/{self.vendor_uid}/contact/send-message?token={self.bearer_token}"
            
            payload: Dict[str, Any] = {
                "phone_number": phone_number,
                "message_body": message_body
            }
            
            if self.from_phone_number_id:
                payload["from_phone_number_id"] = self.from_phone_number_id
            
            # Add optional contact creation
            if contact_info:
                payload["contact"] = contact_info
            
            # Don't use Authorization header since token is in URL
            headers = {"Content-Type": "application/json"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json() if response.text else {"success": True}
                
                logger.info(f"✅ Text message sent to {phone_number}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send message: {str(e)}")
            return None
    
    async def send_media_message(
        self,
        phone_number: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None,
        file_name: Optional[str] = None,
        contact_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send media message (image, video, document)
        
        Args:
            phone_number: Recipient phone number
            media_type: Type of media ("image", "video", "document")
            media_url: Public URL of the media file
            caption: Optional caption for image/video
            file_name: Optional file name for documents
            contact_info: Optional contact details
        
        Returns:
            Response from API or None if failed
        """
        try:
            phone_number = self._format_phone(phone_number)
            
            payload: Dict[str, Any] = {
                "phone_number": phone_number,
                "media_type": media_type,
                "media_url": media_url
            }
            
            if self.from_phone_number_id:
                payload["from_phone_number_id"] = self.from_phone_number_id
            
            if caption:
                payload["caption"] = caption
            
            if file_name:
                payload["file_name"] = file_name
            
            if contact_info:
                payload["contact"] = contact_info
            
            url = f"{self.api_base_url}/{self.vendor_uid}/contact/send-media-message?token={self.bearer_token}"
            headers = {"Content-Type": "application/json"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json() if response.text else {"success": True}
                
                logger.info(f"✅ Media message ({media_type}) sent to {phone_number}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send media: {str(e)}")
            return None
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        template_language: str = "en",
        template_fields: Optional[Dict[str, str]] = None,
        contact_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send WhatsApp template message (for approved templates)
        
        Args:
            phone_number: Recipient phone number
            template_name: Name of approved template
            template_language: Template language code (default: "en")
            template_fields: Template field values (field_1, field_2, etc.)
            contact_info: Optional contact details
        
        Returns:
            Response from API or None if failed
        """
        try:
            phone_number = self._format_phone(phone_number)
            
            payload: Dict[str, Any] = {
                "phone_number": phone_number,
                "template_name": template_name,
                "template_language": template_language
            }
            
            if self.from_phone_number_id:
                payload["from_phone_number_id"] = self.from_phone_number_id
            
            # Add template fields
            if template_fields:
                payload.update(template_fields)
            
            if contact_info:
                payload["contact"] = contact_info
            
            url = f"{self.api_base_url}/{self.vendor_uid}/contact/send-template-message"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json() if response.text else {"success": True}
                
                logger.info(f"✅ Template message sent to {phone_number}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send template: {str(e)}")
            return None
    
    async def send_interactive_message(
        self,
        phone_number: str,
        interactive_type: str,
        header_text: str,
        body_text: str,
        footer_text: Optional[str] = None,
        buttons: Optional[Dict[str, str]] = None,
        list_data: Optional[Dict[str, Any]] = None,
        contact_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send interactive message with buttons or lists
        
        Args:
            phone_number: Recipient phone number
            interactive_type: Type ("button", "list", "cta_url")
            header_text: Header text
            body_text: Main message body
            footer_text: Optional footer text
            buttons: Button data (for "button" type) {"1": "Button 1", "2": "Button 2"}
            list_data: List data (for "list" type)
            contact_info: Optional contact details
        
        Returns:
            Response from API or None if failed
        """
        try:
            phone_number = self._format_phone(phone_number)
            
            payload: Dict[str, Any] = {
                "phone_number": phone_number,
                "interactive_type": interactive_type,
                "header_type": "text",
                "header_text": header_text,
                "body_text": body_text
            }
            
            if self.from_phone_number_id:
                payload["from_phone_number_id"] = self.from_phone_number_id
            
            if footer_text:
                payload["footer_text"] = footer_text
            
            if buttons and interactive_type == "button":
                payload["buttons"] = buttons
            
            if list_data and interactive_type == "list":
                payload["list_data"] = list_data
            
            if contact_info:
                payload["contact"] = contact_info
            
            url = f"{self.api_base_url}/{self.vendor_uid}/contact/send-interactive-message"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json() if response.text else {"success": True}
                
                logger.info(f"✅ Interactive message sent to {phone_number}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send interactive message: {str(e)}")
            return None
    
    # ==================== High-Level Feature Methods ====================
    
    async def send_medicine_reminder(
        self,
        patient_phone: str,
        patient_name: str,
        medicine_name: str,
        dose_amount: str,
        dose_time: str,
        instructions: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send medicine reminder with interactive buttons
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            medicine_name: Name of medicine
            dose_amount: Dosage (e.g., "2 tablets")
            dose_time: Time to take medicine
            instructions: Optional additional instructions
        
        Returns:
            API response or None
        """
        header_text = "⏰ Medicine Reminder"
        
        body_text = f"""Hello {patient_name}! 🌿

It's time for your medicine:

💊 *{medicine_name}*
📋 Dosage: {dose_amount}
🕐 Time: {dose_time}"""
        
        if instructions:
            body_text += f"\n\n📝 Instructions: {instructions}"
        
        footer_text = "Reply to confirm you've taken your medicine"
        
        buttons = {
            "1": "✅ TAKEN",
            "2": "⏰ LATER",
            "3": "❌ SKIP"
        }
        
        contact_info = {
            "first_name": patient_name.split()[0] if patient_name else "Patient",
            "country": "india",
            "language_code": "en"
        }
        
        return await self.send_interactive_message(
            phone_number=patient_phone,
            interactive_type="button",
            header_text=header_text,
            body_text=body_text,
            footer_text=footer_text,
            buttons=buttons,
            contact_info=contact_info
        )
    
    async def send_order_confirmation(
        self,
        customer_phone: str,
        customer_name: str,
        order_number: str,
        order_total: str,
        items: List[str],
        tracking_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send Shopify order confirmation
        
        Args:
            customer_phone: Customer's phone number
            customer_name: Customer's name
            order_number: Order ID
            order_total: Total amount
            items: List of item names
            tracking_url: Optional tracking URL
        
        Returns:
            API response or None
        """
        items_text = "\n".join([f"• {item}" for item in items])
        
        message_body = f"""🎉 *Order Confirmed!*

Hello {customer_name},

Thank you for your order from AyurEze Healthcare!

📦 *Order #{order_number}*
💰 Total: ₹{order_total}

*Items Ordered:*
{items_text}

Your medicines are being prepared and will ship soon! 📬"""
        
        if tracking_url:
            message_body += f"\n\n🔗 Track your order: {tracking_url}"
        
        message_body += "\n\n_AyurEze Healthcare Team_ 🌿"
        
        contact_info = {
            "first_name": customer_name.split()[0] if customer_name else "Customer",
            "country": "india",
            "language_code": "en"
        }
        
        return await self.send_text_message(
            phone_number=customer_phone,
            message_body=message_body,
            contact_info=contact_info
        )
    
    async def send_ai_response(
        self,
        patient_phone: str,
        patient_name: str,
        ai_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Send AI response as a friendly Ayurveda expert - conversational, not formal
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            ai_message: AI-generated response
        
        Returns:
            API response or None
        """
        # Send response like a friendly expert, not a formal bot
        # Just the natural AI response with a leaf emoji - no labels or signatures
        message_body = f"🌿 {ai_message.strip()}"
        
        # Add a friendly closing only if AI didn't include one naturally
        if not any(phrase in ai_message.lower() for phrase in ['let me know', 'feel free', 'hope this', 'take care', 'any questions']):
            message_body += "\n\n_Feel free to ask anything!_ 😊"
        
        contact_info = {
            "first_name": patient_name.split()[0] if patient_name else "Patient",
            "country": "india",
            "language_code": "en",
            "enable_ai_bot": True
        }
        
        return await self.send_text_message(
            phone_number=patient_phone,
            message_body=message_body,
            contact_info=contact_info
        )
    
    async def send_document_link(
        self,
        patient_phone: str,
        patient_name: str,
        document_type: str,
        document_url: str,
        expiry_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Send Storj document sharing link
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            document_type: Type of document (prescription, lab_report, etc.)
            document_url: Secure Storj URL
            expiry_hours: Link expiry in hours
        
        Returns:
            API response or None
        """
        doc_emoji = {
            "prescription": "💊",
            "lab_report": "🔬",
            "xray": "🩻",
            "mri": "🏥",
            "ct_scan": "📊"
        }.get(document_type, "📄")
        
        message_body = f"""🌿 *AyurEze Healthcare - Your Document*

Hello {patient_name}! 👋

Your {document_type.replace('_', ' ').title()} is ready.

{doc_emoji} *Document:* {document_type.replace('_', ' ').title()}
📅 *Date:* {datetime.now().strftime('%B %d, %Y')}

🔗 *View Document:*
{document_url}

⏰ *Link expires in {expiry_hours} hours*
🔒 *Secure & encrypted*

Questions? Reply to this message!

_AyurEze Healthcare Team_ 🌿"""
        
        contact_info = {
            "first_name": patient_name.split()[0] if patient_name else "Patient",
            "country": "india",
            "language_code": "en"
        }
        
        return await self.send_text_message(
            phone_number=patient_phone,
            message_body=message_body,
            contact_info=contact_info
        )
    
    async def create_or_update_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        language_code: str = "en",
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create or update contact in WhatsApp system
        
        Args:
            phone_number: Contact's phone number
            first_name: First name
            last_name: Last name (optional)
            email: Email address (optional)
            language_code: Language preference
            custom_fields: Additional custom fields
        
        Returns:
            API response or None
        """
        try:
            phone_number = self._format_phone(phone_number)
            
            payload: Dict[str, Any] = {
                "phone_number": phone_number,
                "first_name": first_name,
                "country": "india",
                "language_code": language_code
            }
            
            if last_name:
                payload["last_name"] = last_name
            
            if email:
                payload["email"] = email
            
            if custom_fields:
                payload["custom_fields"] = custom_fields
            
            url = f"{self.api_base_url}/{self.vendor_uid}/contact/create"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json() if response.text else {"success": True}
                
                logger.info(f"✅ Contact created/updated: {phone_number}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to create/update contact: {str(e)}")
            return None
