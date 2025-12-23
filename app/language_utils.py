"""
Language detection and multilingual support utilities with enhanced Indic language support
"""

from langdetect import detect, DetectorFactory, detect_langs
from typing import Dict, Optional, List, Tuple, Any
import logging
import re

# Set seed for consistent results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class LanguageManager:
    """Manages language detection and multilingual responses with enhanced Indic language support"""
    
    # Supported languages with their codes and names
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish", 
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "or": "Odia",
        "as": "Assamese",
        "ur": "Urdu",
        "ne": "Nepali",
        "si": "Sinhala",
        "my": "Myanmar"
    }
    
    # Unicode ranges for Indic scripts (inspired by IndicBERT approach)
    INDIC_SCRIPT_RANGES = {
        "hi": [(0x0900, 0x097F)],  # Devanagari (Hindi, Marathi, Nepali)
        "bn": [(0x0980, 0x09FF)],  # Bengali-Assamese
        "as": [(0x0980, 0x09FF)],  # Bengali-Assamese  
        "gu": [(0x0A80, 0x0AFF)],  # Gujarati
        "pa": [(0x0A00, 0x0A7F)],  # Gurmukhi (Punjabi)
        "or": [(0x0B00, 0x0B7F)],  # Odia
        "ta": [(0x0B80, 0x0BFF)],  # Tamil
        "te": [(0x0C00, 0x0C7F)],  # Telugu
        "kn": [(0x0C80, 0x0CFF)],  # Kannada
        "ml": [(0x0D00, 0x0D7F)],  # Malayalam
        "si": [(0x0D80, 0x0DFF)],  # Sinhala
        "my": [(0x1000, 0x109F)],  # Myanmar
        "mr": [(0x0900, 0x097F)],  # Devanagari (same as Hindi)
        "ne": [(0x0900, 0x097F)],  # Devanagari (same as Hindi)
        "ur": [(0x0600, 0x06FF), (0x0750, 0x077F)]  # Arabic script
    }
    
    # Ayurveda keywords in different languages for topic filtering
    AYURVEDA_KEYWORDS = {
        "en": [
            "ayurveda", "ayurvedic", "dosha", "vata", "pitta", "kapha", "pranayama", 
            "chakra", "meditation", "yoga", "herb", "herbal", "turmeric", "ginger", 
            "ashwagandha", "triphala", "tulsi", "neem", "brahmi", "curcuma", "holistic",
            "natural healing", "traditional medicine", "panchakarma", "rasayana",
            "ojas", "tejas", "prana", "agni", "ama", "malas", "srotas", "dhatus",
            "stress", "anxiety", "sleep", "insomnia", "digestion", "immunity", "weight",
            "skin", "fatigue", "energy", "vitality", "wellness", "balance", "constitution"
        ],
        "hi": [
            "आयुर्वेद", "आयुर्वेदिक", "दोष", "वात", "पित्त", "कफ", "प्राणायाम", 
            "चक्र", "ध्यान", "योग", "जड़ी", "हर्बल", "हल्दी", "अदरक", 
            "अश्वगंधा", "त्रिफला", "तुलसी", "नीम", "ब्राह्मी", "प्राकृतिक",
            "पंचकर्म", "रसायन", "ओजस", "तेजस", "प्राण", "अग्नि", "आम",
            "स्वास्थ्य", "उपचार", "औषधि", "चिकित्सा", "संतुलन", "शरीर", "मन"
        ],
        "ta": [
            "ஆயுர்வेதம்", "தோஷம்", "வாதம்", "பித்தம்", "கபம்", "யோகா", "தியானம்",
            "மஞ்சள்", "இஞ்சி", "துளசி", "வேம்பு", "நெல்லிக்காய்", "ஆரோக்கியம்",
            "மருத்துவம்", "சிகிச்சை", "உடல்", "மனம்", "சமநிலை", "இயற்கை"
        ],
        "te": [
            "ఆయుర్వేదం", "దోషం", "వాతం", "పిత్తం", "కఫం", "యోగా", "ధ్యానం",
            "పసుపు", "అల్లం", "తులసి", "వేప", "ఆరోగ్యం", "వైద్యం", "చికిత్స",
            "శరీరం", "మనసు", "సమతుల్యత", "ప్రకృతి", "ఔషధం"
        ],
        "bn": [
            "আয়ুর্বেদ", "দোষ", "বাত", "পিত্ত", "কফ", "যোগ", "ধ্যান",
            "হলুদ", "আদা", "তুলসী", "নিম", "স্বাস্থ্য", "চিকিৎসা", "ওষুধ",
            "শরীর", "মন", "ভারসাম্য", "প্রাকৃতিক", "ঔষধি"
        ],
        "mr": [
            "आयुर्वेद", "दोष", "वात", "पित्त", "कफ", "योग", "ध्यान",
            "हळद", "आले", "तुळस", "कडुनिंब", "आरोग्य", "चिकित्सा", "औषध",
            "शरीर", "मन", "संतुलन", "नैसर्गिक", "वैद्यकीय"
        ],
        "gu": [
            "આયુર્વેદ", "દોષ", "વાત", "પિત્ત", "કફ", "યોગ", "ધ્યાન",
            "હળદર", "આદુ", "તુલસી", "લીમડો", "આરોગ્य", "ચિકિત્સા", "દવા",
            "શરીર", "મન", "સંતુલન", "કુદરતી", "ઔષધિ"
        ],
        "kn": [
            "ಆಯುರ್ವೇದ", "ದೋಷ", "ವಾತ", "ಪಿತ್ತ", "ಕಫ", "ಯೋಗ", "ಧ್ಯಾನ",
            "ಅರಿಶಿನ", "ಶುಂಠಿ", "ತುಳಸಿ", "ಬೇವು", "ಆರೋಗ್ಯ", "ಚಿಕಿತ್ಸೆ",
            "ಶರೀರ", "ಮನಸು", "ಸಮತೋಲ", "ಪ್ರಾಕೃತಿಕ", "ಔಷಧಿ"
        ],
        "ml": [
            "ആയുര്‍വേദം", "ദോഷം", "വാതം", "പിത്തം", "കഫം", "യോഗ", "ധ്യാനം",
            "മഞ്ഞള്‍", "ഇഞ്ചി", "തുളസി", "വേപ്പ്", "ആരോഗ്യം", "ചികിത്സ",
            "ശരീരം", "മനസ്സ്", "സന്തുലിതാവസ്ഥ", "പ്രകൃതി", "ഔഷധം"
        ],
        "pa": [
            "ਆਯੁਰਵੇਦ", "ਦੋਸ਼", "ਵਾਤ", "ਪਿੱਤ", "ਕਫ", "ਯੋਗ", "ਧਿਆਨ",
            "ਹਲਦੀ", "ਅਦਰਕ", "ਤੁਲਸੀ", "ਨਿੰਮ", "ਸਿਹਤ", "ਇਲਾਜ", "ਦਵਾਈ",
            "ਸਰੀਰ", "ਮਨ", "ਸੰਤੁਲਨ", "ਕੁਦਰਤੀ", "ਜੜੀ-ਬੂਟੀ"
        ],
        "es": [
            "ayurveda", "ayurvédico", "dosha", "vata", "pitta", "kapha", "medicina tradicional",
            "hierbas", "cúrcuma", "jengibre", "meditación", "yoga", "sanación natural"
        ],
        "fr": [
            "ayurveda", "ayurvédique", "dosha", "vata", "pitta", "kapha", "médecine traditionnelle",
            "herbes", "curcuma", "gingembre", "méditation", "yoga", "guérison naturelle"
        ],
        "de": [
            "ayurveda", "ayurvedisch", "dosha", "vata", "pitta", "kapha", "traditionelle medizin",
            "kräuter", "kurkuma", "ingwer", "meditation", "yoga", "natürliche heilung"
        ]
    }
    
    def __init__(self):
        self.default_language = "en"
    
    def _detect_script_language(self, text: str) -> Optional[str]:
        """Detect language based on Unicode script ranges (IndicBERT-inspired approach)"""
        char_counts = {}
        
        for char in text:
            char_code = ord(char)
            for lang_code, ranges in self.INDIC_SCRIPT_RANGES.items():
                for start, end in ranges:
                    if start <= char_code <= end:
                        char_counts[lang_code] = char_counts.get(lang_code, 0) + 1
                        break
        
        if char_counts:
            # Return language with most characters in that script
            return max(char_counts.items(), key=lambda x: x[1])[0]
        return None
    
    def _enhanced_langdetect(self, text: str) -> Tuple[str, float]:
        """Enhanced language detection with confidence scores and telemetry"""
        try:
            # Get probability distribution from langdetect
            lang_probs = detect_langs(text)
            if lang_probs:
                best_lang = lang_probs[0]
                
                # Log telemetry for confidence tracking
                logger.info(
                    "Language detection telemetry",
                    extra={
                        'detected_language': best_lang.lang,
                        'confidence': round(best_lang.prob, 3),
                        'text_length': len(text),
                        'detection_method': 'statistical'
                    }
                )
                
                return best_lang.lang, best_lang.prob
        except Exception as e:
            logger.warning(f"Enhanced language detection failed: {e}")
            
            # Log detection failure
            logger.info(
                "Language detection failure",
                extra={
                    'error': str(e),
                    'text_length': len(text),
                    'fallback_applied': True
                }
            )
        
        # Fallback to basic detection
        try:
            detected = detect(text)
            logger.info(
                "Language detection fallback",
                extra={
                    'detected_language': detected,
                    'confidence': 0.8,
                    'detection_method': 'basic_fallback'
                }
            )
            return detected, 0.8  # Assume reasonable confidence
        except Exception:
            logger.warning("All language detection methods failed, using default")
            return self.default_language, 0.5
    
    def enhanced_language_detection(self, text: str) -> Dict[str, Any]:
        """Enhanced language detection with confidence thresholds and graceful fallback"""
        if not text or not text.strip():
            return {
                'language': self.default_language,
                'confidence': 0.0,
                'requires_confirmation': False,
                'method': 'default_empty_text',
                'fallback_applied': True
            }
        
        # First try script-based detection for Indic languages
        script_detected = self._detect_script_language(text)
        if script_detected:
            logger.info(
                "Script-based language detection",
                extra={
                    'detected_language': script_detected,
                    'confidence': 0.95,  # High confidence for script-based detection
                    'text_length': len(text),
                    'detection_method': 'script_based'
                }
            )
            return {
                'language': script_detected,
                'confidence': 0.95,
                'requires_confirmation': False,
                'method': 'script_based',
                'fallback_applied': False
            }
        
        # Fallback to statistical language detection
        try:
            lang_code, confidence = self._enhanced_langdetect(text)
            
            # Enhanced confidence thresholds
            if confidence >= 0.8 and lang_code in self.SUPPORTED_LANGUAGES:
                # High confidence - use directly
                return {
                    'language': lang_code,
                    'confidence': confidence,
                    'requires_confirmation': False,
                    'method': 'statistical_high_confidence',
                    'fallback_applied': False
                }
            elif confidence >= 0.6 and lang_code in self.SUPPORTED_LANGUAGES:
                # Medium confidence - suggest but ask for confirmation
                return {
                    'detected_language': lang_code,
                    'confidence': confidence,
                    'suggested_language': lang_code,
                    'requires_confirmation': True,
                    'method': 'statistical_medium_confidence',
                    'fallback_applied': False,
                    'confirmation_message': f"I detected {self.get_language_name(lang_code)} with {confidence:.1%} confidence. Is this correct?"
                }
            elif confidence < 0.6:
                # Low confidence - fallback to English with user confirmation
                mapped_lang = self._map_language_variants(lang_code)
                if mapped_lang and mapped_lang in self.SUPPORTED_LANGUAGES:
                    return {
                        'detected_language': lang_code,
                        'confidence': confidence,
                        'suggested_language': mapped_lang,
                        'requires_confirmation': True,
                        'method': 'language_mapping',
                        'fallback_applied': True,
                        'confirmation_message': f"Language unclear (confidence: {confidence:.1%}). Would you prefer {self.get_language_name(mapped_lang)}?"
                    }
                else:
                    return {
                        'detected_language': lang_code,
                        'confidence': confidence,
                        'suggested_language': 'en',
                        'requires_confirmation': True,
                        'method': 'low_confidence_fallback',
                        'fallback_applied': True,
                        'confirmation_message': f"Language unclear (confidence: {confidence:.1%}). Shall I respond in English?"
                    }
            
            return {
                'language': self.default_language,
                'confidence': 0.0,
                'requires_confirmation': False,
                'method': 'default_unsupported',
                'fallback_applied': True,
                'error': 'unsupported_language_detected'
            }
            
        except Exception as e:
            logger.error(
                "Language detection failed completely",
                extra={
                    'error': str(e),
                    'text_length': len(text),
                    'fallback_to_default': True
                }
            )
            return {
                'language': self.default_language,
                'confidence': 0.0,
                'error': 'detection_failed',
                'fallback_applied': True,
                'requires_confirmation': False,
                'method': 'error_fallback'
            }
    
    def detect_language(self, text: str) -> str:
        """Legacy method - maintains compatibility while using enhanced detection"""
        result = self.enhanced_language_detection(text)
        return result.get('language', self.default_language)
    
    def _map_language_variants(self, lang_code: str) -> Optional[str]:
        """Map language variants to supported languages"""
        mapping = {
            "ne": "hi",  # Nepali uses Devanagari, similar to Hindi
            "bh": "hi",  # Bihari to Hindi
            "mai": "hi", # Maithili to Hindi
            "sa": "hi",  # Sanskrit to Hindi (Devanagari script)
        }
        return mapping.get(lang_code, None)
    
    def get_language_confidence(self, text: str, language: str) -> float:
        """Get confidence score for detected language"""
        try:
            lang_probs = detect_langs(text)
            for lang_prob in lang_probs:
                if lang_prob.lang == language:
                    return lang_prob.prob
            return 0.0
        except Exception:
            return 0.0
    
    def validate_detection_with_keywords(self, text: str, detected_language: str) -> Dict[str, Any]:
        """Validate language detection using context keywords"""
        text_lower = text.lower()
        
        # Check if text contains keywords from detected language
        keywords = self.AYURVEDA_KEYWORDS.get(detected_language, [])
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        # Calculate keyword-based confidence boost
        keyword_confidence = min(keyword_matches * 0.1, 0.3)  # Max 30% boost
        
        return {
            'keyword_matches': keyword_matches,
            'keyword_confidence_boost': keyword_confidence,
            'keywords_found': [kw for kw in keywords if kw.lower() in text_lower][:3]  # Top 3
        }
    
    def is_ayurveda_related(self, text: str, language: Optional[str] = None) -> bool:
        """Check if the text is related to Ayurveda topics"""
        if not language:
            language = self.detect_language(text)
        
        if not language:
            language = self.default_language
        
        text_lower = text.lower()
        
        # Check keywords for detected language
        keywords = self.AYURVEDA_KEYWORDS.get(language, self.AYURVEDA_KEYWORDS["en"])
        
        # Also check English keywords as fallback
        if language != "en":
            keywords.extend(self.AYURVEDA_KEYWORDS["en"])
        
        # Check if any Ayurveda keywords are present
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Additional health-related terms that could be Ayurveda context
        health_terms = [
            "health", "wellness", "healing", "medicine", "treatment", "remedy",
            "natural", "holistic", "traditional", "herbal", "pain", "disease",
            "cure", "therapy", "balance", "energy", "body", "mind", "spirit",
            "constitution", "detox", "cleanse"
        ]
        
        health_matches = sum(1 for term in health_terms if term in text_lower)
        
        # If one or more health terms are present, likely Ayurveda-related (made more permissive)
        return health_matches >= 1
    
    def get_language_name(self, language_code: str) -> str:
        """Get language name from code"""
        return self.SUPPORTED_LANGUAGES.get(language_code, "English")
    
    def get_astra_greeting(self, language: str) -> str:
        """Get Astra's greeting in specified language"""
        greetings = {
            "en": "Namaste! I'm Astra, your Ayurvedic wellness assistant. How can I help you on your journey to holistic health today?",
            "hi": "नमस्ते! मैं अस्त्रा हूँ, आपकी आयुर्वेदिक कल्याण सहायक। आज मैं आपकी समग्र स्वास्थ्य यात्रा में कैसे सहायता कर सकती हूँ?",
            "es": "¡Namaste! Soy Astra, tu asistente de bienestar ayurvédico. ¿Cómo puedo ayudarte en tu viaje hacia la salud holística hoy?",
            "fr": "Namaste! Je suis Astra, votre assistante de bien-être ayurvédique. Comment puis-je vous aider dans votre voyage vers la santé holistique aujourd'hui?",
            "de": "Namaste! Ich bin Astra, deine ayurvedische Wellness-Assistentin. Wie kann ich dir heute auf deiner Reise zur ganzheitlichen Gesundheit helfen?"
        }
        return greetings.get(language, greetings["en"])
    
    def get_non_ayurveda_response(self, language: str) -> str:
        """Get friendly response for non-Ayurveda questions"""
        responses = {
            "en": [
                "Hello there! 😊 I'm Astra, and I'm absolutely passionate about Ayurvedic wellness and traditional healing. While I'd love to chat about everything, I'm specifically designed to help with questions about Ayurveda, herbal remedies, dosha balancing, and holistic health practices. Could you ask me something about Ayurvedic medicine or wellness instead? I'm super excited to share that knowledge with you! 🌿✨",
                "Hi! 🙏 I appreciate your question, but I'm Astra - your dedicated Ayurvedic wellness companion! I focus exclusively on sharing the beautiful wisdom of Ayurveda, natural healing, herbs, lifestyle practices, and traditional wellness approaches. Is there anything about your health, wellness journey, or Ayurvedic practices you'd like to explore together? I'd be delighted to help! 💚",
                "Namaste! 🌸 While that's an interesting topic, I'm here specifically as your Ayurvedic wellness guide. My heart and expertise lie in traditional Indian medicine, herbs, dosha balancing, and natural healing practices. How about we explore something wonderful about Ayurveda instead? Maybe questions about stress relief, better sleep, digestion, or discovering your unique constitution? I'm here and ready to help! ✨🌿"
            ],
            "hi": [
                "नमस्ते! 🙏 मैं अस्त्रा हूँ, आयुर्वेदिक कल्याण और पारंपरिक चिकित्सा में विशेषज्ञ। मैं केवल आयुर्वेद, हर्बल उपचार, दोष संतुलन, और समग्र स्वास्थ्य प्रथाओं से संबंधित प्रश्नों में सहायता कर सकती हूँ। कृपया मुझसे आयुर्वेदिक चिकित्सा या कल्याण के बारे में कुछ पूछें। मैं आपकी सहायता करने के लिए उत्सुक हूँ! 🌿✨",
                "आपका प्रश्न दिलचस्प है, लेकिन मैं विशेष रूप से आयुर्वेदिक स्वास्थ्य और प्राकृतिक चिकित्सा में मार्गदर्शन करती हूँ। क्या आप अपने स्वास्थ्य, कल्याण, या आयुर्वेदिक प्रथाओं के बारे में कुछ पूछना चाहेंगे? मैं खुशी से आपकी सहायता करूंगी! 💚"
            ],
            "es": [
                "¡Hola! 😊 Soy Astra, especializada en bienestar ayurvédico y sanación tradicional. Aunque me encantaría charlar sobre todo, estoy específicamente diseñada para ayudar con preguntas sobre Ayurveda, remedios herbales, equilibrio de doshas y prácticas de salud holística. ¿Podrías preguntarme algo sobre medicina ayurvédica o bienestar? ¡Estoy súper emocionada de compartir ese conocimiento contigo! 🌿✨",
                "¡Namaste! 🙏 Aunque es un tema interesante, estoy aquí específicamente como tu guía de bienestar ayurvédico. Mi corazón y experiencia están en la medicina tradicional india, hierbas, equilibrio de doshas y prácticas de sanación natural. ¿Qué tal si exploramos algo maravilloso sobre Ayurveda? ¡Estoy aquí y lista para ayudar! ✨🌿"
            ],
            "fr": [
                "Bonjour! 😊 Je suis Astra, spécialisée dans le bien-être ayurvédique et la guérison traditionnelle. Bien que j'aimerais discuter de tout, je suis spécifiquement conçue pour aider avec des questions sur l'Ayurveda, les remèdes à base de plantes et les pratiques de santé holistique. Pourriez-vous me poser une question sur la médecine ayurvédique ou le bien-être? Je suis super excitée de partager cette connaissance avec vous! 🌿✨"
            ],
            "de": [
                "Hallo! 😊 Ich bin Astra, spezialisiert auf ayurvedisches Wohlbefinden und traditionelle Heilung. Obwohl ich gerne über alles sprechen würde, bin ich speziell dafür entwickelt, bei Fragen zu Ayurveda, Kräuterheilmitteln und ganzheitlichen Gesundheitspraktiken zu helfen. Könnten Sie mir stattdessen eine Frage zur ayurvedischen Medizin oder zum Wohlbefinden stellen? 🌿✨"
            ]
        }
        response_list = responses.get(language, responses["en"])
        # Return a random response for variety
        import random
        return random.choice(response_list)

    def get_detection_telemetry(self) -> Dict[str, Any]:
        """Get language detection telemetry summary"""
        # This would typically pull from a database or cache
        # For now, return a basic structure
        return {
            'total_detections': 0,
            'confidence_distribution': {
                'high_confidence': 0,  # >= 0.8
                'medium_confidence': 0,  # 0.6 - 0.8
                'low_confidence': 0,  # < 0.6
            },
            'language_distribution': {},
            'confirmation_requests': 0,
            'fallback_count': 0
        }

# Global language manager instance
language_manager = LanguageManager()