"""
Advanced Escalation System for Medicine Reminders
Handles missed doses, family notifications, and emergency alerts
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# Fixed imports - use main database system
from ..database_models import MedicineSchedule, MedicineReminder, get_db_dependency
from sqlalchemy.orm import Session
from fastapi import Depends
from ..multilang.language_manager import language_manager
# Note: Import will be added when integrating with main app
# from ..medicine_reminders.kwikengage_client import KwikEngageClient

logger = logging.getLogger(__name__)

class EscalationSystem:
    """Advanced escalation system for medicine reminders"""
    
    def __init__(self):
        # Will be initialized when integrated with main app
        self.whatsapp_client = None
        
        # Escalation rules
        self.escalation_rules = {
            'first_missed': {
                'delay_minutes': 30,
                'max_attempts': 3,
                'notify_family': False
            },
            'critical_missed': {
                'delay_minutes': 15, 
                'max_attempts': 5,
                'notify_family': True
            },
            'emergency_threshold_hours': 24,  # Hours before emergency escalation
            'family_notification_delay': 2   # Hours before notifying family
        }
    
    def check_missed_doses(self, db_session: Session) -> Dict[str, Any]:
        """Check for missed doses and trigger escalations"""
        try:
                current_time = datetime.now()
                
                # Find overdue reminders (more than 30 minutes past scheduled time)
                overdue_threshold = current_time - timedelta(minutes=30)
                
                overdue_reminders = db_session.query(MedicineReminder).filter(
                    and_(
                        MedicineReminder.scheduled_time < overdue_threshold,
                        MedicineReminder.status == 'pending',
                        MedicineReminder.escalation_level < 3
                    )
                ).all()
                
                escalation_results = {
                    'checked_at': current_time.isoformat(),
                    'overdue_count': len(overdue_reminders),
                    'escalations_triggered': 0,
                    'family_notifications': 0,
                    'emergency_alerts': 0
                }
                
                for reminder in overdue_reminders:
                    escalation_result = self._escalate_reminder(reminder, db_session)
                    
                    if escalation_result['escalated']:
                        escalation_results['escalations_triggered'] += 1
                    if escalation_result['family_notified']:
                        escalation_results['family_notifications'] += 1
                    if escalation_result['emergency_alert']:
                        escalation_results['emergency_alerts'] += 1
                
                db_session.commit()
                return escalation_results
                
        except Exception as e:
            logger.error(f"Error checking missed doses: {str(e)}")
            return {'error': str(e), 'checked_at': datetime.now().isoformat()}
    
    def _escalate_reminder(self, reminder: MedicineReminder, session: Session) -> Dict[str, bool]:
        """Escalate a specific missed reminder"""
        try:
            current_time = datetime.now()
            schedule = session.query(MedicineSchedule).filter(
                MedicineSchedule.id == reminder.schedule_id
            ).first()
            
            if not schedule:
                return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
            
            # Calculate time since scheduled
            time_since_scheduled = current_time - reminder.scheduled_time
            hours_overdue = time_since_scheduled.total_seconds() / 3600
            
            # Determine escalation level
            is_critical = schedule.is_critical or False
            emergency_threshold = self.escalation_rules['emergency_threshold_hours']
            
            result = {'escalated': False, 'family_notified': False, 'emergency_alert': False}
            
            # Emergency escalation (24+ hours overdue)
            if hours_overdue >= emergency_threshold:
                result.update(self._trigger_emergency_alert(schedule, reminder, session))
                reminder.escalation_level = 5
                reminder.status = 'emergency'
                result['escalated'] = True
                result['emergency_alert'] = True
            
            # Critical medicine escalation
            elif is_critical and hours_overdue >= 2:
                result.update(self._notify_family_members(schedule, reminder, session))
                reminder.escalation_level = 4
                result['escalated'] = True  
                result['family_notified'] = True
            
            # Regular escalation
            elif reminder.escalation_level < 3:
                result.update(self._send_escalation_reminder(schedule, reminder, session))
                reminder.escalation_level += 1
                result['escalated'] = True
            
            # Update reminder timestamp
            reminder.updated_at = current_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error escalating reminder {reminder.id}: {str(e)}")
            return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
    
    def _send_escalation_reminder(self, schedule: MedicineSchedule, 
                                 reminder: MedicineReminder, session: Session) -> Dict[str, bool]:
        """Send escalated reminder to patient"""
        try:
            # Get patient's preferred language
            patient_language = getattr(schedule, 'patient_language', 'en')
            
            # Create escalation message
            escalation_message = language_manager.create_escalation_message(
                medicine_name=schedule.medicine_name,
                patient_name=schedule.patient_name,
                is_critical=schedule.is_critical or False,
                language=patient_language
            )
            
            # Send via WhatsApp
            message_id = self.whatsapp_client.send_medicine_reminder(
                patient_phone=schedule.patient_phone,
                patient_name=schedule.patient_name,
                medicine_name=schedule.medicine_name,
                dose_amount=schedule.dosage,
                dose_time=reminder.scheduled_time.strftime("%I:%M %p"),
                timing_type=schedule.timing_type,
                language=patient_language
            )
            
            if message_id:
                logger.info(f"Escalation reminder sent to {schedule.patient_phone}: {message_id}")
                return {'escalated': True, 'family_notified': False, 'emergency_alert': False}
            else:
                return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
                
        except Exception as e:
            logger.error(f"Error sending escalation reminder: {str(e)}")
            return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
    
    def _notify_family_members(self, schedule: MedicineSchedule, 
                              reminder: MedicineReminder, session: Session) -> Dict[str, bool]:
        """Notify family members about missed critical medicine"""
        try:
            # Get family contact info (you might store this in patient profile)
            family_phone = getattr(schedule, 'family_contact_phone', None)
            family_language = getattr(schedule, 'family_language', 'en')
            
            if not family_phone:
                logger.warning(f"No family contact for patient {schedule.patient_name}")
                return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
            
            # Create family notification message
            family_message = language_manager.create_family_notification(
                patient_name=schedule.patient_name,
                medicine_name=schedule.medicine_name,
                language=family_language
            )
            
            # Send to family member
            message_id = self.whatsapp_client.send_notification(
                phone=family_phone,
                message=family_message
            )
            
            if message_id:
                logger.info(f"Family notification sent for patient {schedule.patient_name}: {message_id}")
                return {'escalated': True, 'family_notified': True, 'emergency_alert': False}
            else:
                return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
                
        except Exception as e:
            logger.error(f"Error notifying family members: {str(e)}")
            return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
    
    def _trigger_emergency_alert(self, schedule: MedicineSchedule, 
                                reminder: MedicineReminder, session: Session) -> Dict[str, bool]:
        """Trigger emergency alert for 24+ hour missed critical medicine"""
        try:
            patient_language = getattr(schedule, 'patient_language', 'en')
            
            # Emergency message for patient
            emergency_message = language_manager.get_translation('emergency_missed', patient_language) + "\\n\\n"
            emergency_message += language_manager.get_translation('doctor_consultation', patient_language) + "\\n\\n"
            emergency_message += language_manager.get_translation('emergency_contact', patient_language)
            
            # Send to patient
            patient_message_id = self.whatsapp_client.send_notification(
                phone=schedule.patient_phone,
                message=emergency_message
            )
            
            # Also notify healthcare provider/emergency contact
            # This would integrate with your healthcare system
            self._notify_healthcare_provider(schedule, reminder)
            
            if patient_message_id:
                logger.critical(f"Emergency alert triggered for patient {schedule.patient_name}")
                return {'escalated': True, 'family_notified': True, 'emergency_alert': True}
            else:
                return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
                
        except Exception as e:
            logger.error(f"Error triggering emergency alert: {str(e)}")
            return {'escalated': False, 'family_notified': False, 'emergency_alert': False}
    
    def _notify_healthcare_provider(self, schedule: MedicineSchedule, reminder: MedicineReminder):
        """Notify healthcare provider about emergency situation"""
        try:
            # This would integrate with your hospital management system
            # For now, log the critical event
            logger.critical(f"""
