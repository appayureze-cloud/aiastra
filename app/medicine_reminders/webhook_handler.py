"""
Custom WhatsApp API Webhook Handler
Receives incoming messages from your custom WhatsApp server
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post("/custom-whatsapp")
async def handle_custom_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming WhatsApp messages from custom API
    
    This webhook receives messages when patients reply to:
    - Medicine reminders (TAKEN, SKIP, LATER)
    - AI agent queries
    - General messages
    """
    try:
        webhook_data = await request.json()
        logger.info(f"📥 Received custom WhatsApp webhook: {webhook_data}")
        
        # Process the webhook in background to respond quickly
        background_tasks.add_task(process_incoming_message, webhook_data)
        
        return {
            "success": True,
            "message": "Webhook received"
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_incoming_message(webhook_data: Dict[str, Any]):
    """
    Process incoming WhatsApp message based on type and content
    
    Webhook format from whatsapp.ayureze.in:
    {
        "contact": {
            "phone_number": "...",
            "first_name": "...",
            ...
        },
        "message": {
            "is_new_message": true,
            "body": "message text",
            "media": {...}
        }
    }
    """
    try:
        # Extract message details from ayureze webhook format
        contact = webhook_data.get("contact", {})
        message = webhook_data.get("message", {})
        
        phone_number = contact.get("phone_number")
        message_body = message.get("body", "")
        is_new_message = message.get("is_new_message", False)
        timestamp = datetime.now().isoformat()
        
        # Only process new messages with text body
        if not is_new_message or not message_body:
            logger.info(f"Skipping webhook - is_new: {is_new_message}, has_body: {bool(message_body)}")
            return
        
        if not phone_number:
            logger.warning("Missing phone number in webhook")
            return
        
        message_lower = message_body.lower().strip()
        
        logger.info(f"📨 Message from {phone_number}: {message_body}")
        
        # PRIORITY 1: Handle greetings first (automatic welcome message)
        greeting_keywords = ['hi', 'hello', 'hey', 'namaste', 'hii', 'hlo', 'start', 'help']
        if any(keyword == message_lower or message_lower.startswith(keyword + ' ') for keyword in greeting_keywords):
            await handle_welcome_message(phone_number, contact.get("first_name", "there"))
            return
        
        # PRIORITY 2: Handle medicine reminder responses
        if message_lower in ['taken', '✅ taken', 'yes', 'done']:
            await handle_medicine_response(phone_number, 'taken', timestamp)
            
        elif message_lower in ['skip', '❌ skip', 'skipped', 'no']:
            await handle_medicine_response(phone_number, 'skipped', timestamp)
            
        elif message_lower in ['later', '⏰ later', 'remind later', 'snooze']:
            await handle_medicine_response(phone_number, 'later', timestamp)
            
        elif message_lower in ['stop', 'cancel', 'unsubscribe']:
            await handle_stop_request(phone_number)
            
        # PRIORITY 3: Handle AI agent queries
        elif len(message_body) > 10:  # Likely a question/query
            await handle_ai_query(phone_number, message_body)
            
        else:
            # Unknown message type - send helpful response
            await handle_unknown_message(phone_number)
        
    except Exception as e:
        logger.error(f"Error processing incoming message: {str(e)}")

async def handle_welcome_message(phone_number: str, customer_name: str):
    """Send automatic welcome message when user says hi"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        whatsapp_client = CustomWhatsAppClient()
        
        welcome_message = f"""🙏 *Namaste, {customer_name}!*

Welcome to *AyurEze Healthcare* - Your Ayurvedic Wellness Partner! 🌿

I'm *Astra*, your AI health assistant. I'm here to help you with:

💊 *Medicine Reminders*
Get timely notifications for your medicines

🤖 *Health Questions*
Ask me anything about Ayurveda and wellness

📦 *Order Updates*
Track your medicine orders

🔐 *Secure Documents*
Access your prescriptions and reports

*Quick Commands:*
• Reply with any health question
• Type "TAKEN/SKIP/LATER" for medicine reminders
• Type "HELP" for more options

_How can I assist you today?_ 🌿"""
        
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=welcome_message
        )
        
        logger.info(f"👋 Welcome message sent to {phone_number}")
        
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}")

async def handle_unknown_message(phone_number: str):
    """Send helpful response for unknown messages"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        whatsapp_client = CustomWhatsAppClient()
        
        help_message = """🌿 *AyurEze Healthcare*

I didn't quite understand that. Here's what I can help with:

💊 *Medicine Reminders:*
Reply TAKEN/SKIP/LATER

🤖 *Health Questions:*
Ask me anything about Ayurveda

🆘 *Need Help?*
Type "HELP" for all commands

_Try asking a health question!_ 🌿"""
        
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=help_message
        )
        
        logger.info(f"❓ Help message sent to {phone_number}")
        
    except Exception as e:
        logger.error(f"Error sending help message: {str(e)}")

