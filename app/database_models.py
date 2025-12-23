"""
Database Models for Astra - Ayurvedic Wellness Assistant
Handles users, sessions, and chat history storage in Supabase
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found. Running without database features.")
    DATABASE_URL = None

# Create engine with connection pooling only if DATABASE_URL exists
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

class User(Base):
    """User model for storing Auth0 user information"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Auth0 user ID (sub claim)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    """User session model for persistent session management"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Store additional session metadata
    session_metadata = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    chat_history = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")

class ChatHistory(Base):
    """Chat history model for storing conversations"""
    __tablename__ = "chat_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False)
    
    # Message content
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    
    # Language and context information
    detected_language = Column(String, default="en")
    language_name = Column(String, default="English")
    is_ayurveda_related = Column(Boolean, default=True)
    
    # Model usage information
    model_name = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Additional metadata (topic, sentiment, etc.)
    chat_metadata = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    session = relationship("UserSession", back_populates="chat_history")

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def get_db_dependency():
    """FastAPI dependency for database session"""
    if not SessionLocal:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    if not engine:
        logger.info("Database not configured, skipping table creation")
        return
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def upsert_user(db: Session, user_info: Dict[str, Any]) -> User:
    """Create or update user in database"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_info["user_id"]).first()
        
        if user:
            # Update existing user
            user.email = user_info.get("email", user.email)
            user.name = user_info.get("name", user.name)
            user.picture = user_info.get("picture", user.picture)
            user.email_verified = user_info.get("email_verified", user.email_verified)
            user.updated_at = datetime.now(timezone.utc)
        else:
            # Create new user
            user = User(
                id=user_info["user_id"],
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                email_verified=user_info.get("email_verified", False)
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upsert user: {e}")
        raise

def create_user_session(db: Session, user_id: str, session_token: str, expires_at: Optional[datetime] = None) -> UserSession:
    """Create new user session"""
    try:
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            session_metadata={"created_via": "auth0_login"}
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user session: {e}")
        raise

def get_user_session(db: Session, session_token: str) -> Optional[UserSession]:
    """Get user session by token"""
    try:
        return db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
    except Exception as e:
        logger.error(f"Failed to get user session: {e}")
        return None

def save_chat_message(
    db: Session,
    user_id: str,
    session_id: uuid.UUID,
    user_message: str,
    assistant_response: str,
    language_info: Dict[str, Any],
    model_info: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> ChatHistory:
    """Save chat message to history"""
    try:
        chat_entry = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            detected_language=language_info.get("detected_language", "en"),
            language_name=language_info.get("language_name", "English"),
            is_ayurveda_related=language_info.get("is_ayurveda_related", True),
            model_name=model_info.get("model"),
            prompt_tokens=model_info.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=model_info.get("usage", {}).get("completion_tokens", 0),
            total_tokens=model_info.get("usage", {}).get("total_tokens", 0),
            chat_metadata=metadata or {}
        )
        
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)
        return chat_entry
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save chat message: {e}")
        raise

def get_user_chat_history(db: Session, user_id: str, session_id: Optional[uuid.UUID] = None, limit: int = 50) -> List[ChatHistory]:
    """Get user's chat history"""
    try:
        query = db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
        
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        
        return query.order_by(ChatHistory.created_at.desc()).limit(limit).all()
    
    except Exception as e:
        logger.error(f"Failed to get user chat history: {e}")
        return []

# Patient Management Models for Smart Auto-Cart System