MEDICAL EMERGENCY ALERT:
Patient: {schedule.patient_name}
Medicine: {schedule.medicine_name}
Status: 24+ hours overdue
Last Scheduled: {reminder.scheduled_time}
Patient Phone: {schedule.patient_phone}
""")
            
            # In production, you might:
            # 1. Send notification to doctor's dashboard
            # 2. Create urgent appointment
            # 3. Alert hospital emergency system
            # 4. Send SMS to healthcare provider
            
        except Exception as e:
            logger.error(f"Error notifying healthcare provider: {str(e)}")
    
    def create_smart_schedule(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent medicine schedule based on patient data"""
        try:
            # Smart timing based on medicine type and patient lifestyle
            smart_schedule = {
                'patient_id': patient_data['patient_id'],
                'optimized_timings': [],
                'meal_based_scheduling': True,
                'lifestyle_factors': []
            }
            
            for medicine in patient_data.get('medicines', []):
                optimal_times = self._calculate_optimal_timing(
                    medicine['name'],
                    medicine['frequency'],
                    medicine['timing'],
                    patient_data.get('lifestyle', {})
                )
                
                smart_schedule['optimized_timings'].append({
                    'medicine': medicine['name'],
                    'original_timing': medicine['timing'],
                    'optimized_timing': optimal_times,
                    'reasoning': self._get_timing_reasoning(medicine, optimal_times)
                })
            
            return smart_schedule
            
        except Exception as e:
            logger.error(f"Error creating smart schedule: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_optimal_timing(self, medicine_name: str, frequency: str, 
                                 timing: str, lifestyle: Dict) -> List[str]:
        """Calculate optimal timing based on medicine properties and lifestyle"""
        # This is where you'd implement AI/ML for optimal timing
        # For now, using rule-based logic
        
        optimal_times = []
        
        if 'morning' in timing.lower():
            # Consider patient's wake-up time
            wake_time = lifestyle.get('wake_up_time', '07:00')
            optimal_times.append(wake_time)
        
        if 'evening' in timing.lower():
            # Consider patient's sleep time  
            sleep_time = lifestyle.get('sleep_time', '22:00')
            evening_time = (datetime.strptime(sleep_time, '%H:%M') - timedelta(hours=2)).strftime('%H:%M')
            optimal_times.append(evening_time)
        
        return optimal_times
    
    def _get_timing_reasoning(self, medicine: Dict, optimal_times: List[str]) -> str:
        """Get reasoning for timing optimization"""
        return f"Optimized for {medicine['timing']} based on medicine properties and patient lifestyle"

# Global escalation system instance
escalation_system = EscalationSystem()