async def handle_medicine_response(phone_number: str, response: str, timestamp: str):
    """Handle patient response to medicine reminder"""
    try:
        from app.medicine_reminders.reminder_engine import ReminderEngine
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        reminder_engine = ReminderEngine()
        whatsapp_client = CustomWhatsAppClient()
        
        # Update adherence tracking
        success = reminder_engine.handle_patient_response(
            patient_phone=phone_number,
            response=response,
            message_timestamp=timestamp
        )
        
        if success:
            # Send confirmation
            confirmation_messages = {
                'taken': "✅ Great! Medicine recorded as taken. Keep up the good work! 🌿",
                'skipped': "⚠️ Noted. Please don't miss your next dose for better health outcomes.",
                'later': "⏰ Okay, I'll remind you in 30 minutes. Don't forget!"
            }
            
            confirmation = confirmation_messages.get(response, "Message received")
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=confirmation
            )
            
            logger.info(f"✅ Medicine response '{response}' processed for {phone_number}")
        else:
            logger.warning(f"Failed to process medicine response for {phone_number}")
            
    except Exception as e:
        logger.error(f"Error handling medicine response: {str(e)}")

async def handle_ai_query(phone_number: str, query: str):
    """Handle patient query using AI agent"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.database_models import PatientProfile, SessionLocal
        import main_enhanced
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Get patient name from database
        db = SessionLocal()
        try:
            patient = db.query(PatientProfile).filter(
                PatientProfile.phone.like(f"%{phone_number.replace('+', '').replace('91', '')}%")
            ).first()
            
            patient_name = patient.name if patient else "there"
        finally:
            db.close()
        
        # Get AI response using the global model inference
        if main_enhanced.model_inference:
            ai_response = await main_enhanced.model_inference.generate_response(query)
        else:
            ai_response = "Thank you for your message! Our AI assistant is currently loading. Please try again in a moment. 🌿"
        
        # Send AI response via WhatsApp
        await whatsapp_client.send_ai_response(
            patient_phone=phone_number,
            patient_name=patient_name,
            ai_message=ai_response
        )
        
        logger.info(f"🤖 AI query handled for {phone_number}")
        
    except Exception as e:
        logger.error(f"Error handling AI query: {str(e)}")

async def handle_stop_request(phone_number: str):
    """Handle patient request to stop reminders"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.database_models import PatientProfile, MedicineSchedule, SessionLocal
        
        whatsapp_client = CustomWhatsAppClient()
        db = SessionLocal()
        
        try:
            # Find patient
            patient = db.query(PatientProfile).filter(
                PatientProfile.phone.like(f"%{phone_number.replace('+', '').replace('91', '')}%")
            ).first()
            
            if patient:
                # Disable all active schedules
                active_schedules = db.query(MedicineSchedule).filter(
                    MedicineSchedule.patient_id == patient.patient_id,
                    MedicineSchedule.is_active == True
                ).all()
                
                for schedule in active_schedules:
                    schedule.reminders_enabled = False
                
                db.commit()
                
                # Send confirmation
                message = f"""🛑 *Reminders Paused*

Hello {patient.name},

Your medicine reminders have been paused as requested.

To resume reminders, please contact your doctor or reply with "START".

_AyurEze Healthcare Team_ 🌿"""
                
                await whatsapp_client.send_text_message(
                    phone_number=phone_number,
                    message_body=message
                )
                
                logger.info(f"🛑 Reminders stopped for {phone_number}")
            else:
                logger.warning(f"Patient not found for stop request: {phone_number}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling stop request: {str(e)}")