class PatientToken(Base):
    """FCM tokens for patient notifications"""
    __tablename__ = "patient_tokens"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(100), unique=True, nullable=False)
    fcm_token = Column(String(200), nullable=False)
    device_info = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PatientProfile(Base):
    """Patient profile information for prescription management"""
    __tablename__ = "patient_profiles"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(100), unique=True, nullable=False)  # Unique identifier
    patient_code = Column(String(20), unique=True, nullable=False)  # Short code for doctor lookup
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(200), nullable=True)
    medical_conditions = Column(Text, nullable=True)  # JSON string
    allergies = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Consultation(Base):
    """Consultation records linking doctors and patients"""
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True)
    consultation_id = Column(String(100), unique=True, nullable=False)
    patient_id = Column(String(100), nullable=False)  # Links to PatientProfile.patient_id
    doctor_id = Column(String(100), nullable=False)
    doctor_name = Column(String(200), nullable=False)
    doctor_specialization = Column(String(200), nullable=True)
    appointment_date = Column(DateTime(timezone=True), nullable=True)
    consultation_type = Column(String(50), default='online')  # online, clinic, home_visit
    status = Column(String(50), default='scheduled')  # scheduled, completed, cancelled
    diagnosis = Column(Text, nullable=True)
    prescription_sent = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Database helper functions for patient management

