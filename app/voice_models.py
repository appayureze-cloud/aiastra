"""
Voice integration models for TTS and audio generation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class VoiceType(str, Enum):
    """Available voice types for TTS"""
    CALM_FEMALE = "calm_female"
    WARM_MALE = "warm_male" 
    SOOTHING_NEUTRAL = "soothing_neutral"

class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"

class TTSRequest(BaseModel):
    """Text-to-Speech request model"""
    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    voice: VoiceType = Field(default=VoiceType.CALM_FEMALE, description="Voice type to use")
    language: str = Field(default="en", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Pitch adjustment")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Audio output format")

class MeditationRequest(BaseModel):
    """Guided meditation generation request"""
    focus: Literal["stress", "sleep", "energy", "anxiety", "concentration"] = Field(
        ..., description="Focus area for meditation"
    )
    duration: int = Field(default=5, ge=1, le=30, description="Duration in minutes")
    user_dosha: Optional[Literal["vata", "pitta", "kapha"]] = Field(
        None, description="User's primary dosha"
    )
    experience_level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner", description="User's meditation experience"
    )
    include_mantra: bool = Field(default=False, description="Include Sanskrit mantras")

class BreathingExerciseRequest(BaseModel):
    """Breathing exercise audio generation request"""
    technique: Literal["4-7-8", "box_breathing", "nadi_shodhana", "bhramari"] = Field(
        ..., description="Breathing technique type"
    )
    duration: int = Field(default=5, ge=1, le=20, description="Duration in minutes")
    guidance_frequency: Literal["continuous", "periodic", "minimal"] = Field(
        default="periodic", description="How often to provide voice guidance"
    )
    background_sound: Optional[Literal["om", "nature", "silence"]] = Field(
        None, description="Background sound during exercise"
    )

class AudioResponse(BaseModel):
    """Audio generation response"""
    audio_url: str = Field(..., description="URL to access the generated audio")
    duration: float = Field(..., description="Audio duration in seconds")
    format: AudioFormat = Field(..., description="Audio format")
    text_content: Optional[str] = Field(None, description="Original text content")

class MeditationResponse(BaseModel):
    """Meditation generation response"""
    script: str = Field(..., description="Generated meditation script")
    audio_url: str = Field(..., description="URL to meditation audio")
    duration: float = Field(..., description="Total duration in minutes")
    sections: List[str] = Field(..., description="Meditation sections/phases")
    mantras: Optional[List[str]] = Field(None, description="Sanskrit mantras included")

class BreathingResponse(BaseModel):
    """Breathing exercise response"""
    technique_name: str = Field(..., description="Name of breathing technique")
    instructions: str = Field(..., description="Written instructions")
    audio_url: str = Field(..., description="URL to guided audio")
    duration: float = Field(..., description="Exercise duration in minutes")
    pattern: str = Field(..., description="Breathing pattern description")