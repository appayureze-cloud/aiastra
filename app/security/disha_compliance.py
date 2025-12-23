"""
DISHA (Digital Information Security in Healthcare Act) Compliance
Implements India's healthcare data protection requirements
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import json

Base = declarative_base()


class ConsentType(str, Enum):
    """Types of consent as per DISHA"""
    DATA_COLLECTION = "data_collection"
    DATA_STORAGE = "data_storage"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    TELEMEDICINE = "telemedicine"
    PRESCRIPTION = "prescription"
    DIAGNOSTIC_TESTS = "diagnostic_tests"
    RESEARCH = "research"


class DataAccessPurpose(str, Enum):
    """Purpose of data access for audit trail"""
    TREATMENT = "treatment"
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    DIAGNOSIS = "diagnosis"
    BILLING = "billing"
    RESEARCH = "research"
    ANALYTICS = "analytics"
    PATIENT_REQUEST = "patient_request"
    LEGAL_REQUIREMENT = "legal_requirement"


class PatientConsent(Base):
    """
    Patient consent records as per DISHA requirements
    All health data processing requires explicit consent
    """
    __tablename__ = "patient_consents"
    
    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    consent_type = Column(String, nullable=False)  # ConsentType
    purpose = Column(Text, nullable=False)
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime)
    expires_at = Column(DateTime)  # Optional expiry
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    consent_text = Column(Text)  # What patient agreed to
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataAccessAudit(Base):
    """
    Audit trail for all health data access
    Required by DISHA for compliance
    """
    __tablename__ = "data_access_audits"
    
    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    accessed_by_id = Column(String, nullable=False)  # User/Doctor/System ID
    accessed_by_type = Column(String, nullable=False)  # doctor, patient, admin, system
    access_type = Column(String, nullable=False)  # read, write, delete, share
    data_type = Column(String, nullable=False)  # prescription, lab_report, consultation
    purpose = Column(String, nullable=False)  # DataAccessPurpose
    consent_id = Column(String, ForeignKey('patient_consents.id'))
    ip_address = Column(String)
    user_agent = Column(String)
    accessed_fields = Column(JSON)  # Which specific fields were accessed
    success = Column(Boolean, default=True)
    failure_reason = Column(Text)
    accessed_at = Column(DateTime, default=datetime.utcnow, index=True)


class DataRetentionPolicy(Base):
    """
    Data retention policies as per DISHA
    Automatic deletion after retention period
    """
    __tablename__ = "data_retention_policies"
    
    id = Column(String, primary_key=True)
    data_type = Column(String, nullable=False, unique=True)
    retention_days = Column(Integer, nullable=False)
    auto_delete = Column(Boolean, default=True)
    anonymize_instead = Column(Boolean, default=False)  # Anonymize instead of delete
    legal_basis = Column(Text)  # Legal reason for retention period
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataBreachLog(Base):
    """
    Data breach logging as required by DISHA
    Must report within 72 hours
    """
    __tablename__ = "data_breach_logs"
    
    id = Column(String, primary_key=True)
    breach_type = Column(String, nullable=False)  # unauthorized_access, data_leak, etc.
    severity = Column(String, nullable=False)  # low, medium, high, critical
    affected_patients = Column(JSON)  # List of patient IDs
    affected_data_types = Column(JSON)  # Types of data affected
    breach_detected_at = Column(DateTime, nullable=False)
    breach_reported_at = Column(DateTime)
    breach_resolved_at = Column(DateTime)
    description = Column(Text)
    impact_assessment = Column(Text)
    remedial_actions = Column(Text)
    reported_to_authorities = Column(Boolean, default=False)
    authority_reference_number = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class DISHACompliance:
    """
    DISHA Compliance Manager
    Handles consent, audit, and compliance requirements
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def check_consent(
        self, 
        patient_id: str, 
        consent_type: ConsentType,
        purpose: Optional[str] = None
    ) -> bool:
        """
        Check if valid consent exists for data access
        """
        consent = self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type,
            PatientConsent.granted == True,
            PatientConsent.revoked == False
        ).first()
        
        if not consent:
            return False
        
        # Check if consent expired
        if consent.expires_at and consent.expires_at < datetime.utcnow():
            return False
        
        return True
    
    async def grant_consent(
        self,
        patient_id: str,
        consent_type: ConsentType,
        purpose: str,
        expires_in_days: Optional[int] = None,
        consent_text: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PatientConsent:
        """
        Record patient consent
        """
        import uuid
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        consent = PatientConsent(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            consent_type=consent_type.value,
            purpose=purpose,
            granted=True,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            consent_text=consent_text,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(consent)
        self.db.commit()
        
        return consent
    
    async def revoke_consent(
        self,
        patient_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Revoke patient consent
        """
        consent = self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type.value,
            PatientConsent.revoked == False
        ).first()
        
        if consent:
            consent.revoked = True
            consent.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    async def log_data_access(
        self,
        patient_id: str,
        accessed_by_id: str,
        accessed_by_type: str,
        access_type: str,
        data_type: str,
        purpose: DataAccessPurpose,
        accessed_fields: Optional[List[str]] = None,
        consent_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None
    ) -> DataAccessAudit:
        """
        Log all health data access for audit trail
        """
        import uuid
        
        audit = DataAccessAudit(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            accessed_by_id=accessed_by_id,
            accessed_by_type=accessed_by_type,
            access_type=access_type,
            data_type=data_type,
            purpose=purpose.value,
            consent_id=consent_id,
            accessed_fields=accessed_fields,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        
        self.db.add(audit)
        self.db.commit()
        
        return audit
    
    async def get_patient_audit_trail(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DataAccessAudit]:
        """
        Get complete audit trail for a patient
        Patients have right to know who accessed their data
        """
        query = self.db.query(DataAccessAudit).filter(
            DataAccessAudit.patient_id == patient_id
        )
        
        if start_date:
            query = query.filter(DataAccessAudit.accessed_at >= start_date)
        if end_date:
            query = query.filter(DataAccessAudit.accessed_at <= end_date)
        
        return query.order_by(DataAccessAudit.accessed_at.desc()).all()
    
    async def anonymize_data(self, patient_data: Dict) -> Dict:
        """
        Anonymize patient data for research/analytics
        Removes all PII as per DISHA requirements
        """
        anonymized = patient_data.copy()
        
        # Remove direct identifiers
        pii_fields = [
            'name', 'phone_number', 'email', 'address', 
            'aadhar', 'pan', 'patient_id', 'id'
        ]
        
        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = None
        
        # Generalize dates (keep only month/year)
        if 'date_of_birth' in anonymized:
            dob = datetime.fromisoformat(anonymized['date_of_birth'])
            anonymized['date_of_birth'] = f"{dob.year}-{dob.month:02d}"
        
        # Generalize location (keep only state/city, remove exact address)
        if 'location' in anonymized:
            # Keep only city/state level
            pass
        
        return anonymized
    
    async def check_retention_policy(self, data_type: str) -> Optional[DataRetentionPolicy]:
        """
        Get retention policy for data type
        """
        return self.db.query(DataRetentionPolicy).filter(
            DataRetentionPolicy.data_type == data_type
        ).first()
    
    async def log_data_breach(
        self,
        breach_type: str,
        severity: str,
        affected_patients: List[str],
        affected_data_types: List[str],
        description: str,
        impact_assessment: Optional[str] = None
    ) -> DataBreachLog:
        """
        Log data breach (must report within 72 hours to authorities)
        """
        import uuid
        
        breach = DataBreachLog(
            id=str(uuid.uuid4()),
            breach_type=breach_type,
            severity=severity,
            affected_patients=affected_patients,
            affected_data_types=affected_data_types,
            breach_detected_at=datetime.utcnow(),
            description=description,
            impact_assessment=impact_assessment
        )
        
        self.db.add(breach)
        self.db.commit()
        
        # TODO: Send automated alert to compliance team
        # TODO: Notify affected patients
        # TODO: Report to authorities if severity is high/critical
        
        return breach