def create_patient_profile(db: Session, patient_data: Dict[str, Any]) -> PatientProfile:
    """Create a new patient profile with unique patient code"""
    try:
        import random
        import string
        
        # Generate unique patient code (e.g., PAT001, PAT002)
        while True:
            patient_code = "PAT" + "".join(random.choices(string.digits, k=3))
            existing = db.query(PatientProfile).filter(PatientProfile.patient_code == patient_code).first()
            if not existing:
                break
        
        patient = PatientProfile(
            patient_id=patient_data["patient_id"],
            patient_code=patient_code,
            name=patient_data["name"],
            email=patient_data.get("email"),
            phone=patient_data.get("phone"),
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            address=patient_data.get("address"),
            emergency_contact=patient_data.get("emergency_contact"),
            medical_conditions=patient_data.get("medical_conditions"),
            allergies=patient_data.get("allergies")
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create patient profile: {e}")
        raise

def search_patients(db: Session, search_term: str) -> List[PatientProfile]:
    """Search patients by name, phone, or patient code for doctor app"""
    try:
        search_term = f"%{search_term}%"
        
        patients = db.query(PatientProfile).filter(
            PatientProfile.is_active == True
        ).filter(
            PatientProfile.name.ilike(search_term) |
            PatientProfile.phone.ilike(search_term) |
            PatientProfile.patient_code.ilike(search_term) |
            PatientProfile.email.ilike(search_term)
        ).limit(10).all()
        
        return patients
        
    except Exception as e:
        logger.error(f"Failed to search patients: {e}")
        return []

def get_patient_by_code(db: Session, patient_code: str) -> Optional[PatientProfile]:
    """Get patient by patient code for prescription creation"""
    try:
        return db.query(PatientProfile).filter(
            PatientProfile.patient_code == patient_code,
            PatientProfile.is_active == True
        ).first()
        
    except Exception as e:
        logger.error(f"Failed to get patient by code: {e}")
        return None

def create_consultation(db: Session, consultation_data: Dict[str, Any]) -> Consultation:
    """Create consultation record"""
    try:
        consultation = Consultation(
            consultation_id=consultation_data["consultation_id"],
            patient_id=consultation_data["patient_id"],
            doctor_id=consultation_data["doctor_id"],
            doctor_name=consultation_data["doctor_name"],
            doctor_specialization=consultation_data.get("doctor_specialization"),
            appointment_date=consultation_data.get("appointment_date"),
            consultation_type=consultation_data.get("consultation_type", "online"),
            status=consultation_data.get("status", "scheduled"),
            diagnosis=consultation_data.get("diagnosis"),
            notes=consultation_data.get("notes")
        )
        
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        return consultation
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create consultation: {e}")
        raise

class PrescriptionRecord(Base):
    """Complete prescription records with Shopify integration"""
    __tablename__ = "prescription_records"
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(String(100), unique=True, nullable=False)
    patient_id = Column(String(100), nullable=False)  # Links to PatientProfile.patient_id
    doctor_id = Column(String(100), nullable=False)
    consultation_id = Column(String(100), nullable=True)  # Links to Consultation
    
    # Prescription details
    diagnosis = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Shopify integration
    draft_order_id = Column(String(50), nullable=True)
    invoice_url = Column(Text, nullable=True)
    total_amount = Column(String(20), nullable=True)
    
    # Status tracking
    status = Column(String(50), default='created')  # created, notified, paid, shipped, delivered, cancelled
    notification_sent = Column(Boolean, default=False)
    payment_status = Column(String(50), default='pending')  # pending, paid, failed, refunded
    
    # Timestamps
    prescribed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notified_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PrescribedMedicine(Base):
    """Individual medicines in a prescription"""
    __tablename__ = "prescribed_medicines"
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(String(100), nullable=False)  # Links to PrescriptionRecord
    
    # Medicine details
    medicine_name = Column(String(200), nullable=False)
    shopify_variant_id = Column(String(50), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(String(20), nullable=True)
    total_price = Column(String(20), nullable=True)
    
    # Dosage instructions
    dose = Column(String(100), nullable=False)
    schedule = Column(String(100), nullable=False)  # 1-0-1, 2-2-2, etc.
    timing = Column(String(100), nullable=False)    # Before meals, After meals, etc.
    duration = Column(String(100), nullable=False)  # 7 days, 30 days, etc.
    instructions = Column(Text, nullable=True)       # Special instructions
    
    # Availability status
    is_available = Column(Boolean, default=True)
    alternatives_suggested = Column(Text, nullable=True)  # JSON string of alternatives
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MedicineSchedule(Base):
    """Medicine schedule and reminder tracking"""
    __tablename__ = "medicine_schedules"
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(String(100), nullable=False)  # Links to PrescriptionRecord
    patient_id = Column(String(100), nullable=False)  # Links to PatientProfile
    medicine_name = Column(String(200), nullable=False)
    
    # Schedule details
    dose_amount = Column(String(50), nullable=False)  # "1 tablet", "5ml", etc.
    schedule_pattern = Column(String(50), nullable=False)  # "1-0-1", "2-2-2", etc.
    timing_type = Column(String(50), nullable=False)  # "before_food", "after_food", "with_food"
    duration_days = Column(Integer, nullable=False)  # Total days to take medicine
    
    # Timing calculations
    morning_time = Column(String(10), nullable=True)  # "08:00"
    afternoon_time = Column(String(10), nullable=True)  # "13:00"
    evening_time = Column(String(10), nullable=True)  # "20:00"
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    reminders_enabled = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Patient preferences
    preferred_reminder_time = Column(Integer, default=30)  # Minutes before dose
    whatsapp_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class MedicineReminder(Base):
    """Individual medicine reminder instances"""
    __tablename__ = "medicine_reminders"
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("medicine_schedules.id"), nullable=False)
    patient_id = Column(String(100), nullable=False)
    
    # Reminder details
    reminder_datetime = Column(DateTime(timezone=True), nullable=False)
    dose_datetime = Column(DateTime(timezone=True), nullable=False)
    dose_type = Column(String(20), nullable=False)  # "morning", "afternoon", "evening"
    
    # Status tracking
    status = Column(String(20), default='scheduled')  # scheduled, sent, acknowledged, missed, stopped
    whatsapp_sent = Column(Boolean, default=False)
    push_sent = Column(Boolean, default=False)
    patient_response = Column(String(20), nullable=True)  # "taken", "skipped", "later"
    response_time = Column(DateTime(timezone=True), nullable=True)
    
    # Message tracking
    whatsapp_message_id = Column(String(100), nullable=True)
    push_notification_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PatientAdherence(Base):
    """Patient medicine adherence tracking"""
    __tablename__ = "patient_adherence"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(100), nullable=False)
    prescription_id = Column(String(100), nullable=False)
    medicine_name = Column(String(200), nullable=False)
    
    # Adherence statistics
    total_doses_prescribed = Column(Integer, default=0)
    doses_taken = Column(Integer, default=0)
    doses_missed = Column(Integer, default=0)
    doses_skipped = Column(Integer, default=0)
    
    # Calculated metrics
    adherence_percentage = Column(Integer, default=0)  # 0-100
    streak_days = Column(Integer, default=0)  # Current consecutive days
    longest_streak = Column(Integer, default=0)  # Best streak achieved
    
    # Tracking period
    tracking_start = Column(DateTime(timezone=True), nullable=False)
    tracking_end = Column(DateTime(timezone=True), nullable=True)
    last_dose_time = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class OrderStatusHistory(Base):
    """Track order status changes over time"""
    __tablename__ = "order_status_history"
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(String(100), nullable=False)
    draft_order_id = Column(String(50), nullable=True)
    
    # Status change details
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), nullable=True)  # system, shopify_webhook, manual
    change_reason = Column(Text, nullable=True)
    
    # Additional data
    shopify_order_id = Column(String(50), nullable=True)  # When draft becomes real order
    tracking_number = Column(String(100), nullable=True)
    tracking_url = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DocumentRecord(Base):
    """Track medical documents stored in Storj"""
    __tablename__ = "document_records"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(100), unique=True, nullable=False)  # UUID
    patient_id = Column(String(100), nullable=False)
    
    # Document details
    doc_type = Column(String(50), nullable=False)  # prescription, lab_report, xray, mri, ct_scan, etc.
    original_filename = Column(String(255), nullable=False)
    storj_object_key = Column(Text, nullable=False)  # Path in Storj bucket
    file_size = Column(Integer, nullable=True)  # Size in bytes
    content_type = Column(String(100), nullable=True)  # MIME type
    
    # Metadata
    uploaded_by = Column(String(100), nullable=True)  # Doctor/Admin ID
    description = Column(Text, nullable=True)
    related_prescription_id = Column(String(100), nullable=True)  # Link to prescription if applicable
    related_consultation_id = Column(Integer, nullable=True)  # Link to consultation if applicable
    
    # Access tracking
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Sharing
    is_shared = Column(Boolean, default=False)
    shared_via = Column(String(50), nullable=True)  # whatsapp, email, link
    share_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Additional metadata (tags, notes, etc.)
    doc_metadata = Column(JSON, default={})

