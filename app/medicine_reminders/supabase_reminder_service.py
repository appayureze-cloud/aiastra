"""
Supabase-based Medicine Reminder Service
Uses Supabase REST API instead of PostgreSQL direct connection
"""

import logging
import os
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import uuid

logger = logging.getLogger(__name__)

class SupabaseReminderService:
    """Medicine reminder service using Supabase REST API"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase credentials not found")
            self.supabase = None
            self.enabled = False
            return
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.enabled = True
            self.use_dedicated_tables = False  # Will be set by _ensure_tables_exist
            logger.info("✅ Supabase Reminder Service initialized")
            
            # Check which tables are available
            self._ensure_tables_exist()
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.enabled = False
    
    def _ensure_tables_exist(self):
        """Check if required tables exist"""
        try:
            # Try to query medicine_reminders table
            response = self.supabase.table('medicine_reminders').select('*').limit(1).execute()
            logger.info("✅ medicine_reminders table exists and ready")
            self.use_dedicated_tables = True
        except Exception as e:
            if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                logger.warning("⚠️ medicine_reminders table not found - using events table fallback")
                self.use_dedicated_tables = False
            else:
                logger.error(f"Error checking tables: {e}")
                self.use_dedicated_tables = False
    
    def create_reminder(
        self,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        medicine_name: str,
        dosage: str,
        frequency: str,
        times: List[str],
        start_date: str,
        end_date: str,
        instructions: Optional[str] = None,
        enable_whatsapp: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new medicine reminder
        
        Args:
            patient_id: Unique patient identifier
            patient_name: Patient's name
            patient_phone: Phone number for WhatsApp (with country code)
            medicine_name: Name of the medicine
            dosage: Dosage (e.g., "500mg", "2 tablets")
            frequency: How often (daily, twice_daily, etc.)
            times: List of times (e.g., ["09:00", "21:00"])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            instructions: Additional instructions
            enable_whatsapp: Whether to send WhatsApp reminders
        
        Returns:
            Created reminder data
        """
        if not self.enabled:
            raise Exception("Supabase Reminder Service not enabled")
        
        try:
            reminder_data = {
                'id': str(uuid.uuid4()),
                'patient_id': patient_id,
                'patient_name': patient_name,
                'patient_phone': patient_phone,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'frequency': frequency,
                'reminder_times': times,
                'start_date': start_date,
                'end_date': end_date,
                'instructions': instructions,
                'enable_whatsapp': enable_whatsapp,
                'is_active': True,
                'adherence_count': 0,
                'missed_count': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Try to insert into Supabase
            try:
                response = self.supabase.table('medicine_reminders').insert(reminder_data).execute()
                
                logger.info(f"✅ Created reminder for {patient_name} - {medicine_name}")
                return {
                    'success': True,
                    'reminder_id': reminder_data['id'],
                    'message': 'Medicine reminder created successfully',
                    'data': reminder_data
                }
                
            except Exception as e:
                # Table might not exist, store in events table as fallback
                if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                    logger.warning("medicine_reminders table not found, using events table")
                    
                    # Events table structure: id, user_id, session_id, name, meta, created_at
                    # user_id and session_id are UUID fields, so we leave them null and store patient_id in meta
                    event_data = {
                        'name': 'medicine_reminder',
                        'meta': reminder_data,  # Store all reminder data in meta field (including patient_id)
                        'created_at': datetime.now().isoformat()
                    }
                    
                    response = self.supabase.table('events').insert(event_data).execute()
                    
                    logger.info(f"✅ Stored reminder in events table (id: {response.data[0]['id']})")
                    
                    return {
                        'success': True,
                        'reminder_id': reminder_data['id'],
                        'event_id': response.data[0]['id'],
                        'message': 'Reminder created successfully (stored in events table)',
                        'data': reminder_data,
                        'fallback_mode': True
                    }
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            raise Exception(f"Failed to create reminder: {str(e)}")
    
    def get_patient_reminders(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all reminders for a patient"""
        if not self.enabled:
            return []
        
        try:
            # Try medicine_reminders table first
            try:
                response = self.supabase.table('medicine_reminders').select('*').eq('patient_id', patient_id).execute()
                
                if response.data:
                    logger.info(f"Found {len(response.data)} reminders for patient {patient_id}")
                    return response.data
                
            except Exception as e:
                if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                    # Fallback to events table
                    logger.info("Using events table for reminders")
                    response = self.supabase.table('events').select('*').eq('name', 'medicine_reminder').execute()
                    
                    # Extract reminder data from meta field, filter by patient_id
                    patient_reminders = [
                        event['meta'] for event in response.data 
                        if event.get('meta') and event['meta'].get('patient_id') == patient_id
                    ]
                    
                    return patient_reminders
                else:
                    raise
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching reminders: {e}")
            return []
    
    def get_reminder_by_id(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific reminder by ID"""
        if not self.enabled:
            return None
        
        try:
            try:
                response = self.supabase.table('medicine_reminders').select('*').eq('id', reminder_id).execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]
                    
            except Exception as e:
                if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                    # Fallback to events
                    response = self.supabase.table('events').select('*').eq('name', 'medicine_reminder').execute()
                    
                    for event in response.data:
                        if event.get('meta', {}).get('id') == reminder_id:
                            return event['meta']
                else:
                    raise
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching reminder: {e}")
            return None
    
    def update_reminder(self, reminder_id: str, updates: Dict[str, Any]) -> bool:
        """Update a reminder"""
        if not self.enabled:
            return False
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            try:
                response = self.supabase.table('medicine_reminders').update(updates).eq('id', reminder_id).execute()
                
                logger.info(f"✅ Updated reminder {reminder_id}")
                return True
                
            except Exception as e:
                if 'PGRST205' in str(e):
                    logger.warning("Cannot update in events table (read-only fallback)")
                    return False
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete/deactivate a reminder"""
        if not self.enabled:
            return False
        
        try:
            # Soft delete by setting is_active = False
            return self.update_reminder(reminder_id, {'is_active': False})
            
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False
    
    def log_adherence(self, reminder_id: str, taken: bool, timestamp: Optional[str] = None) -> bool:
        """Log patient adherence (took medicine or missed)"""
        if not self.enabled:
            return False
        
        try:
            adherence_log = {
                'id': str(uuid.uuid4()),
                'reminder_id': reminder_id,
                'taken': taken,
                'timestamp': timestamp or datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            try:
                # Try adherence_logs table
                response = self.supabase.table('adherence_logs').insert(adherence_log).execute()
                
            except Exception as e:
                if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                    # Fallback to events
                    event_data = {
                        'user_id': None,  # Could extract from reminder if needed
                        'name': 'medicine_adherence',
                        'meta': adherence_log,
                        'created_at': datetime.now().isoformat()
                    }
                    response = self.supabase.table('events').insert(event_data).execute()
                else:
                    raise
            
            # Update reminder counts
            reminder = self.get_reminder_by_id(reminder_id)
            if reminder:
                if taken:
                    new_count = reminder.get('adherence_count', 0) + 1
                    self.update_reminder(reminder_id, {'adherence_count': new_count})
                else:
                    new_count = reminder.get('missed_count', 0) + 1
                    self.update_reminder(reminder_id, {'missed_count': new_count})
            
            logger.info(f"✅ Logged adherence for reminder {reminder_id}: {'taken' if taken else 'missed'}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging adherence: {e}")
            return False
    
    def get_pending_reminders(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get reminders that should be sent now"""
        if not self.enabled:
            return []
        
        if not current_time:
            current_time = datetime.now()
        
        current_time_str = current_time.strftime("%H:%M")
        current_date = current_time.date().isoformat()
        
        try:
            # Get all active reminders
            all_reminders = []
            
            try:
                response = self.supabase.table('medicine_reminders').select('*').eq('is_active', True).execute()
                all_reminders = response.data
                
            except Exception as e:
                if 'PGRST205' in str(e) or 'PGRST204' in str(e):
                    # Fallback
                    response = self.supabase.table('events').select('*').eq('name', 'medicine_reminder').execute()
                    all_reminders = [event['meta'] for event in response.data if event.get('meta', {}).get('is_active', True)]
                else:
                    raise
            
            # Filter by date and time
            pending = []
            for reminder in all_reminders:
                # Check if current date is within reminder period
                start_date = reminder.get('start_date')
                end_date = reminder.get('end_date')
                
                if start_date <= current_date <= end_date:
                    # Check if current time matches any reminder time
                    reminder_times = reminder.get('reminder_times', [])
                    
                    for reminder_time in reminder_times:
                        # Allow 5-minute window
                        if abs(self._time_diff_minutes(current_time_str, reminder_time)) <= 5:
                            pending.append(reminder)
                            break
            
            return pending
            
        except Exception as e:
            logger.error(f"Error fetching pending reminders: {e}")
            return []
    
    def _time_diff_minutes(self, time1: str, time2: str) -> int:
        """Calculate difference between two times in minutes"""
        try:
            h1, m1 = map(int, time1.split(':'))
            h2, m2 = map(int, time2.split(':'))
            
            return abs((h1 * 60 + m1) - (h2 * 60 + m2))
        except:
            return 999  # Large number if parsing fails

# Global instance
supabase_reminder_service = SupabaseReminderService()
