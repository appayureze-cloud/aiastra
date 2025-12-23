"""
Astra Consent Manager - DISHA Compliant Consent Verification

This module manages explicit, purpose-specific consent for:
- Document uploads and analysis
- Lab report interpretation
- Prescription interpretation
- RAG memory storage and retrieval
- Health timeline access

Compliance: DISHA, IT Act 2000, Telemedicine Practice Guidelines 2020
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ConsentPurpose(Enum):
    """Enumeration of consent purposes"""
    ASTRA_USAGE = "astra_usage"
    DOCUMENT_UPLOAD = "document_upload"
    LAB_REPORT_ANALYSIS = "lab_report_analysis"
    PRESCRIPTION_INTERPRETATION = "prescription_interpretation"
    RAG_MEMORY_STORAGE = "rag_memory_storage"
    HEALTH_TIMELINE_ACCESS = "health_timeline_access"
    TELEMEDICINE_CONSULTATION = "telemedicine_consultation"
    FAMILY_PROFILE_ACCESS = "family_profile_access"


class ConsentStatus(Enum):
    """Enumeration of consent statuses"""
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    NOT_REQUESTED = "not_requested"


class ConsentManager:
    """
    Consent management system for DISHA compliance.
    
    RULES:
    - Explicit consent required for sensitive operations
    - Purpose-specific consent (cannot be reused)
    - Time-stamped and revocable
    - Profile-specific (isolated per family member)
    - Immutable audit trail
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize consent manager.
        
        Args:
            db_connection: Database connection (Supabase client)
        """
        self.db = db_connection
        self.consent_cache = {}  # In-memory cache for performance
        logger.info("✅ Consent Manager initialized")
    
    async def verify_consent(
        self,
        user_id: str,
        profile_id: str,
        capability: str,
        purpose: Optional[str] = None
    ) -> Dict:
        """
        Verify if user has granted consent for a capability.
        
        Args:
            user_id: User's account ID
            profile_id: Specific profile ID (for family profiles)
            capability: Capability being executed
            purpose: Optional specific purpose (overrides capability default)
        
        Returns:
            {
                "granted": bool,
                "consent_id": str,
                "granted_at": datetime,
                "expires_at": datetime,
                "purpose": str,
                "revocable": bool,
                "status": ConsentStatus
            }
        """
        # ASTRA 2.0.0 MANDATORY CONSENT CHECK
        # Every Astra interaction requires astra_usage consent
        astra_consent = await self.verify_astra_consent(user_id, profile_id)
        if not astra_consent["granted"]:
            return astra_consent

        # Map capability to consent purpose
        if not purpose:
            purpose = self._map_capability_to_purpose(capability)
        
        # Check if consent is required for this capability
        if not purpose:
            # No additional consent required beyond astra_usage
            return {
                "granted": True,
                "consent_id": astra_consent.get("consent_id"),
                "granted_at": astra_consent.get("granted_at"),
                "expires_at": astra_consent.get("expires_at"),
                "purpose": "astra_usage",
                "revocable": True,
                "status": ConsentStatus.GRANTED.value,
                "message": "Astra usage consent is valid"
            }
        
        # Check cache first for specific purpose
        cache_key = f"{user_id}:{profile_id}:{purpose}"
        if cache_key in self.consent_cache:
            cached = self.consent_cache[cache_key]
            if not self._is_expired(cached):
                logger.info("✅ Consent found in cache: %s", purpose)
                return cached
        
        # Query database for specific consent
        consent_record = await self._get_consent_from_db(user_id, profile_id, purpose)
        
        if not consent_record:
            logger.warning("⚠️ No consent found for %s (user: %s, profile: %s)", 
                         purpose, user_id, profile_id)
            return {
                "granted": False,
                "consent_id": None,
                "granted_at": None,
                "expires_at": None,
                "purpose": purpose,
                "revocable": True,
                "status": ConsentStatus.NOT_REQUESTED.value,
                "message": f"Purpose-specific consent required for {purpose}. Please grant consent in your profile settings."
            }
        
        # Check if consent is active and not revoked
        if consent_record.get('revoked_at'):
            logger.warning("⚠️ Consent revoked for %s", purpose)
            return {
                "granted": False,
                "consent_id": consent_record.get('id'),
                "granted_at": consent_record.get('granted_at'),
                "expires_at": consent_record.get('expires_at'),
                "purpose": purpose,
                "revocable": True,
                "status": ConsentStatus.REVOKED.value,
                "message": "Consent has been revoked. Please grant consent again if needed."
            }
        
        # Check if consent is expired
        if self._is_expired(consent_record):
            logger.warning("⚠️ Consent expired for %s", purpose)
            return {
                "granted": False,
                "consent_id": consent_record.get('id'),
                "granted_at": consent_record.get('granted_at'),
                "expires_at": consent_record.get('expires_at'),
                "purpose": purpose,
                "revocable": True,
                "status": ConsentStatus.EXPIRED.value,
                "message": "Consent has expired. Please renew consent."
            }
        
        # Consent is valid
        result = {
            "granted": True,
            "consent_id": consent_record.get('id'),
            "granted_at": consent_record.get('granted_at'),
            "expires_at": consent_record.get('expires_at'),
            "purpose": purpose,
            "revocable": True,
            "status": ConsentStatus.GRANTED.value,
            "message": "Consent is active and valid"
        }
        
        # Cache the result
        self.consent_cache[cache_key] = result
        
        logger.info("✅ Consent verified for %s", purpose)
        return result

    async def verify_astra_consent(self, user_id: str, profile_id: str) -> Dict:
        """Verify mandatory general Astra usage consent (ASTRA 2.0.0)"""
        purpose = ConsentPurpose.ASTRA_USAGE.value
        
        # Check cache
        cache_key = f"{user_id}:{profile_id}:{purpose}"
        if cache_key in self.consent_cache:
            cached = self.consent_cache[cache_key]
            if not self._is_expired(cached):
                return cached
                
        # Query DB
        consent_record = await self._get_consent_from_db(user_id, profile_id, purpose)
        
        if not consent_record:
            return {
                "granted": False,
                "purpose": purpose,
                "status": ConsentStatus.NOT_REQUESTED.value,
                "message": (
                    "Astra is a wellness and Ayurvedic knowledge companion. "
                    "It does not provide medical diagnosis or treatment. "
                    "All medical decisions must be taken by a qualified Ayurvedic doctor. "
                    "Please grant consent to Astra's terms to continue."
                )
            }
            
        if consent_record.get('revoked_at') or self._is_expired(consent_record):
            return {
                "granted": False,
                "purpose": purpose,
                "status": ConsentStatus.REVOKED.value if consent_record.get('revoked_at') else ConsentStatus.EXPIRED.value,
                "message": "Your Astra usage consent has expired or been revoked. Please re-grant consent to continue."
            }
            
        result = {
            "granted": True,
            "consent_id": consent_record.get('id'),
            "granted_at": consent_record.get('granted_at'),
            "expires_at": consent_record.get('expires_at'),
            "purpose": purpose,
            "revocable": True,
            "status": ConsentStatus.GRANTED.value,
            "message": "Astra usage consent is valid"
        }
        
        self.consent_cache[cache_key] = result
        return result
    
    async def grant_consent(
        self,
        user_id: str,
        profile_id: str,
        purpose: str,
        duration_days: int = 365,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Grant consent for a specific purpose.
        
        Args:
            user_id: User's account ID
            profile_id: Specific profile ID
            purpose: Purpose of consent
            duration_days: How long consent is valid (default: 1 year)
            metadata: Optional metadata (e.g., IP address, device info)
        
        Returns:
            {
                "success": bool,
                "consent_id": str,
                "granted_at": datetime,
                "expires_at": datetime,
                "message": str
            }
        """
        granted_at = datetime.utcnow()
        expires_at = granted_at + timedelta(days=duration_days)
        
        consent_data = {
            "user_id": user_id,
            "profile_id": profile_id,
            "purpose": purpose,
            "granted": True,
            "granted_at": granted_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "revoked_at": None,
            "is_active": True,
            "metadata": metadata or {}
        }
        
        # Save to database
        consent_id = await self._save_consent_to_db(consent_data)
        
        if consent_id:
            # Invalidate cache
            cache_key = f"{user_id}:{profile_id}:{purpose}"
            if cache_key in self.consent_cache:
                del self.consent_cache[cache_key]
            
            logger.info("✅ Consent granted: %s for user %s (profile: %s)", 
                       purpose, user_id, profile_id)
            
            return {
                "success": True,
                "consent_id": consent_id,
                "granted_at": granted_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "message": f"Consent granted for {purpose}"
            }
        else:
            logger.error("❌ Failed to grant consent for %s", purpose)
            return {
                "success": False,
                "consent_id": None,
                "granted_at": None,
                "expires_at": None,
                "message": "Failed to grant consent"
            }
    
    async def revoke_consent(
        self,
        user_id: str,
        profile_id: str,
        purpose: str
    ) -> Dict:
        """
        Revoke previously granted consent.
        
        Args:
            user_id: User's account ID
            profile_id: Specific profile ID
            purpose: Purpose of consent to revoke
        
        Returns:
            {
                "success": bool,
                "revoked_at": datetime,
                "message": str
            }
        """
        revoked_at = datetime.utcnow()
        
        # Update database
        success = await self._revoke_consent_in_db(user_id, profile_id, purpose, revoked_at)
        
        if success:
            # Invalidate cache
            cache_key = f"{user_id}:{profile_id}:{purpose}"
            if cache_key in self.consent_cache:
                del self.consent_cache[cache_key]
            
            logger.info("✅ Consent revoked: %s for user %s (profile: %s)", 
                       purpose, user_id, profile_id)
            
            return {
                "success": True,
                "revoked_at": revoked_at.isoformat(),
                "message": f"Consent revoked for {purpose}"
            }
        else:
            logger.error("❌ Failed to revoke consent for %s", purpose)
            return {
                "success": False,
                "revoked_at": None,
                "message": "Failed to revoke consent"
            }
    
    async def get_all_consents(
        self,
        user_id: str,
        profile_id: str
    ) -> List[Dict]:
        """
        Get all consents for a user profile.
        
        Args:
            user_id: User's account ID
            profile_id: Specific profile ID
        
        Returns:
            List of consent records
        """
        if not self.db:
            logger.warning("⚠️ Database not connected, returning empty list")
            return []
        
        try:
            # Query all consents for this profile
            # Implementation depends on your database (Supabase, PostgreSQL, etc.)
            # This is a placeholder
            consents = []
            
            logger.info("📋 Retrieved %d consents for profile %s", len(consents), profile_id)
            return consents
            
        except Exception as e:
            logger.error("❌ Error retrieving consents: %s", e)
            return []
    
    def _map_capability_to_purpose(self, capability: str) -> Optional[str]:
        """Map capability to consent purpose"""
        capability_purpose_map = {
            "DOCUMENT_INTERPRETATION": ConsentPurpose.DOCUMENT_UPLOAD.value,
            "SYMPTOM_DOCUMENTATION": ConsentPurpose.RAG_MEMORY_STORAGE.value,
            "MEDICATION_REMINDER_CHAT": ConsentPurpose.RAG_MEMORY_STORAGE.value,
            "HEALTH_TIMELINE": ConsentPurpose.HEALTH_TIMELINE_ACCESS.value,
            "APPOINTMENT_BOOKING": ConsentPurpose.TELEMEDICINE_CONSULTATION.value,
        }
        
        return capability_purpose_map.get(capability)
    
    def _is_expired(self, consent_record: Dict) -> bool:
        """Check if consent has expired"""
        if not consent_record.get('expires_at'):
            return False
        
        try:
            expires_at = datetime.fromisoformat(consent_record['expires_at'].replace('Z', '+00:00'))
            return datetime.utcnow() > expires_at
        except Exception as e:
            logger.error("❌ Error checking expiration: %s", e)
            return True
    
    async def _get_consent_from_db(
        self,
        user_id: str,
        profile_id: str,
        purpose: str
    ) -> Optional[Dict]:
        """Get consent record from database"""
        if not self.db:
            logger.warning("⚠️ Database not connected, consent verification skipped")
            return None
        
        try:
            # Query database for consent
            # Implementation depends on your database
            # This is a placeholder
            
            # Example Supabase query:
            # result = self.db.table('astra_consents').select('*').eq('user_id', user_id).eq('profile_id', profile_id).eq('purpose', purpose).eq('is_active', True).execute()
            # if result.data:
            #     return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("❌ Error querying consent: %s", e)
            return None
    
    async def _save_consent_to_db(self, consent_data: Dict) -> Optional[str]:
        """Save consent record to database"""
        if not self.db:
            logger.warning("⚠️ Database not connected, consent not saved")
            return None
        
        try:
            # Insert consent record
            # Implementation depends on your database
            # This is a placeholder
            
            # Example Supabase insert:
            # result = self.db.table('astra_consents').insert(consent_data).execute()
            # if result.data:
            #     return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error("❌ Error saving consent: %s", e)
            return None
    
    async def _revoke_consent_in_db(
        self,
        user_id: str,
        profile_id: str,
        purpose: str,
        revoked_at: datetime
    ) -> bool:
        """Revoke consent in database"""
        if not self.db:
            logger.warning("⚠️ Database not connected, consent not revoked")
            return False
        
        try:
            # Update consent record
            # Implementation depends on your database
            # This is a placeholder
            
            # Example Supabase update:
            # result = self.db.table('astra_consents').update({
            #     'revoked_at': revoked_at.isoformat(),
            #     'is_active': False
            # }).eq('user_id', user_id).eq('profile_id', profile_id).eq('purpose', purpose).execute()
            # return bool(result.data)
            
            return False
            
        except Exception as e:
            logger.error("❌ Error revoking consent: %s", e)
            return False
    
    async def verify_guardian_consent(
        self,
        user_id: str,
        profile_id: str,
        guardian_id: str
    ) -> Dict:
        """
        Verify guardian consent for minor profiles.
        
        Required by Indian Contract Act 1872 (minors cannot give legal consent).
        
        Args:
            user_id: User's account ID
            profile_id: Minor's profile ID
            guardian_id: Guardian's user ID
        
        Returns:
            {
                "granted": bool,
                "guardian_id": str,
                "relationship": str,
                "granted_at": datetime,
                "message": str
            }
        """
        # Check if profile is marked as minor
        # Check if guardian consent exists
        # This is a placeholder implementation
        
        logger.info("🔍 Verifying guardian consent for minor profile %s", profile_id)
        
        # Placeholder return
        return {
            "granted": False,
            "guardian_id": guardian_id,
            "relationship": "unknown",
            "granted_at": None,
            "message": "Guardian consent verification not yet implemented"
        }