# Helper functions for prescription management

def create_prescription_record(db: Session, prescription_data: Dict[str, Any]) -> PrescriptionRecord:
    """Create a complete prescription record with medicines"""
    try:
        import uuid
        
        # Generate unique prescription ID
        prescription_id = f"rx_{uuid.uuid4().hex[:12]}"
        
        # Create prescription record
        prescription = PrescriptionRecord(
            prescription_id=prescription_id,
            patient_id=prescription_data["patient_id"],
            doctor_id=prescription_data["doctor_id"],
            consultation_id=prescription_data.get("consultation_id"),
            diagnosis=prescription_data["diagnosis"],
            notes=prescription_data.get("notes"),
            draft_order_id=prescription_data.get("draft_order_id"),
            invoice_url=prescription_data.get("invoice_url"),
            total_amount=prescription_data.get("total_amount"),
            status="created"
        )
        
        db.add(prescription)
        db.flush()  # Get the ID before adding medicines
        
        # Add prescribed medicines
        for medicine_data in prescription_data.get("medicines", []):
            medicine = PrescribedMedicine(
                prescription_id=prescription_id,
                medicine_name=medicine_data["medicine_name"],
                shopify_variant_id=medicine_data.get("shopify_variant_id"),
                quantity=medicine_data.get("quantity", 1),
                unit_price=medicine_data.get("unit_price"),
                total_price=medicine_data.get("total_price"),
                dose=medicine_data["dose"],
                schedule=medicine_data["schedule"],
                timing=medicine_data["timing"],
                duration=medicine_data["duration"],
                instructions=medicine_data.get("instructions"),
                is_available=medicine_data.get("is_available", True),
                alternatives_suggested=medicine_data.get("alternatives_suggested")
            )
            db.add(medicine)
        
        # Add initial status history
        status_history = OrderStatusHistory(
            prescription_id=prescription_id,
            draft_order_id=prescription_data.get("draft_order_id"),
            previous_status=None,
            new_status="created",
            changed_by="system",
            change_reason="Prescription created by doctor"
        )
        db.add(status_history)
        
        db.commit()
        db.refresh(prescription)
        return prescription
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create prescription record: {e}")
        raise

