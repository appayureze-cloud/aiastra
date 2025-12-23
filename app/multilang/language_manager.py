"""
Language Manager for Multi-Language Medicine Reminder System
Supports Tamil, Hindi, and English with automatic language detection
"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from langdetect import detect
import json

logger = logging.getLogger(__name__)

class LanguageManager:
    """Manages multi-language support for medicine reminders"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'ta': 'Tamil', 
            'hi': 'Hindi'
        }
        
        # Load translations
        self.translations = self._load_translations()
        
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation dictionaries for all supported languages"""
        translations = {
            'en': {
                # Medicine reminders
                'reminder_greeting': "Hi {patient_name}! 💊",
                'time_for_medicine': "Time for your {medicine_name}",
                'take_dosage': "Please take {dosage}",
                'timing_before_food': "Take before meals 🍽️",
                'timing_after_food': "Take after meals 🍽️", 
                'timing_morning': "Morning dose 🌅",
                'timing_afternoon': "Afternoon dose ☀️",
                'timing_evening': "Evening dose 🌆",
                'timing_night': "Night dose 🌙",
                'response_options': "Reply: ✅ TAKEN | ❌ SKIP | ⏰ LATER | 🛑 STOP",
                'footer': "Ayureze Healthcare - Your wellness partner 🏥",
                
                # Response confirmations
                'medicine_taken': "Great! Medicine taken successfully ✅",
                'medicine_skipped': "Medicine skipped. Please consult your doctor if needed ❌",
                'medicine_later': "Reminder set for later ⏰",
                'reminders_stopped': "Reminders stopped. Take care! 🛑",
                
                # Escalation messages
                'missed_dose_alert': "⚠️ IMPORTANT: You missed your {medicine_name} dose",
                'critical_medicine': "This is critical medicine. Please take immediately!",
                'family_notification': "Patient {patient_name} missed critical medicine {medicine_name}",
                
                # Emergency alerts
                'emergency_missed': "🚨 EMERGENCY: Critical medicine missed for 24+ hours",
                'doctor_consultation': "Please consult your doctor immediately",
                'emergency_contact': "Emergency contact has been notified"
            },
            'ta': {
                # Medicine reminders in Tamil
                'reminder_greeting': "வணக்கம் {patient_name}! 💊",
                'time_for_medicine': "உங்கள் {medicine_name} மருந்து நேரம்",
                'take_dosage': "தயவுசெய்து {dosage} எடுத்துக்கொள்ளுங்கள்",
                'timing_before_food': "சாப்பாட்டிற்கு முன் எடுக்கவும் 🍽️",
                'timing_after_food': "சாப்பாட்டிற்கு பின் எடுக்கவும் 🍽️",
                'timing_morning': "காலை மருந்து 🌅", 
                'timing_afternoon': "மதிய மருந்து ☀️",
                'timing_evening': "மாலை மருந்து 🌆",
                'timing_night': "இரவு மருந்து 🌙",
                'response_options': "பதில்: ✅ எடுத்தேன் | ❌ தவிர்க்க | ⏰ பிறகு | 🛑 நிறுத்து",
                'footer': "ஆயுரேஜ் ஹெல்த்கேர் - உங்கள் நல்வாழ்வு பங்காளி 🏥",
                
                # Response confirmations
                'medicine_taken': "சிறப்பு! மருந்து வெற்றிகரமாக எடுக்கப்பட்டது ✅",
                'medicine_skipped': "மருந்து தவிர்க்கப்பட்டது. தேவைப்பட்டால் மருத்துவரை அணுகவும் ❌",
                'medicine_later': "பிற்பாடு நினைவூட்டல் அமைக்கப்பட்டது ⏰",
                'reminders_stopped': "நினைவூட்டல்கள் நிறுத்தப்பட்டன. கவனமாக இருங்கள்! 🛑",
                
                # Escalation messages  
                'missed_dose_alert': "⚠️ முக்கியம்: நீங்கள் {medicine_name} மருந்து தவறவிட்டீர்கள்",
                'critical_medicine': "இது முக்கியமான மருந்து. உடனே எடுத்துக்கொள்ளுங்கள்!",
                'family_notification': "நோயாளி {patient_name} முக்கிய மருந்து {medicine_name} தவறவிட்டார்",
                
                # Emergency alerts
                'emergency_missed': "🚨 அவசரம்: 24+ மணி நேரமாக முக்கிய மருந்து தவறவிடப்பட்டது",
                'doctor_consultation': "உடனே உங்கள் மருத்துவரை அணுகவும்",
                'emergency_contact': "அவசர தொடர்புக்கு அறிவிக்கப்பட்டுள்ளது"
            },
            'hi': {
                # Medicine reminders in Hindi
                'reminder_greeting': "नमस्ते {patient_name}! 💊",
                'time_for_medicine': "आपकी {medicine_name} दवा का समय",
                'take_dosage': "कृपया {dosage} लें",
                'timing_before_food': "खाना खाने से पहले लें 🍽️",
                'timing_after_food': "खाना खाने के बाद लें 🍽️",
                'timing_morning': "सुबह की दवा 🌅",
                'timing_afternoon': "दोपहर की दवा ☀️", 
                'timing_evening': "शाम की दवा 🌆",
                'timing_night': "रात की दवा 🌙",
                'response_options': "जवाब: ✅ ली गई | ❌ छोड़ें | ⏰ बाद में | 🛑 बंद करें",
                'footer': "आयुरेज हेल्थकेयर - आपका कल्याण साथी 🏥",
                
                # Response confirmations
                'medicine_taken': "बढ़िया! दवा सफलतापूर्वक ली गई ✅", 
                'medicine_skipped': "दवा छोड़ी गई। जरूरत पड़ने पर डॉक्टर से सलाह लें ❌",
                'medicine_later': "बाद के लिए रिमाइंडर सेट किया गया ⏰",
                'reminders_stopped': "रिमाइंडर बंद कर दिए गए। ध्यान रखें! 🛑",
                
                # Escalation messages
                'missed_dose_alert': "⚠️ महत्वपूर्ण: आपने {medicine_name} दवा छोड़ी है",
                'critical_medicine': "यह महत्वपूर्ण दवा है। तुरंत लें!",
                'family_notification': "मरीज़ {patient_name} ने महत्वपूर्ण दवा {medicine_name} छोड़ी है",
                
                # Emergency alerts
                'emergency_missed': "🚨 आपातकाल: 24+ घंटे से महत्वपूर्ण दवा छूटी हुई",
                'doctor_consultation': "तुरंत अपने डॉक्टर से सलाह लें", 
                'emergency_contact': "आपातकालीन संपर्क को सूचित किया गया है"
            }
        }
        
        return translations
    
    def detect_language(self, text: str) -> str:
        """Detect language from text input"""
        try:
            detected = detect(text)
            # Map detected codes to our supported languages
            if detected in ['ta', 'tamil']:
                return 'ta'
            elif detected in ['hi', 'hindi']:
                return 'hi'
            else:
                return 'en'  # Default to English
        except:
            return 'en'  # Default to English on detection failure
    
    def get_translation(self, key: str, language: str = 'en', **kwargs) -> str:
        """Get translated text for a given key and language"""
        try:
            # Get base translation
            text = self.translations.get(language, {}).get(key, 
                   self.translations['en'].get(key, key))
            
            # Format with provided variables
            if kwargs:
                text = text.format(**kwargs)
                
            return text
        except Exception as e:
            logger.error(f"Translation error for key '{key}': {str(e)}")
            return key  # Return key as fallback
    
    def create_multilingual_reminder(self, patient_name: str, medicine_name: str, 
                                   dosage: str, timing_type: str, language: str = 'en') -> str:
        """Create a complete medicine reminder in specified language"""
        
        # Build reminder message parts
        greeting = self.get_translation('reminder_greeting', language, patient_name=patient_name)
        medicine_time = self.get_translation('time_for_medicine', language, medicine_name=medicine_name)
        dosage_instruction = self.get_translation('take_dosage', language, dosage=dosage)
        
        # Get timing-specific message
        timing_key = f'timing_{timing_type.lower()}'
        timing_msg = self.get_translation(timing_key, language)
        
        # Response options and footer
        responses = self.get_translation('response_options', language)
        footer = self.get_translation('footer', language)
        
        # Combine into complete message
        complete_message = f"""{greeting}

