"""
Astra AI Agent - Connected to your Llama LoRA model on Hugging Face Space
Uses: https://ayureze-fastapi.hf.space/
"""

import asyncio
import logging
import httpx
from typing import Optional

from app.language_utils import language_manager

logger = logging.getLogger(__name__)

class AstraModelInference:
    """Astra - Your Ayurvedic wellness assistant using YOUR trained Llama LoRA model"""
    
    def __init__(self, base_model_id: str = "", lora_model_id: str = "", device: str = "cpu"):
        self.api_endpoint = "https://ayureze-fastapi.hf.space"
        self.loaded = False
        logger.info("✅ Astra AI Agent initialized - connecting to your Llama model...")
        
    async def load_model(self):
        """Initialize connection to your Hugging Face Space"""
        try:
            logger.info("🤖 Connecting to your AI model at Hugging Face Space...")
            logger.info(f"🔗 Endpoint: {self.api_endpoint}")
            
            # Check if the API is accessible
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self.api_endpoint}/health", timeout=10.0)
                    if response.status_code == 200:
                        health_data = response.json()
                        logger.info(f"✅ API is healthy: {health_data}")
                        
                        # Try to load the model
                        logger.info("⏳ Loading your Llama LoRA model...")
                        try:
                            load_response = await client.post(
                                f"{self.api_endpoint}/load-model",
                                timeout=180.0  # 3 minutes for model loading
                            )
                            if load_response.status_code == 200:
                                logger.info("✅ Your Llama model loaded successfully!")
                                self.loaded = True
                            else:
                                logger.warning(f"Model load returned {load_response.status_code}")
                                logger.info("💡 Will use conversational responses until model loads")
                                self.loaded = False
                        except Exception as e:
                            logger.warning(f"Model loading in progress: {str(e)}")
                            logger.info("💡 Will use conversational responses until model is ready")
                            self.loaded = False
                    else:
                        logger.warning(f"API returned {response.status_code}")
                        self.loaded = False
                        
                except Exception as e:
                    logger.warning(f"Could not connect to AI endpoint: {str(e)}")
                    logger.info("💡 Using conversational responses as fallback")
                    self.loaded = False
            
        except Exception as e:
            logger.error(f"Error initializing: {str(e)}")
            self.loaded = False
    
    def is_loaded(self) -> bool:
        return True  # Always ready (with fallback if needed)
    
    async def generate_response(
        self,
        prompt: str,
        language: str = "en",
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True
    ) -> str:
        """Generate response from YOUR trained Llama LoRA model or fallback"""
        
        # Try to get response from your Llama model first
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/generate",
                    json={
                        "prompt": prompt,
                        "max_length": max_length,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "do_sample": do_sample
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("generated_text", data.get("response", ""))
                    if ai_response:
                        logger.info(f"✅ Response from YOUR Llama LoRA model: {len(ai_response)} chars")
                        return ai_response
                    
                elif response.status_code == 503:
                    # Model not loaded yet - use fallback
                    logger.info("⏳ Model still loading, using conversational fallback")
                else:
                    logger.warning(f"API returned {response.status_code}: {response.text}")
                    
        except httpx.TimeoutException:
            logger.warning("Model response timeout, using conversational fallback")
        except Exception as e:
            logger.warning(f"Model API error: {str(e)}, using conversational fallback")
        
        # Use conversational fallback
        logger.info("💬 Using conversational fallback response")
        return self._get_fallback_response(prompt, language)
    
    def _get_fallback_response(self, prompt: str, language: str = "en") -> str:
        """Intelligent conversational responses for Ayurvedic wellness"""
        prompt_lower = prompt.lower()
        
        # Digestion & Gut Health
        if any(word in prompt_lower for word in ['digestion', 'stomach', 'acidity', 'gas', 'bloating', 'indigestion', 'constipation']):
            return """Hey! For better digestion, here's what works wonders:

Try ginger tea before meals - it fires up your digestive system! Also, warm water throughout the day is your best friend. Chew slowly and avoid cold drinks with meals.

A short walk after eating helps everything settle nicely. Triphala at bedtime is amazing for regularity. Let me know how it goes! 🌿"""
        
        # Sleep & Rest
        elif any(word in prompt_lower for word in ['sleep', 'insomnia', 'tired', 'fatigue', 'rest', 'exhausted']):
            return """Sleep troubles? I hear you! Here's what can help:

Warm milk with a pinch of nutmeg before bed works like magic. Also, try massaging your feet with sesame oil - sounds simple but it's incredibly calming!

Keep dinner light and early. Wind down by 10 PM if you can. Ashwagandha is wonderful for deeper sleep too. Sweet dreams! 💤"""
        
        # Stress & Anxiety
        elif any(word in prompt_lower for word in ['stress', 'anxiety', 'worry', 'tension', 'nervous', 'overwhelmed']):
            return """Taking care of your mind is so important! Here's what helps:

Try this right now: breathe in for 4 counts, hold for 4, breathe out for 4. Just 5 minutes can shift everything!

Ashwagandha is amazing for stress (check with a practitioner first). Also, warm herbal teas and daily walks work wonders. You've got this! 💚"""
        
        # Immunity & Cold/Flu
        elif any(word in prompt_lower for word in ['immunity', 'immune', 'cold', 'flu', 'fever', 'cough', 'infection']):
            return """Boosting immunity naturally? Great question!

Turmeric milk (golden milk) is a powerhouse! Mix 1 tsp turmeric in warm milk with honey. Also, Chyawanprash in the morning is like a superhero for your immune system.

Stay warm, rest well, and sip on ginger-tulsi tea throughout the day. Your body knows how to heal - just give it support! 🌟"""
        
        # Weight Management
        elif any(word in prompt_lower for word in ['weight', 'obesity', 'fat', 'lose weight', 'diet', 'slim']):
            return """Weight management in Ayurveda is all about balance!

Start your day with warm lemon water - it kickstarts metabolism. Focus on whole, warm foods and avoid heavy dinners. Regular movement is key, even just 30-minute walks.

Triphala and honey in warm water before bed helps too. Remember, it's about feeling good, not just numbers! 🌸"""
        
        # Skin Health
        elif any(word in prompt_lower for word in ['skin', 'acne', 'pimple', 'rash', 'eczema', 'glow', 'complexion']):
            return """Beautiful skin starts from within!

Try turmeric-chickpea flour face mask (besan + turmeric + rose water) - it's a time-tested glow secret! Also, drink plenty of warm water and eat cooling foods like cucumber and coconut.

Neem is amazing for acne. And don't forget - good sleep = glowing skin! ✨"""
        
        # Hair Health
        elif any(word in prompt_lower for word in ['hair', 'hair fall', 'baldness', 'dandruff', 'scalp']):
            return """Let's get your hair healthy and happy!

Coconut oil massage once a week works wonders - warm it slightly and massage into your scalp. Amla and Bhringraj are traditional herbs for strong, lustrous hair.

Diet matters too: have sesame seeds, almonds, and leafy greens. Stay hydrated and manage stress. Your hair will thank you! 💆"""
        
        # Herbs & Remedies
        elif any(word in prompt_lower for word in ['ashwagandha', 'turmeric', 'triphala', 'tulsi', 'neem', 'amla', 'ginger', 'herb']):
            return """Ah, the wisdom of Ayurvedic herbs!

Each herb has unique benefits:
• Ashwagandha - Stress relief & energy
• Turmeric - Inflammation & immunity
• Triphala - Digestion & detox
• Tulsi - Respiratory & overall wellness

Start with one herb, be consistent, and listen to your body. Quality matters, so get them from trusted sources! 🌿"""
        
        # Doshas (Vata, Pitta, Kapha)
        elif any(word in prompt_lower for word in ['dosha', 'vata', 'pitta', 'kapha', 'constitution', 'prakriti']):
            return """Understanding your dosha is like having a personal wellness blueprint!

**Vata** (air): Creative, energetic - needs warmth & routine
**Pitta** (fire): Driven, focused - needs cooling & balance
**Kapha** (earth): Steady, calm - needs movement & stimulation

Most of us are a unique mix! I'd recommend seeing an Ayurvedic practitioner to discover your constitution. It's fascinating! 🌟"""
        
        # Seasonal Health (Ritucharya)
        elif any(word in prompt_lower for word in ['season', 'winter', 'summer', 'monsoon', 'spring', 'autumn']):
            return """Seasonal living (Ritucharya) is such a beautiful Ayurvedic concept!

Adjust your diet and lifestyle with the seasons:
• Summer: Cooling foods, lighter meals
• Winter: Warming spices, nourishing foods
• Monsoon: Warm, dry foods, boost immunity

Nature guides us - just tune in and adapt! Your body will feel the difference. 🍂☀️🌧️"""
        
        # General Ayurveda Questions
        elif any(word in prompt_lower for word in ['ayurveda', 'ayurvedic', 'what is', 'tell me about']):
            return """Welcome to the beautiful world of Ayurveda! 🙏

Ayurveda is 5,000+ years of wisdom about living in harmony with nature. It's all about understanding your unique body and creating balance through:
• Wholesome food
• Daily routines
• Herbal support
• Mind-body practices

It's not just about treating illness - it's about thriving! What specific area interests you? 🌿"""
        
        # Greetings
        elif any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'namaste', 'greetings']):
            return """Namaste! 🙏✨

I'm Astra, your Ayurvedic wellness companion! I'm here to share time-tested wisdom about natural health, herbs, lifestyle, and finding balance.

What's on your mind today? Ask me about digestion, sleep, stress, immunity, herbs, or anything wellness-related! Let's explore together. 🌿💚"""
        
        # Thank you / Appreciation
        elif any(word in prompt_lower for word in ['thank', 'thanks', 'appreciate', 'grateful']):
            return """You're so welcome! 💚

I'm happy to help on your wellness journey. Remember, small consistent steps create big changes!

Feel free to ask anything else. Wishing you vibrant health and peace! 🌿✨"""
        
        # Default Response - General Wellness
        else:
            return f"""Great question! Ayurveda has beautiful wisdom for this.

The key is understanding your unique body and working with it, not against it. Focus on warm, fresh foods, good sleep, staying hydrated, and managing stress.

I'd recommend chatting with an Ayurvedic practitioner for personalized guidance tailored to your constitution. Feel free to ask me anything else about Ayurvedic wellness! 🌿"""
    
    async def generate_streaming_response(
        self,
        prompt: str,
        language: str = "en",
        max_length: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True
    ):
        """Generate streaming response with typing effect"""
        
        # Check if question is Ayurveda-related
        if not language_manager.is_ayurveda_related(prompt, language):
            response = language_manager.get_non_ayurveda_response(language)
            # Stream the response word by word
            words = response.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                await asyncio.sleep(0.05)
            return
        
        # Get full response (from Llama model or fallback)
        full_response = await self.generate_response(
            prompt, language, max_length, temperature, top_p, top_k, do_sample
        )
        
        # Stream the response word by word with typing effect
        words = full_response.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield f" {word}"
            await asyncio.sleep(0.08)