def update_prescription_status(
    db: Session, 
    prescription_id: str, 
    new_status: str, 
    changed_by: str = "system",
    change_reason: str = None,
    additional_data: Dict[str, Any] = None
) -> bool:
    """Update prescription status and add to history"""
    try:
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.prescription_id == prescription_id
        ).first()
        
        if not prescription:
            return False
        
        previous_status = prescription.status
        prescription.status = new_status
        prescription.updated_at = datetime.now(timezone.utc)
        
        # Update specific timestamps based on status
        now = datetime.now(timezone.utc)
        if new_status == "notified":
            prescription.notified_at = now
            prescription.notification_sent = True
        elif new_status == "paid":
            prescription.paid_at = now
            prescription.payment_status = "paid"
        elif new_status == "shipped":
            prescription.shipped_at = now
        elif new_status == "delivered":
            prescription.delivered_at = now
        
        # Add to status history
        status_history = OrderStatusHistory(
            prescription_id=prescription_id,
            draft_order_id=prescription.draft_order_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=change_reason,
            shopify_order_id=additional_data.get("shopify_order_id") if additional_data else None,
            tracking_number=additional_data.get("tracking_number") if additional_data else None,
            tracking_url=additional_data.get("tracking_url") if additional_data else None
        )
        db.add(status_history)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update prescription status: {e}")
        return False

def get_patient_prescriptions(db: Session, patient_id: str) -> List[Dict[str, Any]]:
    """Get all prescriptions for a patient with medicines and status history"""
    try:
        prescriptions = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.patient_id == patient_id
        ).order_by(PrescriptionRecord.created_at.desc()).all()
        
        result = []
        for prescription in prescriptions:
            # Get medicines for this prescription
            medicines = db.query(PrescribedMedicine).filter(
                PrescribedMedicine.prescription_id == prescription.prescription_id
            ).all()
            
            # Get status history
            status_history = db.query(OrderStatusHistory).filter(
                OrderStatusHistory.prescription_id == prescription.prescription_id
            ).order_by(OrderStatusHistory.created_at.desc()).all()
            
            result.append({
                "prescription_id": prescription.prescription_id,
                "diagnosis": prescription.diagnosis,
                "notes": prescription.notes,
                "status": prescription.status,
                "payment_status": prescription.payment_status,
                "total_amount": prescription.total_amount,
                "draft_order_id": prescription.draft_order_id,
                "invoice_url": prescription.invoice_url,
                "prescribed_at": prescription.prescribed_at.isoformat(),
                "notified_at": prescription.notified_at.isoformat() if prescription.notified_at else None,
                "paid_at": prescription.paid_at.isoformat() if prescription.paid_at else None,
                "medicines": [{
                    "medicine_name": med.medicine_name,
                    "dose": med.dose,
                    "schedule": med.schedule,
                    "timing": med.timing,
                    "duration": med.duration,
                    "instructions": med.instructions,
                    "quantity": med.quantity,
                    "unit_price": med.unit_price,
                    "total_price": med.total_price,
                    "is_available": med.is_available
                } for med in medicines],
                "status_history": [{
                    "status": history.new_status,
                    "changed_at": history.created_at.isoformat(),
                    "changed_by": history.changed_by,
                    "reason": history.change_reason
                } for history in status_history]
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get patient prescriptions: {e}")
        return []