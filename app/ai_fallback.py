"""
AI Fallback for Railway Deployment
Uses Hugging Face Inference API instead of local model
"""
import os
import requests
from typing import Optional

class AIFallbackService:
    """Lightweight AI service using Hugging Face API"""
    
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
        self.model_id = "ayureasehealthcare/llama3-ayurveda-lora-v3"
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        
    async def generate_response(
        self, 
        message: str, 
        language: str = "en",
        conversation_history: Optional[list] = None
    ) -> str:
        """
        Generate AI response using Hugging Face Inference API
        Falls back to predefined responses if API unavailable
        """
        try:
            # Build context from history
            context = ""
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages
                    context += f"User: {msg.get('user_message', '')}\n"
                    context += f"Astra: {msg.get('ai_response', '')}\n"
            
            # Build prompt
            prompt = f"{context}User: {message}\nAstra:"
            
            # If HF token available, use API
            if self.hf_token:
                return await self._call_hf_api(prompt)
            else:
                # Fall back to predefined responses
                return self._get_fallback_response(message, language)
                
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_response(message, language)
    
    async def _call_hf_api(self, prompt: str) -> str:
        """Call Hugging Face Inference API"""
        try:
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    # Extract only the new response
                    if "Astra:" in generated_text:
                        return generated_text.split("Astra:")[-1].strip()
                    return generated_text.strip()
            
            # If API call fails, use fallback
            return self._get_fallback_response(prompt, "en")
            
        except Exception as e:
            print(f"HF API call failed: {e}")
            return self._get_fallback_response(prompt, "en")
    
    def _get_fallback_response(self, message: str, language: str) -> str:
        """Predefined responses when AI unavailable"""
        message_lower = message.lower()
        
        # Health topics
        if any(word in message_lower for word in ["digest", "stomach", "acidity", "gas"]):
            return self._translate(
                "For digestive health, try drinking warm water with ginger. "
                "Avoid heavy, oily foods and eat smaller meals throughout the day. "
                "Consider triphala before bed for gentle digestive support.",
                language
            )
        
        elif any(word in message_lower for word in ["sleep", "insomnia", "can't sleep"]):
            return self._translate(
                "For better sleep, establish a regular bedtime routine. "
                "Drink warm milk with nutmeg before bed. Avoid screens 1 hour before sleep. "
                "Try abhyanga (self-massage) with warm sesame oil in the evening.",
                language
            )
        
        elif any(word in message_lower for word in ["stress", "anxiety", "tension"]):
            return self._translate(
                "To reduce stress, practice pranayama (breathing exercises) daily. "
                "Try ashwagandha tea in the evening. Maintain regular sleep and meal times. "
                "Consider meditation or yoga for 15-20 minutes each day.",
                language
            )
        
        elif any(word in message_lower for word in ["immunity", "immune", "cold", "fever"]):
            return self._translate(
                "To boost immunity, drink warm water with tulsi leaves daily. "
                "Include turmeric, ginger, and honey in your diet. "
                "Ensure adequate sleep and regular exercise. Consider chyawanprash in the morning.",
                language
            )
        
        elif any(word in message_lower for word in ["weight", "lose weight", "fat"]):
            return self._translate(
                "For healthy weight management, drink warm water with lemon in the morning. "
                "Eat your largest meal at lunch when digestion is strongest. "
                "Include more vegetables and reduce refined carbs. Walk for 30 minutes daily.",
                language
            )
        
        elif any(word in message_lower for word in ["skin", "acne", "pimples"]):
            return self._translate(
                "For healthy skin, drink plenty of water and eat fresh fruits. "
                "Apply aloe vera gel for natural hydration. "
                "Avoid processed foods and get adequate sleep. Try neem for purification.",
                language
            )
        
        elif any(word in message_lower for word in ["hair", "hair fall", "baldness"]):
            return self._translate(
                "For healthy hair, massage scalp with warm coconut oil weekly. "
                "Include protein-rich foods like dal and nuts. "
                "Try amla powder for hair strength. Avoid harsh chemicals and heat styling.",
                language
            )
        
        else:
            # Generic response
            return self._translate(
                "Thank you for your question. I'm here to help with Ayurvedic wellness guidance. "
                "Please feel free to ask about digestion, sleep, stress, immunity, weight management, "
                "skin health, or any other wellness topics.",
                language
            )
    
    def _translate(self, text: str, language: str) -> str:
        """Simple translation mapping for common languages"""
        if language == "hi":
            translations = {
                "Thank you for your question": "आपके प्रश्न के लिए धन्यवाद",
                "For digestive health": "पाचन स्वास्थ्य के लिए",
                "For better sleep": "बेहतर नींद के लिए",
                "To reduce stress": "तनाव कम करने के लिए",
                "To boost immunity": "प्रतिरक्षा बढ़ाने के लिए",
            }
            for eng, hindi in translations.items():
                text = text.replace(eng, hindi)
        
        return text

# Global instance
ai_fallback = AIFallbackService()
