"""
Medicine Reminder Engine
Handles scheduling, sending, and tracking medicine reminders
"""

import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database_models import (
    SessionLocal, MedicineSchedule, MedicineReminder, 
    PatientProfile, PatientAdherence, PrescriptionRecord
)
from .custom_whatsapp_client import CustomWhatsAppClient
from .prescription_analyzer import PrescriptionAnalyzer
import os

logger = logging.getLogger(__name__)

class ReminderEngine:
    """Engine for managing medicine reminders and patient adherence"""
    
    def __init__(self):
        # Initialize custom WhatsApp client
        try:
            self.whatsapp_client = CustomWhatsAppClient()
            logger.info("✅ Custom WhatsApp client initialized for reminders")
        except Exception as e:
            logger.error(f"Failed to initialize custom WhatsApp client: {e}")
            self.whatsapp_client = None
        
        self.prescription_analyzer = PrescriptionAnalyzer()
        
        # Default reminder times
        self.default_times = {
            'morning': time(8, 0),    # 8:00 AM
            'afternoon': time(13, 0), # 1:00 PM
            'evening': time(20, 0)    # 8:00 PM
        }
    
    def create_medicine_schedules_from_prescription(self, prescription_id: str) -> bool:
        """Create medicine schedules from a prescription"""
        try:
            db = SessionLocal()
            
            # Get prescription details
            prescription = db.query(PrescriptionRecord).filter(
                PrescriptionRecord.prescription_id == prescription_id
            ).first()
            
            if not prescription:
                logger.error(f"Prescription not found: {prescription_id}")
                return False
            
            # Get patient details
            patient = db.query(PatientProfile).filter(
                PatientProfile.patient_id == prescription.patient_id
            ).first()
            
            if not patient:
                logger.error(f"Patient not found: {prescription.patient_id}")
                return False
            
            # Get prescribed medicines from database
            from ..database_models import PrescribedMedicine
            prescribed_medicines = db.query(PrescribedMedicine).filter(
                PrescribedMedicine.prescription_id == prescription_id
            ).all()
            
            if not prescribed_medicines:
                logger.warning(f"No prescribed medicines found for prescription: {prescription_id}")
                return False
            
            # Convert to dict format for analyzer
            medicines_data = []
            for med in prescribed_medicines:
                medicines_data.append({
                    'medicine_name': med.medicine_name,
                    'dose': med.dose,
                    'schedule': med.schedule,
                    'timing': med.timing,
                    'duration': med.duration,
                    'instructions': med.instructions
                })
            
            # Analyze medicines to extract schedules
            analyzed_medicines = self.prescription_analyzer.analyze_prescribed_medicines(medicines_data)
            
            # Create medicine schedules
            created_count = 0
            for medicine in analyzed_medicines:
                if self._create_medicine_schedule(db, prescription, patient, medicine):
                    created_count += 1
            
            db.commit()
            logger.info(f"Created {created_count} medicine schedules for prescription {prescription_id}")
            return created_count > 0
            
        except Exception as e:
            logger.error(f"Error creating medicine schedules: {str(e)}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    def _create_medicine_schedule(self, db: Session, prescription: PrescriptionRecord, 
                                patient: PatientProfile, medicine: Dict[str, Any]) -> bool:
        """Create a single medicine schedule"""
        try:
            # Calculate timing based on schedule
            schedule = medicine['schedule']
            morning_time = self.default_times['morning'] if schedule.get('morning', 0) > 0 else None
            afternoon_time = self.default_times['afternoon'] if schedule.get('afternoon', 0) > 0 else None
            evening_time = self.default_times['evening'] if schedule.get('evening', 0) > 0 else None
            
            # Calculate start and end dates
            start_date = datetime.now()
            end_date = start_date + timedelta(days=medicine['duration_days'])
            
            # Create schedule
            schedule_obj = MedicineSchedule(
                prescription_id=prescription.prescription_id,
                patient_id=patient.patient_id,
                medicine_name=medicine['medicine_name'],
                dose_amount=medicine['dose_amount'],
                schedule_pattern=f"{schedule.get('morning', 0)}-{schedule.get('afternoon', 0)}-{schedule.get('evening', 0)}",
                timing_type=medicine['timing_type'],
                duration_days=medicine['duration_days'],
                morning_time=morning_time.strftime('%H:%M') if morning_time else None,
                afternoon_time=afternoon_time.strftime('%H:%M') if afternoon_time else None,
                evening_time=evening_time.strftime('%H:%M') if evening_time else None,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                reminders_enabled=True
            )
            
            db.add(schedule_obj)
            db.flush()  # Get the ID
            
            # Create individual reminders for the next 3 days (as requested)
            self._create_reminders_for_schedule(db, schedule_obj, days=3)
            
            # Initialize adherence tracking
            self._initialize_adherence_tracking(db, schedule_obj)
            
            logger.info(f"Created schedule for {medicine['medicine_name']} for patient {patient.patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating medicine schedule: {str(e)}")
            return False
    
    def _create_reminders_for_schedule(self, db: Session, schedule: MedicineSchedule, days: int = 3):
        """Create reminder instances for a schedule"""
        try:
            current_date = schedule.start_date.date()
            end_date = min(schedule.end_date.date(), current_date + timedelta(days=days))
            
            while current_date <= end_date:
                # Create reminders based on schedule pattern
                pattern_parts = schedule.schedule_pattern.split('-')
                morning_doses = int(pattern_parts[0])
                afternoon_doses = int(pattern_parts[1]) if len(pattern_parts) > 1 else 0
                evening_doses = int(pattern_parts[2]) if len(pattern_parts) > 2 else 0
                
                # Create morning reminders
                if morning_doses > 0 and schedule.morning_time:
                    self._create_reminder_instance(db, schedule, current_date, 'morning', schedule.morning_time)
                
                # Create afternoon reminders
                if afternoon_doses > 0 and schedule.afternoon_time:
                    self._create_reminder_instance(db, schedule, current_date, 'afternoon', schedule.afternoon_time)
                
                # Create evening reminders
                if evening_doses > 0 and schedule.evening_time:
                    self._create_reminder_instance(db, schedule, current_date, 'evening', schedule.evening_time)
                
                current_date += timedelta(days=1)
            
            logger.info(f"Created reminders for {days} days for schedule {schedule.id}")
            
        except Exception as e:
            logger.error(f"Error creating reminders for schedule: {str(e)}")
    
    def _create_reminder_instance(self, db: Session, schedule: MedicineSchedule, 
                                date, dose_type: str, dose_time_str: str):
        """Create a single reminder instance"""
        try:
            # Parse dose time
            hour, minute = map(int, dose_time_str.split(':'))
            dose_datetime = datetime.combine(date, time(hour, minute))
            
            # Calculate reminder time (30 minutes before by default)
            reminder_datetime = dose_datetime - timedelta(minutes=schedule.preferred_reminder_time)
            
            # Only create if reminder time is in the future
            if reminder_datetime > datetime.now():
                reminder = MedicineReminder(
                    schedule_id=schedule.id,
                    patient_id=schedule.patient_id,
                    reminder_datetime=reminder_datetime,
                    dose_datetime=dose_datetime,
                    dose_type=dose_type,
                    status='scheduled'
                )
                
                db.add(reminder)
                
        except Exception as e:
            logger.error(f"Error creating reminder instance: {str(e)}")
    
    def _initialize_adherence_tracking(self, db: Session, schedule: MedicineSchedule):
        """Initialize adherence tracking for a medicine schedule"""
        try:
            # Calculate total doses for the duration
            pattern_parts = schedule.schedule_pattern.split('-')
            daily_doses = sum(int(part) for part in pattern_parts)
            total_doses = daily_doses * schedule.duration_days
            
            adherence = PatientAdherence(
                patient_id=schedule.patient_id,
                prescription_id=schedule.prescription_id,
                medicine_name=schedule.medicine_name,
                total_doses_prescribed=total_doses,
                tracking_start=schedule.start_date,
                tracking_end=schedule.end_date
            )
            
            db.add(adherence)
            
        except Exception as e:
            logger.error(f"Error initializing adherence tracking: {str(e)}")
    
    async def send_pending_reminders(self) -> int:
        """Send all pending reminders"""
        try:
            db = SessionLocal()
            sent_count = 0
            
            # Get reminders that need to be sent (within next 5 minutes)
            now = datetime.now()
            send_window = now + timedelta(minutes=5)
            
            pending_reminders = db.query(MedicineReminder).filter(
                and_(
                    MedicineReminder.status == 'scheduled',
                    MedicineReminder.reminder_datetime <= send_window,
                    MedicineReminder.reminder_datetime >= now - timedelta(minutes=5)
                )
            ).all()
            
            for reminder in pending_reminders:
                if await self._send_reminder(db, reminder):
                    sent_count += 1
            
            db.commit()
            if sent_count > 0:
                logger.info(f"Sent {sent_count} medicine reminders")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending pending reminders: {str(e)}")
            return 0
        finally:
            if db:
                db.close()
    
    async def _send_reminder(self, db: Session, reminder: MedicineReminder) -> bool:
        """Send a single reminder"""
        try:
            # Get patient details
            patient = db.query(PatientProfile).filter(
                PatientProfile.patient_id == reminder.patient_id
            ).first()
            
            if not patient or not patient.phone:
                logger.warning(f"Patient phone not found for reminder {reminder.id}")
                return False
            
            # Get schedule details
            schedule = db.query(MedicineSchedule).filter(
                MedicineSchedule.id == reminder.schedule_id
            ).first()
            
            if not schedule:
                logger.error(f"Schedule not found for reminder {reminder.id}")
                return False
            
            # Send WhatsApp reminder if enabled and client available
            if schedule.whatsapp_enabled and self.whatsapp_client:
                result = await self.whatsapp_client.send_medicine_reminder(
                    patient_phone=patient.phone,
                    patient_name=patient.name,
                    medicine_name=schedule.medicine_name,
                    dose_amount=schedule.dose_amount,
                    dose_time=reminder.dose_datetime.strftime('%I:%M %p'),
                    instructions=schedule.instructions if hasattr(schedule, 'instructions') else None
                )
                
                if result:
                    reminder.whatsapp_sent = True
                    reminder.whatsapp_message_id = str(result.get('id', '')) if isinstance(result, dict) else 'sent'
                    logger.info(f"WhatsApp reminder sent for {schedule.medicine_name} to {patient.name}")
            
            # Update reminder status
            reminder.status = 'sent'
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {str(e)}")
            return False
    
    def handle_patient_response(self, patient_phone: str, response: str, 
                              message_timestamp: Optional[str] = None) -> bool:
        """Handle patient response to medicine reminder"""
        try:
            db = SessionLocal()
            
            # Find patient by phone
            patient = db.query(PatientProfile).filter(
                PatientProfile.phone.like(f"%{patient_phone.replace('+91', '')}%")
            ).first()
            
            if not patient:
                logger.warning(f"Patient not found for phone: {patient_phone}")
                return False
            
            # Find the most recent sent reminder for this patient
            recent_reminder = db.query(MedicineReminder).filter(
                and_(
                    MedicineReminder.patient_id == patient.patient_id,
                    MedicineReminder.status == 'sent',
                    MedicineReminder.whatsapp_sent == True
                )
            ).order_by(MedicineReminder.reminder_datetime.desc()).first()
            
            if not recent_reminder:
                logger.warning(f"No recent reminder found for patient {patient.patient_id}")
                return False
            
            # Update reminder with response
            recent_reminder.patient_response = response
            recent_reminder.response_time = datetime.now()
            recent_reminder.status = 'acknowledged'
            
            # Update adherence tracking
            self._update_adherence(db, recent_reminder, response)
            
            # Handle stop request
            if response == 'stop':
                self._stop_reminders_for_patient(db, patient.patient_id, recent_reminder.schedule_id)
            
            db.commit()
            logger.info(f"Processed response '{response}' from {patient.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling patient response: {str(e)}")
            return False
        finally:
            if db:
                db.close()
    
    def _update_adherence(self, db: Session, reminder: MedicineReminder, response: str):
        """Update patient adherence based on response"""
        try:
            schedule = db.query(MedicineSchedule).filter(
                MedicineSchedule.id == reminder.schedule_id
            ).first()
            
            if not schedule:
                return
            
            adherence = db.query(PatientAdherence).filter(
                and_(
                    PatientAdherence.patient_id == reminder.patient_id,
                    PatientAdherence.medicine_name == schedule.medicine_name
                )
            ).first()
            
            if not adherence:
                return
            
            # Update counts based on response
            if response == 'taken':
                adherence.doses_taken += 1
                adherence.last_dose_time = datetime.now()
                # Update streak
                if adherence.last_dose_time and adherence.last_dose_time.date() == (datetime.now() - timedelta(days=1)).date():
                    adherence.streak_days += 1
                else:
                    adherence.streak_days = 1
                adherence.longest_streak = max(adherence.longest_streak, adherence.streak_days)
                
            elif response == 'skipped':
                adherence.doses_skipped += 1
                adherence.streak_days = 0
                
            elif response == 'later':
                # Don't count as missed yet, will be handled by missed reminder logic
                pass
            
            # Recalculate adherence percentage
            total_responded = adherence.doses_taken + adherence.doses_skipped + adherence.doses_missed
            if total_responded > 0:
                adherence.adherence_percentage = int((adherence.doses_taken / total_responded) * 100)
            
        except Exception as e:
            logger.error(f"Error updating adherence: {str(e)}")
    
    def _stop_reminders_for_patient(self, db: Session, patient_id: str, schedule_id: int):
        """Stop all future reminders for a specific medicine schedule"""
        try:
            # Disable the schedule
            schedule = db.query(MedicineSchedule).filter(
                MedicineSchedule.id == schedule_id
            ).first()
            
            if schedule:
                schedule.reminders_enabled = False
                
                # Cancel future reminders
                future_reminders = db.query(MedicineReminder).filter(
                    and_(
                        MedicineReminder.schedule_id == schedule_id,
                        MedicineReminder.status == 'scheduled',
                        MedicineReminder.reminder_datetime > datetime.now()
                    )
                ).all()
                
                for reminder in future_reminders:
                    reminder.status = 'stopped'
                
                # Send confirmation
                patient = db.query(PatientProfile).filter(
                    PatientProfile.patient_id == patient_id
                ).first()
                
                if patient and patient.phone:
                    self.whatsapp_client.send_stop_reminder_confirmation(
                        patient_phone=patient.phone,
                        patient_name=patient.name,
                        medicine_name=schedule.medicine_name
                    )
                
                logger.info(f"Stopped reminders for {schedule.medicine_name} for patient {patient_id}")
            
        except Exception as e:
            logger.error(f"Error stopping reminders: {str(e)}")
    
    def mark_missed_reminders(self) -> int:
        """Mark overdue reminders as missed"""
        try:
            db = SessionLocal()
            missed_count = 0
            
            # Find reminders that are overdue (dose time + 2 hours has passed)
            cutoff_time = datetime.now() - timedelta(hours=2)
            
            overdue_reminders = db.query(MedicineReminder).filter(
                and_(
                    MedicineReminder.status == 'sent',
                    MedicineReminder.dose_datetime < cutoff_time,
                    MedicineReminder.patient_response.is_(None)
                )
            ).all()
            
            for reminder in overdue_reminders:
                reminder.status = 'missed'
                # Update adherence
                self._update_adherence(db, reminder, 'missed')
                missed_count += 1
            
            db.commit()
            
            if missed_count > 0:
                logger.info(f"Marked {missed_count} reminders as missed")
            
            return missed_count
            
        except Exception as e:
            logger.error(f"Error marking missed reminders: {str(e)}")
            return 0
        finally:
            if db:
                db.close()