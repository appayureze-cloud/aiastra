"""
PDF Template Content Extractor
Analyzes uploaded PDF templates and extracts structured prescription data
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from io import BytesIO
from ..shopify_models import PrescriptionRequest, PatientInfo, DoctorInfo, PrescriptionItem

logger = logging.getLogger(__name__)

class TemplateAnalyzer:
    """Analyzes PDF templates and extracts prescription content"""
    
    def __init__(self):
        self.field_patterns = {
            # Patient information patterns
            'patient_name': [
                r'name\s*/\s*பெயர்\s*:?\s*([^\n]+)',
                r'patient\s*name\s*:?\s*([^\n]+)',
                r'name\s*:?\s*([^\n]+)'
            ],
            'patient_age': [
                r'age\s*/\s*வயது\s*:?\s*(\d+)',
                r'age\s*:?\s*(\d+)',
                r'வயது\s*:?\s*(\d+)'
            ],
            'patient_contact': [
                r'contact\s*/\s*தொடர்பு\s*:?\s*([+\d\s-]+)',
                r'contact\s*:?\s*([+\d\s-]+)',
                r'phone\s*:?\s*([+\d\s-]+)'
            ],
            'patient_id': [
                r'patient\s*id\s*:?\s*([^\n]+)',
                r'id\s*:?\s*([A-Z0-9]+)'
            ],
            # Doctor information patterns
            'doctor_name': [
                r'doctor\'?s?\s*name\s*:?\s*([^\n]+)',
                r'dr\.?\s+([^\n]+)',
                r'physician\s*:?\s*([^\n]+)'
            ],
            'doctor_regn': [
                r'regn?\s*no\.?\s*:?\s*([^\n]+)',
                r'registration\s*:?\s*([^\n]+)',
                r'reg\.?\s*:?\s*([^\n]+)'
            ],
            'doctor_contact': [
                r'doctor.*contact\s*:?\s*([+\d\s-]+)',
                r'dr.*contact\s*:?\s*([+\d\s-]+)',
                r'physician.*phone\s*:?\s*([+\d\s-]+)'
            ],
            # Date and review patterns
            'date': [
                r'date\s*/\s*தேதி\s*:?\s*([^\n]+)',
                r'date\s*:?\s*([^\n]+)'
            ],
            'next_review': [
                r'next\s*review\s*/\s*அடுத்த\s*பரிசோதனை\s*:?\s*([^\n]+)',
                r'next\s*review\s*:?\s*([^\n]+)',
                r'follow\s*up\s*:?\s*([^\n]+)'
            ],
            # Diagnosis pattern
            'diagnosis': [
                r'diagnosis\s*\(nidana\)\s*/?\s*நோய்\s*கண்டறிதல்\s*:?\s*([^\n]+)',
                r'diagnosis\s*:?\s*([^\n]+)',
                r'condition\s*:?\s*([^\n]+)'
            ]
        }
    
    def extract_pdf_text_with_coordinates(self, pdf_bytes: bytes) -> List[Dict]:
        """Extract text with position coordinates from PDF"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_blocks = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_blocks.append({
                                    "text": span["text"].strip(),
                                    "x": span["bbox"][0],
                                    "y": span["bbox"][1], 
                                    "width": span["bbox"][2] - span["bbox"][0],
                                    "height": span["bbox"][3] - span["bbox"][1],
                                    "page": page_num,
                                    "font": span.get("font", ""),
                                    "size": span.get("size", 0)
                                })
            
            doc.close()
            logger.info(f"Extracted {len(text_blocks)} text blocks from PDF")
            return text_blocks
            
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return []
    
    def extract_field_value(self, text_blocks: List[Dict], patterns: List[str]) -> Optional[str]:
        """Extract field value using regex patterns"""
        # Combine all text for pattern matching
        full_text = " ".join([block["text"] for block in text_blocks])
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value not in ['.', '...', '____', '------']:
                    logger.debug(f"Extracted value: '{value}' using pattern: {pattern}")
                    return value
        
        return None
    
    def extract_medicines_from_sections(self, text_blocks: List[Dict]) -> List[PrescriptionItem]:
        """Extract medicines from Before Food and After Food sections"""
        medicines = []
        
        # Find section headers
        before_food_y = None
        after_food_y = None
        
        for block in text_blocks:
            text = block["text"].lower()
            if "before food" in text or "உணவுக்கு முன்" in text:
                before_food_y = block["y"]
            elif "after food" in text or "உணவுக்குப் பின்" in text:
                after_food_y = block["y"]
        
        # Extract medicines from each section
        for block in text_blocks:
            text = block["text"].strip()
            
            # Skip empty or header text
            if not text or len(text) < 3:
                continue
                
            # Skip common labels and symbols
            skip_patterns = [
                r'^(before|after|food|breakfast|lunch|dinner|காலை|மதியம்|இரவு)$',
                r'^[✓☑☐]+$',
                r'^[.\-_]+$'
            ]
            
            if any(re.match(pattern, text, re.IGNORECASE) for pattern in skip_patterns):
                continue
            
            # Detect medicine-like text (contains letters, possibly with dose info)
            if re.search(r'[a-zA-Z]{3,}', text):
                # Determine timing based on position
                timing = "After meals"  # Default
                if before_food_y and after_food_y:
                    if before_food_y < block["y"] < after_food_y:
                        timing = "Before meals"
                elif before_food_y and block["y"] > before_food_y:
                    timing = "Before meals"
                
                # Extract dose if present
                dose_match = re.search(r'(\d+(?:\.\d+)?\s*(?:ml|mg|g|tablets?|caps?))', text, re.IGNORECASE)
                dose = dose_match.group(1) if dose_match else "As directed"
                
                # Clean medicine name
                medicine_name = re.sub(r'\d+(?:\.\d+)?\s*(?:ml|mg|g|tablets?|caps?)', '', text, flags=re.IGNORECASE).strip()
                medicine_name = re.sub(r'[^\w\s]', ' ', medicine_name).strip()
                
                if len(medicine_name) >= 3:  # Valid medicine name
                    medicines.append(PrescriptionItem(
                        medicine=medicine_name,
                        dose=dose,
                        schedule="As prescribed",
                        timing=timing,
                        duration="As directed",
                        instructions="Take as prescribed by doctor",
                        quantity=1
                    ))
        
        logger.info(f"Extracted {len(medicines)} medicines from PDF sections")
        return medicines
    
    def extract_prescription_from_pdf(self, pdf_bytes: bytes) -> PrescriptionRequest:
        """Main method to extract complete prescription from PDF"""
        try:
            # Extract text blocks with coordinates
            text_blocks = self.extract_pdf_text_with_coordinates(pdf_bytes)
            
            if not text_blocks:
                raise ValueError("Could not extract text from PDF")
            
            # Extract patient information
            patient = PatientInfo(
                name=self.extract_field_value(text_blocks, self.field_patterns['patient_name']) or "Patient Name",
                age=int(age) if (age := self.extract_field_value(text_blocks, self.field_patterns['patient_age'])) and age.isdigit() else 30,
                patient_id=self.extract_field_value(text_blocks, self.field_patterns['patient_id']),
                contact=self.extract_field_value(text_blocks, self.field_patterns['patient_contact']),
                date=self.extract_field_value(text_blocks, self.field_patterns['date']),
                next_review=self.extract_field_value(text_blocks, self.field_patterns['next_review'])
            )
            
            # Extract doctor information
            doctor = DoctorInfo(
                name=self.extract_field_value(text_blocks, self.field_patterns['doctor_name']) or "Dr. Ayurveda Specialist",
                regn_no=self.extract_field_value(text_blocks, self.field_patterns['doctor_regn']) or "REG123456",
                contact=self.extract_field_value(text_blocks, self.field_patterns['doctor_contact'])
            )
            
            # Extract diagnosis
            diagnosis = self.extract_field_value(text_blocks, self.field_patterns['diagnosis']) or "Ayurvedic wellness consultation and treatment"
            
            # Extract medicines
            prescriptions = self.extract_medicines_from_sections(text_blocks)
            
            # Ensure at least one prescription item
            if not prescriptions:
                prescriptions = [PrescriptionItem(
                    medicine="Ayurvedic Wellness Supplement",
                    dose="As directed",
                    schedule="As prescribed",
                    timing="After meals",
                    duration="15 days",
                    instructions="Take as prescribed by doctor",
                    quantity=1
                )]
            
            prescription_request = PrescriptionRequest(
                patient=patient,
                diagnosis=diagnosis,
                prescriptions=prescriptions,
                doctor=doctor,
                external_therapies=["Traditional Ayurvedic therapy as prescribed"],
                doctor_notes="Follow prescribed regimen for optimal wellness"
            )
            
            logger.info(f"Successfully extracted prescription for patient: {patient.name}")
            return prescription_request
            
        except Exception as e:
            logger.error(f"Failed to extract prescription from PDF: {e}")
            raise ValueError(f"PDF extraction failed: {e}")

# Global instance
template_analyzer = TemplateAnalyzer()