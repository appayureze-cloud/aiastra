"""
ElevenLabs Voice Service Integration
Text-to-Speech for AI Companion responses
"""

import os
import logging
import httpx
from typing import Optional, BinaryIO
import base64

logger = logging.getLogger(__name__)

class VoiceService:
    """ElevenLabs TTS integration"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.api_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning("⚠️ ElevenLabs API key not configured. Voice features disabled.")
        else:
            logger.info("✅ ElevenLabs Voice Service initialized")
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en"
    ) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text: Text to convert
            voice_id: ElevenLabs voice ID (optional)
            language: Language code (en/hi/ta)
        
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        if not self.api_key:
            logger.warning("ElevenLabs not configured")
            return None
        
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided")
            return None
        
        # Limit text length (ElevenLabs has limits)
        if len(text) > 5000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 5000")
            text = text[:5000]
        
        voice_id = voice_id or self.default_voice_id
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
                
                # ElevenLabs API payload
                payload = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",  # Supports multiple languages
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"✅ Generated speech: {len(text)} chars -> {len(response.content)} bytes")
                    return response.content
                else:
                    logger.error(f"❌ ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("ElevenLabs request timeout")
            return None
        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            return None
    
    async def text_to_speech_base64(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Convert text to speech and return as base64 string
        Useful for API responses
        """
        audio_bytes = await self.text_to_speech(text, voice_id, language)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    async def get_available_voices(self) -> Optional[list]:
        """Get list of available voices from ElevenLabs"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/voices"
                headers = {"xi-api-key": self.api_key}
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
                else:
                    logger.error(f"Failed to fetch voices: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if voice service is available"""
        return bool(self.api_key)

# Global instance
voice_service = VoiceService()
