"""
Input Sanitization Module
Fixed Bug #20: Sanitize user inputs to prevent XSS and injection attacks
"""

import re
import logging
from typing import Optional, List, Dict, Any
import html

logger = logging.getLogger(__name__)


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input text
    
    - Strips HTML tags
    - Escapes special characters
    - Removes excessive whitespace
    - Optionally truncates to max length
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (None for no limit)
        
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Strip HTML tags (basic protection)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
        logger.warning(f"Text truncated to {max_length} characters")
    
    return text


def sanitize_name(name: str) -> str:
    """
    Sanitize person names
    
    - Allows letters, spaces, hyphens, apostrophes
    - Removes numbers and special characters
    - Capitalizes properly
    
    Args:
        name: Name to sanitize
        
    Returns:
        Sanitized name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Allow only letters, spaces, hyphens, and apostrophes
    name = re.sub(r"[^a-zA-Z\s\-']", '', name)
    
    # Remove excessive whitespace
    name = ' '.join(name.split())
    
    # Capitalize words
    name = name.title()
    
    return name.strip()


def sanitize_email(email: str) -> Optional[str]:
    """
    Sanitize and validate email address
    
    Args:
        email: Email to sanitize
        
    Returns:
        Sanitized email or None if invalid
    """
    if not email or not isinstance(email, str):
        return None
    
    # Basic email validation
    email = email.lower().strip()
    
    # Simple regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_pattern, email):
        return email
    
    logger.warning(f"Invalid email format: {email[:20]}...")
    return None


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number
    
    - Keeps only digits and +
    - Removes other characters
    
    Args:
        phone: Phone number to sanitize
        
    Returns:
        Sanitized phone number
    """
    if not phone or not isinstance(phone, str):
        return ""
    
    # Keep only digits and +
    phone = re.sub(r'[^0-9+]', '', phone)
    
    return phone.strip()


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize URL and validate protocol
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL or None if invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Only allow http and https protocols
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL protocol: {url[:50]}")
        return None
    
    # Basic URL validation
    url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if re.match(url_pattern, url):
        return url
    
    logger.warning(f"Invalid URL format: {url[:50]}")
    return None


def sanitize_patient_id(patient_id: str) -> str:
    """
    Sanitize patient ID
    
    - Allows only alphanumeric and underscore
    - Converts to uppercase
    
    Args:
        patient_id: Patient ID to sanitize
        
    Returns:
        Sanitized patient ID
    """
    if not patient_id or not isinstance(patient_id, str):
        return ""
    
    # Keep only alphanumeric and underscore
    patient_id = re.sub(r'[^a-zA-Z0-9_]', '', patient_id)
    
    return patient_id.upper().strip()


def sanitize_dict(data: Dict[str, Any], text_fields: List[str]) -> Dict[str, Any]:
    """
    Sanitize multiple fields in a dictionary
    
    Args:
        data: Dictionary to sanitize
        text_fields: List of field names to sanitize
        
    Returns:
        Dictionary with sanitized fields
    """
    sanitized = data.copy()
    
    for field in text_fields:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitize_text(sanitized[field])
    
    return sanitized


def sanitize_message(message: str, max_length: int = 5000) -> str:
    """
    Sanitize chat messages and user content
    
    - Removes HTML
    - Escapes special characters
    - Limits length
    - Preserves newlines (converted to safe format)
    
    Args:
        message: Message to sanitize
        max_length: Maximum message length
        
    Returns:
        Sanitized message
    """
    if not message or not isinstance(message, str):
        return ""
    
    # Strip HTML tags
    message = re.sub(r'<[^>]+>', '', message)
    
    # Escape HTML entities
    message = html.escape(message)
    
    # Normalize whitespace but preserve newlines
    lines = message.split('\n')
    lines = [' '.join(line.split()) for line in lines]
    message = '\n'.join(lines)
    
    # Remove excessive newlines (max 2 consecutive)
    message = re.sub(r'\n{3,}', '\n\n', message)
    
    # Truncate if needed
    if len(message) > max_length:
        message = message[:max_length].rstrip()
        logger.warning(f"Message truncated to {max_length} characters")
    
    return message.strip()


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal)
    
    Args:
        filename: Filename to check
        
    Returns:
        True if safe, False otherwise
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        logger.warning(f"Unsafe filename detected: {filename}")
        return False
    
    # Check for allowed characters (alphanumeric, dash, underscore, dot)
    if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
        logger.warning(f"Invalid characters in filename: {filename}")
        return False
    
    return True


def sanitize_json_string(json_str: str) -> str:
    """
    Sanitize JSON string to prevent injection
    
    Args:
        json_str: JSON string to sanitize
        
    Returns:
        Sanitized JSON string
    """
    if not json_str or not isinstance(json_str, str):
        return ""
    
    # Remove any potential script tags
    json_str = re.sub(r'<script[^>]*>.*?</script>', '', json_str, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove any potential event handlers
    json_str = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', json_str, flags=re.IGNORECASE)
    
    return json_str.strip()
