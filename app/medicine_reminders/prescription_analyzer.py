"""
Prescription Analyzer for Medicine Reminder System
Extracts medicine schedules from prescription PDFs and data
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class PrescriptionAnalyzer:
    """Analyzes prescriptions to extract medicine schedules"""
    
    def __init__(self):
        # Common schedule patterns
        self.schedule_patterns = {
            # Pattern: Morning-Afternoon-Evening format
            r'(\d+)-(\d+)-(\d+)': self._parse_mae_schedule,
            r'(\d+) - (\d+) - (\d+)': self._parse_mae_schedule,
            r'(\d+)_(\d+)_(\d+)': self._parse_mae_schedule,
            
            # Pattern: "X times daily" format
            r'(\d+)\s*times?\s*(daily|per\s*day|a\s*day)': self._parse_times_daily,
            r'(\d+)x\s*(daily|per\s*day|a\s*day)': self._parse_times_daily,
            
            # Pattern: "Every X hours" format
            r'every\s*(\d+)\s*hours?': self._parse_every_hours,
            r'(\d+)\s*hourly': self._parse_every_hours,
            
            # Pattern: "Twice daily", "Once daily" etc.
            r'once\s*(daily|per\s*day|a\s*day)': lambda: {'morning': 1, 'afternoon': 0, 'evening': 0},
            r'twice\s*(daily|per\s*day|a\s*day)': lambda: {'morning': 1, 'afternoon': 0, 'evening': 1},
            r'thrice\s*(daily|per\s*day|a\s*day)': lambda: {'morning': 1, 'afternoon': 1, 'evening': 1},
            
            # Pattern: Specific times
            r'morning\s*only': lambda: {'morning': 1, 'afternoon': 0, 'evening': 0},
            r'evening\s*only': lambda: {'morning': 0, 'afternoon': 0, 'evening': 1},
            r'bedtime': lambda: {'morning': 0, 'afternoon': 0, 'evening': 1},
        }
        
        # Timing type patterns
        self.timing_patterns = {
            r'before\s*(food|meals?|eating|breakfast|lunch|dinner)': 'before_food',
            r'after\s*(food|meals?|eating|breakfast|lunch|dinner)': 'after_food',
            r'with\s*(food|meals?|eating|breakfast|lunch|dinner)': 'with_food',
            r'empty\s*stomach': 'empty_stomach',
            r'on\s*empty\s*stomach': 'empty_stomach',
            r'any\s*time': 'anytime',
            r'as\s*needed': 'anytime',
        }
        
        # Duration patterns
        self.duration_patterns = {
            r'(\d+)\s*days?': lambda match: int(match.group(1)),
            r'(\d+)\s*weeks?': lambda match: int(match.group(1)) * 7,
            r'(\d+)\s*months?': lambda match: int(match.group(1)) * 30,
            r'for\s*(\d+)\s*days?': lambda match: int(match.group(1)),
            r'for\s*(\d+)\s*weeks?': lambda match: int(match.group(1)) * 7,
            r'for\s*(\d+)\s*months?': lambda match: int(match.group(1)) * 30,
        }
        
        # Dose amount patterns
        self.dose_patterns = {
            r'(\d+)\s*tablet[s]?': lambda match: f"{match.group(1)} tablet{'s' if int(match.group(1)) > 1 else ''}",
            r'(\d+)\s*capsule[s]?': lambda match: f"{match.group(1)} capsule{'s' if int(match.group(1)) > 1 else ''}",
            r'(\d+)\s*ml': lambda match: f"{match.group(1)}ml",
            r'(\d+)\s*drops?': lambda match: f"{match.group(1)} drop{'s' if int(match.group(1)) > 1 else ''}",
            r'(\d+)\s*tsp': lambda match: f"{match.group(1)} tsp",
            r'(\d+)\s*tbsp': lambda match: f"{match.group(1)} tbsp",
        }
    
    def _parse_mae_schedule(self, match) -> Dict[str, int]:
        """Parse Morning-Afternoon-Evening schedule format"""
        morning = int(match.group(1))
        afternoon = int(match.group(2))
        evening = int(match.group(3))
        return {'morning': morning, 'afternoon': afternoon, 'evening': evening}
    
    def _parse_times_daily(self, match) -> Dict[str, int]:
        """Parse 'X times daily' format"""
        times = int(match.group(1))
        if times == 1:
            return {'morning': 1, 'afternoon': 0, 'evening': 0}
        elif times == 2:
            return {'morning': 1, 'afternoon': 0, 'evening': 1}
        elif times == 3:
            return {'morning': 1, 'afternoon': 1, 'evening': 1}
        elif times == 4:
            return {'morning': 2, 'afternoon': 0, 'evening': 2}
        else:
            # Distribute evenly
            return {'morning': times // 3, 'afternoon': times // 3, 'evening': times - 2 * (times // 3)}
    
    def _parse_every_hours(self, match) -> Dict[str, int]:
        """Parse 'every X hours' format"""
        hours = int(match.group(1))
        times_per_day = 24 // hours
        return self._parse_times_daily(type('MockMatch', (), {'group': lambda self, n: str(times_per_day)})())
    
    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract medicine schedule from PDF"""
        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                all_text += page.get_text()
            
            doc.close()
            
            return self.analyze_prescription_text(all_text)
            
        except Exception as e:
            logger.error(f"Error extracting from PDF: {str(e)}")
            return []
    
    def analyze_prescription_text(self, text: str) -> List[Dict[str, Any]]:
        """Analyze prescription text to extract medicine schedules"""
        try:
            medicines = []
            
            # Split text into lines and process each
            lines = text.split('\n')
            current_medicine = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line contains a medicine name
                # Look for patterns that suggest medicine names
                if self._is_medicine_line(line):
                    # Save previous medicine if exists
                    if current_medicine:
                        medicines.append(current_medicine)
                    
                    # Start new medicine
                    current_medicine = {
                        'medicine_name': self._extract_medicine_name(line),
                        'dose_amount': self._extract_dose_amount(line),
                        'schedule': self._extract_schedule(line),
                        'timing_type': self._extract_timing_type(line),
                        'duration_days': self._extract_duration(line),
                        'instructions': line
                    }
                
                elif current_medicine:
                    # This might be continuation of medicine details
                    schedule_update = self._extract_schedule(line)
                    if schedule_update and not current_medicine['schedule']:
                        current_medicine['schedule'] = schedule_update
                    
                    timing_update = self._extract_timing_type(line)
                    if timing_update != 'anytime' and current_medicine['timing_type'] == 'anytime':
                        current_medicine['timing_type'] = timing_update
                    
                    duration_update = self._extract_duration(line)
                    if duration_update and not current_medicine['duration_days']:
                        current_medicine['duration_days'] = duration_update
                    
                    dose_update = self._extract_dose_amount(line)
                    if dose_update and not current_medicine['dose_amount']:
                        current_medicine['dose_amount'] = dose_update
            
            # Add the last medicine
            if current_medicine:
                medicines.append(current_medicine)
            
            # Clean up and validate medicines
            validated_medicines = []
            for medicine in medicines:
                if self._validate_medicine(medicine):
                    validated_medicines.append(medicine)
            
            logger.info(f"Extracted {len(validated_medicines)} medicines from prescription")
            return validated_medicines
            
        except Exception as e:
            logger.error(f"Error analyzing prescription text: {str(e)}")
            return []
    
    def _is_medicine_line(self, line: str) -> bool:
        """Check if line contains a medicine name"""
        line_lower = line.lower()
        
        # Common medicine indicators
        medicine_indicators = [
            'tablet', 'capsule', 'syrup', 'drops', 'cream', 'ointment',
            'injection', 'powder', 'granules', 'liquid', 'suspension',
            'mg', 'ml', 'gm', 'mcg', 'dose', 'strength'
        ]
        
        # Check if line contains medicine indicators
        has_indicator = any(indicator in line_lower for indicator in medicine_indicators)
        
        # Check if line has reasonable length for medicine name
        has_reasonable_length = 5 <= len(line) <= 100
        
        # Check if line doesn't start with common instruction words
        instruction_starters = ['take', 'use', 'apply', 'give', 'administer', 'continue']
        starts_with_instruction = any(line_lower.startswith(starter) for starter in instruction_starters)
        
        return has_indicator and has_reasonable_length and not starts_with_instruction
    
    def _extract_medicine_name(self, line: str) -> str:
        """Extract medicine name from line"""
        # Remove common suffixes and dose information
        name = re.sub(r'\s*\d+\s*(mg|ml|gm|mcg|%)', '', line, flags=re.IGNORECASE)
        name = re.sub(r'\s*\(\s*.*?\s*\)', '', name)  # Remove parentheses content
        name = name.split('-')[0].strip()  # Take part before dash
        name = name.split(':')[0].strip()  # Take part before colon
        
        return name.strip()
    
    def _extract_dose_amount(self, text: str) -> str:
        """Extract dose amount from text"""
        text_lower = text.lower()
        
        for pattern, formatter in self.dose_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return formatter(match)
        
        # Default fallback
        return "1 tablet"
    
    def _extract_schedule(self, text: str) -> Optional[Dict[str, int]]:
        """Extract medicine schedule from text"""
        text_lower = text.lower()
        
        for pattern, parser in self.schedule_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                if callable(parser):
                    if hasattr(parser, '__code__') and parser.__code__.co_argcount > 0:
                        return parser(match)
                    else:
                        return parser()
                else:
                    return parser
        
        # Default schedule if nothing found
        return None
    
    def _extract_timing_type(self, text: str) -> str:
        """Extract timing type from text"""
        text_lower = text.lower()
        
        for pattern, timing_type in self.timing_patterns.items():
            if re.search(pattern, text_lower):
                return timing_type
        
        return 'anytime'  # Default
    
    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in days from text"""
        text_lower = text.lower()
        
        for pattern, parser in self.duration_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return parser(match)
        
        return None
    
    def _validate_medicine(self, medicine: Dict[str, Any]) -> bool:
        """Validate extracted medicine data"""
        # Must have medicine name
        if not medicine.get('medicine_name'):
            return False
        
        # Set defaults for missing values
        if not medicine.get('schedule'):
            medicine['schedule'] = {'morning': 1, 'afternoon': 0, 'evening': 0}
        
        if not medicine.get('dose_amount'):
            medicine['dose_amount'] = '1 tablet'
        
        if not medicine.get('timing_type'):
            medicine['timing_type'] = 'anytime'
        
        if not medicine.get('duration_days'):
            medicine['duration_days'] = 7  # Default 7 days
        
        return True
    
    def analyze_prescribed_medicines(self, prescribed_medicines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze prescribed medicines from database format"""
        try:
            analyzed_medicines = []
            
            for medicine in prescribed_medicines:
                # Extract schedule pattern
                schedule_text = medicine.get('schedule', '1-0-1')
                schedule = self._extract_schedule(schedule_text)
                if not schedule:
                    # Parse numeric schedule like "1-0-1"
                    parts = schedule_text.split('-')
                    if len(parts) == 3:
                        schedule = {
                            'morning': int(parts[0]),
                            'afternoon': int(parts[1]),
                            'evening': int(parts[2])
                        }
                    else:
                        schedule = {'morning': 1, 'afternoon': 0, 'evening': 1}
                
                # Extract timing type
                timing_text = medicine.get('timing', 'anytime')
                timing_type = self._extract_timing_type(timing_text)
                
                # Extract duration
                duration_text = medicine.get('duration', '7 days')
                duration_days = self._extract_duration(duration_text)
                if not duration_days:
                    duration_days = 7
                
                analyzed_medicine = {
                    'medicine_name': medicine.get('medicine_name', ''),
                    'dose_amount': medicine.get('dose', '1 tablet'),
                    'schedule': schedule,
                    'timing_type': timing_type,
                    'duration_days': duration_days,
                    'instructions': medicine.get('instructions', '')
                }
                
                if self._validate_medicine(analyzed_medicine):
                    analyzed_medicines.append(analyzed_medicine)
            
            logger.info(f"Analyzed {len(analyzed_medicines)} prescribed medicines")
            return analyzed_medicines
            
        except Exception as e:
            logger.error(f"Error analyzing prescribed medicines: {str(e)}")
            return []