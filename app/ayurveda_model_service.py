"""
Ayurveda AI Model Service
Uses your custom trained model: ayureasehealthcare/ayurze-llama-3b-1.9
Base model: unsloth/llama-3.2-3b-instruct-unsloth-bnb-4bit
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from huggingface_hub import InferenceClient
import asyncio

logger = logging.getLogger(__name__)

class AyurvedaModelService:
    """
    Service to interact with your custom Ayurveda LLM model
    """
    
    def __init__(self):
        self.model_id = os.getenv("AYURVEDA_MODEL_ID", "ayureasehealthcare/ayurze-llama-3b-1.9")
        self.api_url = os.getenv("AYURVEDA_API_URL", "https://ayureze-fastapi.hf.space")
        self.hf_token = os.getenv("HF_TOKEN")
        self.loaded = False
        
        # Try to connect to the deployed API
        try:
            import httpx
            response = httpx.get(f"{self.api_url}/health", timeout=10.0)
            if response.status_code == 200:
                logger.info(f"✅ Ayurveda API connected: {self.api_url}")
                logger.info(f"   Model: Astra - Ayurvedic AI Assistant")
                self.loaded = True
            else:
                logger.warning(f"⚠️ Ayurveda API returned {response.status_code}")
                self.loaded = False
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Ayurveda API: {e}")
            self.loaded = False
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Generate Ayurvedic wellness advice using deployed Astra API
        
        Args:
            prompt: User's health question or concern
            system_prompt: Optional system instructions
            max_tokens: Maximum response length
            temperature: Creativity (0-1)
            top_p: Nucleus sampling
            
        Returns:
            Dict with response and metadata
        """
        if not self.loaded:
            return {
                "response": self._get_fallback_response(prompt),
                "model_used": "fallback",
                "tokens": 0,
                "success": False
            }
        
        try:
            import httpx
            
            # Prepare the prompt with context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAstra:"
            
            logger.info(f"🤖 Calling Astra API for: {prompt[:50]}...")
            
            # Calculate proper max_length
            # Astra API uses max_length (total tokens including input)
            # Average: 1 token ≈ 4 characters
            estimated_input_tokens = len(full_prompt) // 4
            # Add requested output tokens + buffer
            adjusted_max_length = estimated_input_tokens + max_tokens + 100
            
            # Ensure we don't exceed a reasonable limit
            adjusted_max_length = min(adjusted_max_length, 2048)
            
            # Call the deployed Astra API with extended timeout
            # HF Space has 2 vCPU/16GB RAM - needs patience for inference
            # Reduce max_tokens for faster response
            optimized_max_tokens = min(max_tokens, 200)  # Smaller = faster on limited CPU
            
            logger.info(f"🔄 Calling HF Space (may take 30-60s on 2 vCPU)...")
            logger.info(f"   Optimized tokens: {optimized_max_tokens}")
            
            async with httpx.AsyncClient(timeout=90.0) as client:  # Extended timeout for slow HF Space
                payload = {
                    "prompt": full_prompt,
                    "max_new_tokens": optimized_max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True,
                    "repetition_penalty": 1.1  # Prevent repetition
                }
                
                response = await client.post(
                    f"{self.api_url}/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", result.get("generated_text", ""))
                    
                    if response_text:
                        token_count = len(response_text.split())
                        logger.info(f"✅ Astra API responded with {token_count} tokens")
                        
                        return {
                            "response": response_text,
                            "model_used": "Astra API",
                            "tokens": token_count,
                            "success": True
                        }
                    else:
                        logger.warning("⚠️ Empty response from Astra API")
                        return {
                            "response": self._get_fallback_response(prompt),
                            "model_used": "fallback",
                            "tokens": 0,
                            "success": False
                        }
                else:
                    logger.error(f"❌ Astra API error: {response.status_code}")
                    return {
                        "response": self._get_fallback_response(prompt),
                        "model_used": "fallback",
                        "tokens": 0,
                        "success": False
                    }
            
        except Exception as e:
            logger.error(f"Error calling Astra API: {e}")
            return {
                "response": self._get_fallback_response(prompt),
                "model_used": "fallback",
                "tokens": 0,
                "error": str(e),
                "success": False
            }
    # Removed _format_chat_prompt - now using deployed Astra API
    
    def _get_fallback_response(self, prompt: str) -> str:
        """
        Fallback responses when model is unavailable
        """
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['stress', 'anxiety', 'tension']):
            return """🧘 For stress and anxiety, Ayurveda recommends:

**Immediate Relief:**
- Practice Pranayama (deep breathing) - 10 minutes daily
- Drink warm Ashwagandha tea before bed
- Apply Brahmi oil on scalp and feet

**Lifestyle Changes:**
- Wake up during Brahma Muhurta (sunrise)
- Practice meditation for 15 minutes
- Avoid caffeine after 4 PM

**Herbs to Consider:**
- Ashwagandha (500mg twice daily)
- Brahmi for mental clarity
- Jatamansi for deep relaxation

Remember to consult an Ayurvedic practitioner for personalized dosha-based treatment."""

        elif any(word in prompt_lower for word in ['digestion', 'stomach', 'acidity']):
            return """🌿 For digestive health, follow these Ayurvedic principles:

**Agni (Digestive Fire) Enhancement:**
- Drink warm water with lemon in the morning
- Eat meals at regular times
- Chew food thoroughly (32 times per bite)

**Dietary Guidelines:**
- Avoid cold drinks with meals
- Include ginger and cumin in cooking
- Eat largest meal at noon (Pitta time)

**Herbal Support:**
- Triphala powder before bed
- Fresh ginger tea after meals
- Fennel seeds for gas relief

Avoid heavy, fried, and processed foods. Consult an Ayurvedic doctor for chronic issues."""

        else:
            return """🌸 Hello! I'm Astra, your Ayurvedic wellness companion.

I can help you with:
- Dosha-based health guidance
- Natural remedies and herbs
- Diet and lifestyle recommendations
- Stress management techniques
- Seasonal health tips

Please tell me more about your health concern, and I'll provide personalized Ayurvedic guidance based on ancient wisdom and modern understanding.

What specific health issue would you like to address today?"""
    
    def is_available(self) -> bool:
        """Check if model service is available"""
        return self.loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_id": self.model_id,
            "loaded": self.loaded,
            "available": self.is_available(),
            "base_model": "unsloth/llama-3.2-3b-instruct-unsloth-bnb-4bit",
            "specialization": "Ayurvedic Wellness",
            "capabilities": [
                "Dosha analysis",
                "Herbal recommendations",
                "Lifestyle guidance",
                "Diet planning",
                "Yoga and meditation"
            ]
        }

# Global instance
ayurveda_model_service = AyurvedaModelService()
