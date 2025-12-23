"""
PDF Form Filler Service
Fills prescription data directly onto the uploaded Ayureze PDF template
"""

import logging
from io import BytesIO
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

class PrescriptionPDFFiller:
    def __init__(self):
        self.template_path = "attached_assets/AYUREZE HEALTHCARE APP (1)_1758039743925.pdf"
        
    def fill_prescription_pdf(self, prescription):
        """
        Fill the actual Ayureze PDF template with prescription data
        """
        try:
            logger.info(f"Filling prescription PDF for patient: {getattr(prescription.patient, 'name', 'Unknown')}")
            
            # Check if template exists
            if not os.path.exists(self.template_path):
                logger.error(f"Template PDF not found at: {self.template_path}")
                raise FileNotFoundError(f"Template PDF not found: {self.template_path}")
            
            # Read the original PDF
            with open(self.template_path, 'rb') as template_file:
                reader = PdfReader(template_file)
                writer = PdfWriter()
                
                # Get the first page (assuming single page template)
                page = reader.pages[0]
                
                # Create overlay with prescription data
                overlay_buffer = self._create_data_overlay(prescription)
                overlay_reader = PdfReader(overlay_buffer)
                overlay_page = overlay_reader.pages[0]
                
                # Merge the overlay onto the template
                page.merge_page(overlay_page)
                writer.add_page(page)
                
                # Write to output buffer
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)
                
                pdf_data = output_buffer.getvalue()
                output_buffer.close()
                overlay_buffer.close()
                
                logger.info(f"Successfully filled PDF for patient: {getattr(prescription.patient, 'name', 'Unknown')}")
                return pdf_data
                
        except Exception as e:
            logger.error(f"Failed to fill prescription PDF: {e}")
            raise
    
    def _create_data_overlay(self, prescription):
        """
        Create an overlay with prescription data positioned accurately to match the template
        """
        buffer = BytesIO()
        
        # Get the actual PDF page dimensions for accurate positioning
        with open(self.template_path, 'rb') as template_file:
            reader = PdfReader(template_file)
            page = reader.pages[0]
            # Get the actual page dimensions from the PDF
            mediabox = page.mediabox
            actual_width = float(mediabox.width)
            actual_height = float(mediabox.height)
        
        # Create canvas with actual PDF dimensions
        c = canvas.Canvas(buffer, pagesize=(actual_width, actual_height))
        
        # Get prescription data
        patient_info = getattr(prescription, 'patient', None)
        doctor_info = getattr(prescription, 'doctor', None)
        diagnosis = getattr(prescription, 'diagnosis', '')
        external_therapy = getattr(prescription, 'external_therapy', '')
        next_review = getattr(prescription, 'next_review', '')
        
        logger.info(f"PDF dimensions: {actual_width} x {actual_height}")
        
        # PRECISE POSITIONING BASED ON PDF ANALYSIS
        # Using exact coordinates from template analysis (595.5 x 842.25 page)
        
        # PATIENT DETAILS SECTION (Left side) - EXACT positioning from analysis
        if patient_info:
            # Patient name - exactly after "Name / பெயர்:" at (145, 737.25)
            c.setFont("Helvetica", 10)
            c.drawString(145, 737.25, getattr(patient_info, 'name', ''))
            
            # Patient age - exactly after "Age / வயது:" at (115, 717.25)  
            age_text = str(getattr(patient_info, 'age', ''))
            c.setFont("Helvetica", 10)
            c.drawString(115, 717.25, age_text)
            
            # Sex field - after "Sex / பாலினம்:" at (285, 717.25)
            c.setFont("Helvetica", 9)
            c.drawString(285, 717.25, "_______")  # Placeholder for manual entry
            
            # OP/IP No - after "OP/IP No / பதிவு எண்:" at (165, 697.25)
            c.setFont("Helvetica", 9)
            c.drawString(165, 697.25, "__________")  # Placeholder
            
            # Patient ID - exactly after "Patient Id:" at (120, 677.25)
            c.setFont("Helvetica", 10)
            c.drawString(120, 677.25, getattr(patient_info, 'patient_id', ''))
            
            # Patient contact - exactly after "Contact / தொடர்பு:" at (140, 657.25)
            c.setFont("Helvetica", 10)
            c.drawString(140, 657.25, getattr(patient_info, 'contact', ''))
        
        # DOCTOR DETAILS SECTION (Right side) - More accurate positioning  
        if doctor_info:
            # Current date (after "Date / தேதி:")
            c.setFont("Helvetica", 10)
            c.drawString(445.5, 757.25, datetime.now().strftime("%d/%m/%Y"))
            
            # Doctor name (after "Doctor's Name:")
            c.setFont("Helvetica", 10)
            c.drawString(445.5, 737.25, getattr(doctor_info, 'name', ''))
            
            # Registration number (after "Regn No:")
            c.setFont("Helvetica", 10)
            c.drawString(445.5, 717.25, getattr(doctor_info, 'regn_no', ''))
            
            # Doctor contact (after "Contact:")
            c.setFont("Helvetica", 10)
            c.drawString(445.5, 697.25, getattr(doctor_info, 'contact', ''))
        
        # DIAGNOSIS SECTION (Right side, below doctor details)
        if diagnosis:
            # Diagnosis text area (after "Diagnosis (Nidana) / நோய் கண்டறிதல்")
            diagnosis_lines = self._wrap_text(diagnosis, 35)
            y_pos = 642.25
            c.setFont("Helvetica", 9)
            for line in diagnosis_lines[:4]:  # Max 4 lines for diagnosis
                c.drawString(415.5, y_pos, line)
                y_pos -= 12
        
        # MEDICINE SECTIONS - More accurate positioning with checkboxes
        self._fill_medicine_sections_accurate(c, prescription.prescriptions, actual_width, actual_height)
        
        # EXTERNAL THERAPY SECTION - Better positioning
        if external_therapy:
            therapy_lines = self._wrap_text(external_therapy, 70)
            y_pos = 372.25
            c.setFont("Helvetica", 10)
            for line in therapy_lines[:4]:  # Max 4 lines
                c.drawString(60, y_pos, line)
                y_pos -= 12
        
        # NEXT REVIEW DATE - More accurate positioning
        if next_review:
            c.setFont("Helvetica", 10)
            c.drawString(220, 312.25, next_review)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _fill_medicine_sections_accurate(self, canvas, prescriptions, page_width, page_height):
        """
        Fill medicine data in Before Food and After Food sections with accurate positioning and checkboxes
        """
        before_food_items = []
        after_food_items = []
        
        logger.info(f"Processing {len(prescriptions)} medicines for accurate PDF filling")
        
        # Categorize medicines with enhanced logic
        for item in prescriptions:
            medicine_name = getattr(item, 'medicine', '')
            dose = getattr(item, 'dose', '')
            schedule = getattr(item, 'schedule', '')
            timing = getattr(item, 'timing', '').lower()
            instructions = getattr(item, 'instructions', '')
            duration = getattr(item, 'duration', '')
            
            # Create medicine display
            medicine_display = f"{medicine_name}"
            if dose:
                medicine_display += f" - {dose}"
            
            # Enhanced timing determination with better logic
            breakfast_mark = ""
            lunch_mark = ""
            dinner_mark = ""
            
            # Improved schedule parsing
            if 'once' in schedule.lower() or '1' in schedule:
                if 'morning' in timing or 'breakfast' in timing:
                    breakfast_mark = "✓"
                elif 'evening' in timing or 'dinner' in timing or 'night' in timing:
                    dinner_mark = "✓"
                else:
                    breakfast_mark = "✓"  # Default morning
            elif 'twice' in schedule.lower() or '2' in schedule:
                breakfast_mark = "✓"
                dinner_mark = "✓"
            elif 'thrice' in schedule.lower() or 'three' in schedule.lower() or '3' in schedule:
                breakfast_mark = "✓"
                lunch_mark = "✓"
                dinner_mark = "✓"
            else:
                # Parse specific timing mentions
                if 'morning' in timing or 'breakfast' in timing:
                    breakfast_mark = "✓"
                if 'afternoon' in timing or 'lunch' in timing:
                    lunch_mark = "✓"
                if 'evening' in timing or 'dinner' in timing or 'night' in timing:
                    dinner_mark = "✓"
                if not any([breakfast_mark, lunch_mark, dinner_mark]):
                    breakfast_mark = "✓"  # Default
            
            # Enhanced before/after food categorization
            is_before_food = (
                'before' in timing or 'empty stomach' in timing or 
                'before' in instructions.lower() or 'empty' in instructions.lower() or
                'before food' in instructions.lower() or 'fasting' in instructions.lower()
            )
            
            medicine_entry = {
                'name': medicine_display,
                'instructions': instructions[:25] + "..." if len(instructions) > 25 else instructions,
                'breakfast': breakfast_mark,
                'lunch': lunch_mark,
                'dinner': dinner_mark
            }
            
            if is_before_food:
                before_food_items.append(medicine_entry)
                logger.info(f"Before Food: {medicine_name} - B:{breakfast_mark} L:{lunch_mark} D:{dinner_mark}")
            else:
                after_food_items.append(medicine_entry)
                logger.info(f"After Food: {medicine_name} - B:{breakfast_mark} L:{lunch_mark} D:{dinner_mark}")
        
        # MEDICINE SECTIONS - EXACT positioning from PDF analysis
        # Using precise coordinates from template analysis
        medicine_col_x = 60         # Medicine name column - exact from analysis
        breakfast_col_x = 375.5     # Breakfast checkbox column - exact from analysis
        lunch_col_x = 455.5         # Lunch checkbox column - exact from analysis  
        dinner_col_x = 535.5        # Dinner checkbox column - exact from analysis
        
        # Before Food section - exact positioning from analysis
        before_food_start_y = 552.25  # Exact Y from analysis
        row_height = 18               # Exact row height from analysis
        
        for i, medicine in enumerate(before_food_items[:3]):  # Max 3 rows in Before Food
            y_pos = before_food_start_y - (i * row_height)
            
            # Medicine name and dose - proper font size
            canvas.setFont("Helvetica", 9)  # Slightly smaller for better fit
            canvas.drawString(medicine_col_x, y_pos, medicine['name'])
            
            # Checkboxes for timing - using proper checkbox symbols with exact positioning
            if medicine['breakfast']:
                canvas.setFont("Helvetica", 10)  # Consistent checkbox size
                canvas.drawString(breakfast_col_x, y_pos, "☑")  # Checked box
            else:
                canvas.setFont("Helvetica", 10)  
                canvas.drawString(breakfast_col_x, y_pos, "☐")  # Empty box
                
            if medicine['lunch']:
                canvas.setFont("Helvetica", 10)  # Consistent checkbox size
                canvas.drawString(lunch_col_x, y_pos, "☑")
            else:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(lunch_col_x, y_pos, "☐")
                
            if medicine['dinner']:
                canvas.setFont("Helvetica", 10)  # Consistent checkbox size
                canvas.drawString(dinner_col_x, y_pos, "☑")
            else:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(dinner_col_x, y_pos, "☐")
        
        # AFTER FOOD SECTION - EXACT positioning from analysis
        after_food_start_y = 452.25  # Exact Y position from analysis
        
        for i, medicine in enumerate(after_food_items[:3]):  # Max 3 rows in After Food
            y_pos = after_food_start_y - (i * row_height)
            
            # Medicine name and dose - proper font size for After Food section
            canvas.setFont("Helvetica", 9)  # Consistent with Before Food section
            canvas.drawString(medicine_col_x, y_pos, medicine['name'])
            
            # Checkboxes for timing - consistent font sizes
            if medicine['breakfast']:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(breakfast_col_x, y_pos, "☑")
            else:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(breakfast_col_x, y_pos, "☐")
                
            if medicine['lunch']:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(lunch_col_x, y_pos, "☑")
            else:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(lunch_col_x, y_pos, "☐")
                
            if medicine['dinner']:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(dinner_col_x, y_pos, "☑")
            else:
                canvas.setFont("Helvetica", 10)
                canvas.drawString(dinner_col_x, y_pos, "☐")
        
        logger.info(f"Filled {len(before_food_items)} before food and {len(after_food_items)} after food medicines with checkboxes")
    
    def _wrap_text(self, text, max_length):
        """
        Wrap text to fit within specified length
        """
        if len(text) <= max_length:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines