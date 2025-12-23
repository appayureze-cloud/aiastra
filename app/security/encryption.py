"""
Encryption utilities for securing sensitive patient data
Implements end-to-end encryption for DISHA compliance
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as PBKDF2
import base64
import os
import json
from typing import Any, Dict, Optional
import hashlib

class DataEncryption:
    """
    End-to-end encryption for sensitive health data
    Uses Fernet (symmetric encryption) with key derivation
    """
    
    def __init__(self):
        # Get master key from environment (optional - use default for development)
        master_key = os.getenv('DATA_ENCRYPTION_KEY')
        if not master_key:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("DATA_ENCRYPTION_KEY not set. Using default key for development. NOT FOR PRODUCTION!")
            master_key = "development-key-not-for-production-use-32-bytes-minimum"
        
        self.master_key = master_key.encode()
        self._cipher = None
    
    def _get_cipher(self, salt: Optional[bytes] = None):
        """Get Fernet cipher with key derivation"""
        if salt is None:
            salt = os.urandom(16)
        
        # Derive key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key), salt
    
    def encrypt_data(self, data: Any) -> str:
        """
        Encrypt any data (dict, string, etc.)
        Returns: base64 encoded encrypted data with salt
        """
        # Convert to JSON string
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Get cipher with new salt
        cipher, salt = self._get_cipher()
        
        # Encrypt data
        encrypted = cipher.encrypt(data.encode())
        
        # Combine salt + encrypted data
        combined = salt + encrypted
        
        # Return base64 encoded
        return base64.b64encode(combined).decode()
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """
        Decrypt data and return original format
        """
        try:
            # Decode base64
            combined = base64.b64decode(encrypted_data.encode())
            
            # Extract salt and encrypted data
            salt = combined[:16]
            encrypted = combined[16:]
            
            # Get cipher with same salt
            cipher, _ = self._get_cipher(salt)
            
            # Decrypt
            decrypted = cipher.decrypt(encrypted).decode()
            
            # Try to parse JSON
            try:
                return json.loads(decrypted)
            except:
                return decrypted
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def hash_pii(self, data: str) -> str:
        """
        One-way hash for PII (phone, email, etc.)
        Used for indexing without storing plaintext
        """
        return hashlib.sha256(data.encode()).hexdigest()


class FieldLevelEncryption:
    """
    Field-level encryption for database models
    Encrypts specific sensitive fields
    """
    
    SENSITIVE_FIELDS = {
        'phone_number',
        'email',
        'medical_history',
        'prescriptions',
        'lab_reports',
        'doctor_notes',
        'symptoms',
        'allergies',
        'current_medications',
        'personal_notes'
    }
    
    def __init__(self):
        self.encryptor = DataEncryption()
    
    def encrypt_fields(self, data: Dict[str, Any], fields: Optional[set] = None) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary
        fields: set of field names to encrypt (default: all sensitive fields)
        """
        if fields is None:
            fields = self.SENSITIVE_FIELDS
        
        encrypted_data = data.copy()
        
        for field in fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encryptor.encrypt_data(encrypted_data[field])
                # Also create a searchable hash
                encrypted_data[f"{field}_hash"] = self.encryptor.hash_pii(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_fields(self, data: Dict[str, Any], fields: Optional[set] = None) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary
        """
        if fields is None:
            fields = self.SENSITIVE_FIELDS
        
        decrypted_data = data.copy()
        
        for field in fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    decrypted_data[field] = self.encryptor.decrypt_data(decrypted_data[field])
                except:
                    # Field might not be encrypted
                    pass
        
        return decrypted_data


# Singleton instances
data_encryptor = DataEncryption()
field_encryptor = FieldLevelEncryption()
