"""
Model Service - Abstraction layer for AI model inference
Avoids circular dependencies and provides clean interface for AI chat
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # "user" or "assistant"
    content: str


class ModelService:
    """
    Service for AI model inference with proper abstraction
    Singleton pattern to avoid circular dependencies
    """
    
    _instance: Optional['ModelService'] = None
    _model_inference = None
    
    def __init__(self):
        """Private constructor - use get_instance()"""
        pass
    
    @classmethod
    def get_instance(cls) -> 'ModelService':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_model_inference(cls, model_inference):
        """Set the model inference instance (called from main_enhanced.py)"""
        cls._model_inference = model_inference
        logger.info("✅ ModelService configured with model inference")
    
    async def generate_response(
        self,
        prompt: str,
        language: str = "en",
        context: Optional[str] = None,
        chat_history: Optional[List[ChatMessage]] = None,
        max_length: int = 500
    ) -> str:
        """
        Generate AI response with optional conversation history
        
        Args:
            prompt: The user's message or prompt
            language: Target language
            context: Additional context (journey info, etc.)
            chat_history: Previous conversation messages for context
            max_length: Maximum response length
        
        Returns:
            AI-generated response string
        """
        if not self._model_inference:
            # Fallback response when model not available
            logger.warning("Model not available, using fallback response")
            return self._get_fallback_response(prompt, language)
        
        try:
            # Build context-aware prompt with conversation history
            full_prompt = self._build_context_prompt(
                prompt=prompt,
                context=context,
                chat_history=chat_history,
                language=language
            )
            
            # Generate response using the model
            response = await self._model_inference.generate_response(
                prompt=full_prompt,
                language=language,
                context=context or ""
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(prompt, language)
    
    def _build_context_prompt(
        self,
        prompt: str,
        context: Optional[str],
        chat_history: Optional[List[ChatMessage]],
        language: str
    ) -> str:
        """Build a context-aware prompt with conversation history"""
        
        parts = []
        
        # Add context if provided
        if context:
            parts.append(f"Context: {context}")
        
        # Add conversation history
        if chat_history and len(chat_history) > 0:
            parts.append("\nRecent conversation:")
            # Include last 5 messages for context
            for msg in chat_history[-5:]:
                role = "Patient" if msg.role == "user" else "Astra"
                parts.append(f"{role}: {msg.content}")
        
        # Add current prompt
        parts.append(f"\nPatient's current message: {prompt}")
        
        # Add language instruction
        parts.append(f"\nRespond in {language} language with warm, supportive Ayurvedic guidance.")
        
        return "\n".join(parts)
    
    def _get_fallback_response(self, prompt: str, language: str) -> str:
        """Get a fallback response when model is unavailable"""
        
        # Simple keyword-based fallback responses
        prompt_lower = prompt.lower()
        
        if language == "hi":
            return "मैं आपकी मदद करने के लिए यहाँ हूँ। कृपया अपनी समस्या के बारे में और बताएं।"
        elif language == "ta":
            return "நான் உங்களுக்கு உதவ இங்கே இருக்கிறேன். உங்கள் பிரச்சினையை மேலும் விவரிக்கவும்."
        else:
            return "I'm here to support you on your wellness journey. Please tell me more about how you're feeling, and I'll provide personalized Ayurvedic guidance."
    
    def is_model_available(self) -> bool:
        """Check if AI model is available"""
        return self._model_inference is not None


# Global singleton instance
model_service = ModelService.get_instance()