{medicine_time} 
{dosage_instruction}

{timing_msg}

{responses}

{footer}"""
        
        return complete_message
    
    def create_response_confirmation(self, response_type: str, language: str = 'en', **kwargs) -> str:
        """Create response confirmation message in specified language"""
        
        confirmation_keys = {
            'taken': 'medicine_taken',
            'skipped': 'medicine_skipped', 
            'later': 'medicine_later',
            'stop': 'reminders_stopped'
        }
        
        key = confirmation_keys.get(response_type, 'medicine_taken')
        return self.get_translation(key, language, **kwargs)
    
    def create_escalation_message(self, medicine_name: str, patient_name: str, 
                                 is_critical: bool = False, language: str = 'en') -> str:
        """Create escalation message for missed doses"""
        
        if is_critical:
            alert = self.get_translation('missed_dose_alert', language, medicine_name=medicine_name)
            critical = self.get_translation('critical_medicine', language)
            footer = self.get_translation('footer', language)
            
            return f"{alert}\n\n{critical}\n\n{footer}"
        else:
            return self.get_translation('missed_dose_alert', language, medicine_name=medicine_name)
    
    def create_family_notification(self, patient_name: str, medicine_name: str, 
                                  language: str = 'en') -> str:
        """Create family member notification message"""
        return self.get_translation('family_notification', language, 
                                  patient_name=patient_name, medicine_name=medicine_name)
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Return dictionary of supported language codes and names"""
        return self.supported_languages.copy()

# Global language manager instance
language_manager = LanguageManager()