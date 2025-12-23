"""
Astra Tone Mapper - Empathetic Language Style Mapping

This module maps detected emotions to appropriate response tones.
It affects HOW Astra speaks, not WHAT Astra decides.

IMPORTANT: Tone mapping is purely linguistic, not medical.
"""

import logging
from typing import Dict
from .emotion_detector import EmotionCategory

logger = logging.getLogger(__name__)


class ResponseTone:
    """Response tone definitions"""
    EMPATHETIC = "empathetic"
    CALM = "calm"
    NEUTRAL = "neutral"
    URGENT = "urgent"
    ENCOURAGING = "encouraging"
    EDUCATIONAL = "educational"


class ToneMapper:
    """
    Maps emotions to appropriate response tones.
    
    RULES:
    - Affects language style ONLY
    - Does NOT override safety or rules
    - Does NOT make medical decisions
    - Purely for empathetic communication
    """
    
    def __init__(self):
        self.emotion_tone_map = self._build_emotion_tone_map()
        self.tone_templates = self._build_tone_templates()
        logger.info("✅ Tone Mapper initialized")
    
    def _build_emotion_tone_map(self) -> Dict[str, str]:
        """Map emotions to tones"""
        return {
            EmotionCategory.HAPPY.value: ResponseTone.ENCOURAGING,
            EmotionCategory.ANXIOUS.value: ResponseTone.CALM,
            EmotionCategory.FRUSTRATED.value: ResponseTone.EMPATHETIC,
            EmotionCategory.CURIOUS.value: ResponseTone.EDUCATIONAL,
            EmotionCategory.GRATEFUL.value: ResponseTone.ENCOURAGING,
            EmotionCategory.CONCERNED.value: ResponseTone.CALM,
            EmotionCategory.CONFUSED.value: ResponseTone.EDUCATIONAL,
            EmotionCategory.NEUTRAL.value: ResponseTone.NEUTRAL,
        }
    
    def _build_tone_templates(self) -> Dict[str, Dict]:
        """Build tone-specific language templates"""
        return {
            ResponseTone.EMPATHETIC: {
                "prefix": ["I understand how you feel.", "I hear you.", "That sounds challenging."],
                "style": "warm, understanding, supportive",
                "emoji": "🌿",
            },
            ResponseTone.CALM: {
                "prefix": ["Let me help you with that.", "Take a deep breath.", "It's okay."],
                "style": "reassuring, peaceful, balanced",
                "emoji": "🧘",
            },
            ResponseTone.NEUTRAL: {
                "prefix": ["", "Here's what I can tell you:", "Let me explain:"],
                "style": "professional, clear, informative",
                "emoji": "",
            },
            ResponseTone.URGENT: {
                "prefix": ["This is important:", "Please note:", "Immediate action needed:"],
                "style": "direct, action-oriented, clear",
                "emoji": "⚠️",
            },
            ResponseTone.ENCOURAGING: {
                "prefix": ["That's great!", "Well done!", "You're doing well!"],
                "style": "positive, motivating, supportive",
                "emoji": "✨",
            },
            ResponseTone.EDUCATIONAL: {
                "prefix": ["Let me explain:", "Here's how it works:", "To answer your question:"],
                "style": "clear, informative, patient",
                "emoji": "📚",
            },
        }
    
    def map_tone(self, emotion: str, capability: str) -> str:
        """
        Map emotion and capability to appropriate tone.
        
        Args:
            emotion: Detected emotion
            capability: Current capability being executed
        
        Returns:
            Response tone (string)
        """
        # Emergency always uses urgent tone
        if capability == "EMERGENCY_REDIRECT":
            return ResponseTone.URGENT
        
        # Map emotion to tone
        tone = self.emotion_tone_map.get(emotion, ResponseTone.NEUTRAL)
        
        logger.info("🎨 Tone mapped: %s (emotion: %s, capability: %s)", 
                   tone, emotion, capability)
        
        return tone
    
    def apply_tone(self, response: str, tone: str, add_prefix: bool = True) -> str:
        """
        Apply tone to response text.
        
        Args:
            response: Original response text
            tone: Tone to apply
            add_prefix: Whether to add tone-specific prefix
        
        Returns:
            Response with tone applied
        """
        if tone not in self.tone_templates:
            return response
        
        template = self.tone_templates[tone]
        
        # Build toned response
        toned_response = response
        
        # Add prefix if requested
        if add_prefix and template["prefix"]:
            import random
            prefix = random.choice(template["prefix"])
            if prefix:
                toned_response = f"{prefix} {toned_response}"
        
        # Add emoji if appropriate
        emoji = template.get("emoji", "")
        if emoji and not response.startswith(emoji):
            toned_response = f"{emoji} {toned_response}"
        
        logger.info("🎨 Tone applied: %s", tone)
        return toned_response
    
    def get_tone_guidelines(self, tone: str) -> str:
        """
        Get style guidelines for a tone (for AI prompt).
        
        Args:
            tone: Tone name
        
        Returns:
            Style guidelines string
        """
        if tone not in self.tone_templates:
            return "Be professional and clear."
        
        template = self.tone_templates[tone]
        return f"Use a {template['style']} tone."
