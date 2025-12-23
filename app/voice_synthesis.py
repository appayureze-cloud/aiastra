"""
Voice synthesis and TTS functionality for Astra
"""

import os
import logging
import asyncio
import hashlib
import io
from typing import Optional, Dict, Any
from pathlib import Path

# TTS libraries (will be optional imports)
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

from app.voice_models import VoiceType, AudioFormat, TTSRequest

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """Handles text-to-speech synthesis with multiple backends"""
    
    def __init__(self):
        self.cache_dir = Path("audio_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.tts_engine = None
        self._init_engines()
    
    def _init_engines(self):
        """Initialize available TTS engines"""
        if HAS_PYTTSX3:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_pyttsx3()
                logger.info("pyttsx3 TTS engine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}")
                self.tts_engine = None
        
        if not HAS_PYTTSX3 and not HAS_GTTS:
            logger.warning("No TTS engines available. Audio synthesis will be simulated.")
    
    def _configure_pyttsx3(self):
        """Configure pyttsx3 engine settings"""
        if not self.tts_engine:
            return
        
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Prefer female voice for calm effect
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        
        # Set calm, slower speech rate
        self.tts_engine.setProperty('rate', 160)  # Slower than default 200
        self.tts_engine.setProperty('volume', 0.8)
    
    def _get_cache_key(self, text: str, voice: VoiceType, language: str) -> str:
        """Generate cache key for audio file"""
        content = f"{text}_{voice}_{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_audio(self, cache_key: str, format: AudioFormat) -> Optional[Path]:
        """Check if audio file exists in cache"""
        audio_file = self.cache_dir / f"{cache_key}.{format.value}"
        return audio_file if audio_file.exists() else None
    
    async def synthesize_speech(self, request: TTSRequest) -> Dict[str, Any]:
        """Synthesize speech from text"""
        cache_key = self._get_cache_key(request.text, request.voice, request.language)
        cached_file = self._get_cached_audio(cache_key, request.format)
        
        if cached_file:
            logger.info(f"Using cached audio: {cached_file}")
            return {
                "audio_path": str(cached_file),
                "duration": await self._get_audio_duration(cached_file),
                "cached": True
            }
        
        # Generate new audio
        audio_path = await self._generate_audio(request, cache_key)
        duration = await self._get_audio_duration(audio_path)
        
        return {
            "audio_path": str(audio_path),
            "duration": duration,
            "cached": False
        }
    
    async def _generate_audio(self, request: TTSRequest, cache_key: str) -> Path:
        """Generate audio file using available TTS engine"""
        output_path = self.cache_dir / f"{cache_key}.{request.format.value}"
        
        if HAS_GTTS and request.language in ['en', 'hi', 'es', 'fr', 'de']:
            # Use Google TTS for supported languages
            await self._generate_with_gtts(request, output_path)
        elif HAS_PYTTSX3 and self.tts_engine:
            # Use pyttsx3 for local generation
            await self._generate_with_pyttsx3(request, output_path)
        else:
            # Fallback: create silent audio file
            await self._generate_silent_audio(request, output_path)
        
        return output_path
    
    async def _generate_with_gtts(self, request: TTSRequest, output_path: Path):
        """Generate audio using Google Text-to-Speech"""
        def _gtts_synthesis():
            tts = gTTS(
                text=request.text,
                lang=request.language,
                slow=request.speed < 1.0
            )
            tts.save(str(output_path))
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _gtts_synthesis)
        logger.info(f"Generated audio with gTTS: {output_path}")
    
    async def _generate_with_pyttsx3(self, request: TTSRequest, output_path: Path):
        """Generate audio using pyttsx3"""
        def _pyttsx3_synthesis():
            if self.tts_engine:
                self.tts_engine.setProperty('rate', int(200 * request.speed))
                self.tts_engine.save_to_file(request.text, str(output_path))
                self.tts_engine.runAndWait()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _pyttsx3_synthesis)
        logger.info(f"Generated audio with pyttsx3: {output_path}")
    
    async def _generate_silent_audio(self, request: TTSRequest, output_path: Path):
        """Generate a silent audio file as fallback"""
        # Create a minimal WAV file with silence
        # This is a placeholder - in production you'd want proper silence generation
        duration_seconds = len(request.text.split()) * 0.6  # Estimate speaking time
        
        # For now, create an empty file to indicate synthesis was attempted
        output_path.touch()
        logger.warning(f"Generated placeholder audio file: {output_path}")
    
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file"""
        try:
            # For now, estimate duration based on text length
            # In production, you'd use librosa or similar to get actual duration
            if audio_path.stat().st_size == 0:
                return 0.0
            
            # Rough estimation: average speaking rate is 150 words per minute
            with open(audio_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content:
                # For binary audio files, estimate from file size
                file_size = audio_path.stat().st_size
                return max(1.0, file_size / 16000)  # Rough estimate
            
            word_count = len(content.split())
            return max(1.0, (word_count / 150) * 60)  # Convert to seconds
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 5.0  # Default fallback

# Global synthesizer instance
voice_synthesizer = VoiceSynthesizer()