"""
Enhanced Input Validation
Comprehensive validation for all user inputs
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class InputValidator:
    """Comprehensive input validation"""
    
    # Limits
    MAX_MESSAGE_LENGTH = 2000
    MAX_HEALTH_CONCERN_LENGTH = 500
    MAX_NAME_LENGTH = 100
    MIN_MESSAGE_LENGTH = 1
    
    # Patterns
    SQL_INJECTION_PATTERN = re.compile(
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bEXEC\b|--;|/\*|\*/)",
        re.IGNORECASE
    )
    
    XSS_PATTERN = re.compile(
        r"<script|javascript:|onerror=|onload=|<iframe|<object|<embed",
        re.IGNORECASE
    )
    
    @classmethod
    def validate_message(
        cls,
        message: str,
        allow_empty: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate chat message
        
        Returns:
            (is_valid, sanitized_message, error_message)
        """
        if not message:
            if allow_empty:
                return True, "", None
            return False, None, "Message cannot be empty"
        
        # Check length
        if len(message) < cls.MIN_MESSAGE_LENGTH:
            return False, None, "Message too short"
        
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, None, f"Message too long (max {cls.MAX_MESSAGE_LENGTH} characters)"
        
        # Check for SQL injection
        if cls.SQL_INJECTION_PATTERN.search(message):
            logger.warning(f"⚠️ Potential SQL injection detected: {message[:50]}")
            return False, None, "Invalid message content detected"
        
        # Check for XSS
        if cls.XSS_PATTERN.search(message):
            logger.warning(f"⚠️ Potential XSS detected: {message[:50]}")
            return False, None, "Invalid message content detected"
        
        # Sanitize
        sanitized = cls._sanitize_text(message)
        
        return True, sanitized, None
    
    @classmethod
    def validate_health_concern(
        cls,
        concern: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate health concern
        
        Returns:
            (is_valid, sanitized_concern, error_message)
        """
        if not concern or not concern.strip():
            return False, None, "Health concern cannot be empty"
        
        if len(concern) > cls.MAX_HEALTH_CONCERN_LENGTH:
            return False, None, f"Health concern too long (max {cls.MAX_HEALTH_CONCERN_LENGTH} characters)"
        
        # Basic sanitization
        sanitized = cls._sanitize_text(concern)
        
        return True, sanitized, None
    
    @classmethod
    def validate_patient_id(
        cls,
        patient_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate patient ID
        
        Returns:
            (is_valid, error_message)
        """
        if not patient_id or not patient_id.strip():
            return False, "Patient ID cannot be empty"
        
        # Only allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', patient_id):
            return False, "Invalid patient ID format"
        
        if len(patient_id) > 100:
            return False, "Patient ID too long"
        
        return True, None
    
    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        """Basic text sanitization"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @classmethod
    def validate_language_code(
        cls,
        language: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate language code
        
        Returns:
            (is_valid, error_message)
        """
        valid_languages = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa']
        
        if not language:
            return True, None  # Default will be used
        
        if language.lower() not in valid_languages:
            return False, f"Unsupported language. Supported: {', '.join(valid_languages)}"
        
        return True, None

# Global instance
input_validator = InputValidator()
