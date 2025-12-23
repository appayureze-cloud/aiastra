"""
Complete Ayureze Healthcare Prescription PDF Template
Matches the exact format from the provided template
"""

import os
import logging
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, navy, darkgray
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

def generate_ayureze_prescription_pdf(prescription) -> bytes:
    """Generate prescription PDF matching Ayureze Healthcare template exactly"""
    try:
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=0.4*inch, 
            bottomMargin=0.4*inch, 
            leftMargin=0.4*inch, 
            rightMargin=0.4*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles matching template
        title_style = ParagraphStyle(
            'AyurezeTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=navy,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'AyurezeSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=navy,
            fontName='Helvetica'
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=black,
            fontName='Helvetica-Bold'
        )
        
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            textColor=black,
            fontName='Helvetica'
        )
        
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=3,
            textColor=black,
            fontName='Helvetica'
        )
        
        story = []
        
        # Header - Company Name and Branding
        story.append(Paragraph("AYUREZE HEALTHCARE", title_style))
        story.append(Paragraph("Empowering Health through Authentic Ayurveda", subtitle_style))
        
        # Contact information header (exactly as in template)
        contact_header = f"""
        <para align=center fontSize=9>
        Whatsapp: +91-89689 68156 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Mail: info@ayureze.in
        </para>
        """
        story.append(Paragraph(contact_header, small_style))
        story.append(Spacer(1, 12))
        
        # Patient and Doctor Details Section (exactly as in template)
        patient_info = getattr(prescription, 'patient', None)
        doctor_info = getattr(prescription, 'doctor', None)
        
        # Patient and Doctor details table (side by side layout)
        details_data = [
            ['Patient Details / நோயாளி விவரங்கள்:', '', '', '', 'Date / தேதி: ' + datetime.now().strftime("%d/%m/%Y")],
            ['', '', '', '', ''],
            ['Name / பெயர்: ' + getattr(patient_info, 'name', ''), '', '', '', "Doctor's Name: " + getattr(doctor_info, 'name', '')],
            ['', '', '', '', ''],
            ['Age / வயது: ' + str(getattr(patient_info, 'age', '')) + '     Sex / பாலினம்: ___________', '', '', '', 'Regn No: ' + getattr(doctor_info, 'regn_no', '')],
            ['', '', '', '', ''],
            ['OP/IP No / பதிவு எண்: _______________', '', '', '', 'Contact: ' + getattr(doctor_info, 'contact', '')],
            ['', '', '', '', ''],
            ['Patient Id: ' + getattr(patient_info, 'patient_id', ''), '', '', '', ''],
            ['Contact / தொடர்பு: ' + getattr(patient_info, 'contact', ''), '', '', '', '']
        ]
        
        details_table = Table(details_data, colWidths=[2.4*inch, 0.3*inch, 0.3*inch, 0.3*inch, 2.4*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 12))
        
        # Investigations and Diagnosis Section (side by side as in template)
        diagnosis_text = getattr(prescription, 'diagnosis', '')
        inv_diag_data = [
            ['Investigations (Pariksha) / பரிசோதனைகள்', '', '', '', 'Diagnosis (Nidana) / நோய் கண்டறிதல்'],
            ['', '', '', '', ''],
            ['', '', '', '', diagnosis_text],
            ['', '', '', '', ''],
            ['', '', '', '', ''],
            ['', '', '', '', ''],
            ['', '', '', '', '']
        ]
        
        inv_diag_table = Table(inv_diag_data, colWidths=[2.4*inch, 0.3*inch, 0.3*inch, 0.3*inch, 2.4*inch], rowHeights=[20, 8, 15, 15, 15, 15, 15])
        inv_diag_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (0, -1), 1, black),
            ('BOX', (4, 0), (4, -1), 1, black),
            ('LINEBELOW', (0, 0), (0, 0), 1, black),
            ('LINEBELOW', (4, 0), (4, 0), 1, black),
        ]))
        story.append(inv_diag_table)
        story.append(Spacer(1, 15))
        
        # Medicine prescription table with Before/After Food layout (populated with doctor's medicines)
        medicine_table_data = [
            # Header row with time columns
            ['', '', 'Breakfast\nகாலை', 'Lunch\nமதியம்', 'Dinner\nஇரவு'],
            # Before Food section header
            ['Before Food / உணவுக்கு முன்', '', '', '', ''],
        ]
        
        # Process ALL doctor's prescribed medicines (expand sections as needed)
        before_food_items = []
        after_food_items = []
        
        logger.info(f"Processing {len(prescription.prescriptions)} medicines for patient: {getattr(prescription.patient, 'name', 'Unknown')}")
        
        for item in prescription.prescriptions:
            medicine_name = getattr(item, 'medicine', '')
            dose = getattr(item, 'dose', '')
            schedule = getattr(item, 'schedule', '')
            timing = getattr(item, 'timing', '').lower()
            instructions = getattr(item, 'instructions', '')
            duration = getattr(item, 'duration', '')
            
            # Create comprehensive medicine display
            medicine_display = f"{medicine_name}"
            if dose:
                medicine_display += f" - {dose}"
            if duration:
                medicine_display += f" ({duration})"
            
            # Format instructions for display
            instruction_display = instructions[:35] + "..." if len(instructions) > 35 else instructions
            
            # Determine timing slots based on schedule and timing
            breakfast_slot = ""
            lunch_slot = ""
            dinner_slot = ""
            
            # Parse schedule for timing (Once daily, Twice daily, etc.)
            if 'once' in schedule.lower() or '1' in schedule:
                if 'morning' in timing or 'breakfast' in timing or 'after breakfast' in timing:
                    breakfast_slot = "✓"
                elif 'evening' in timing or 'dinner' in timing or 'after dinner' in timing:
                    dinner_slot = "✓"
                elif 'night' in timing or 'bedtime' in timing or 'sleep' in timing:
                    dinner_slot = "✓"
                else:
                    breakfast_slot = "✓"  # Default morning
                    
            elif 'twice' in schedule.lower() or '2' in schedule:
                breakfast_slot = "✓"
                dinner_slot = "✓"
                
            elif 'thrice' in schedule.lower() or 'three times' in schedule.lower() or '3' in schedule:
                breakfast_slot = "✓"
                lunch_slot = "✓"
                dinner_slot = "✓"
                
            else:
                # Default based on timing keywords
                if 'morning' in timing or 'breakfast' in timing:
                    breakfast_slot = "✓"
                if 'afternoon' in timing or 'lunch' in timing:
                    lunch_slot = "✓"
                if 'evening' in timing or 'night' in timing or 'dinner' in timing:
                    dinner_slot = "✓"
                if not any([breakfast_slot, lunch_slot, dinner_slot]):
                    breakfast_slot = "✓"  # Default to morning
            
            # Determine if before or after food (with more comprehensive checks)
            is_before_food = (
                'before' in timing or 'empty stomach' in timing or 
                'before' in instructions.lower() or 'empty' in instructions.lower() or
                'before food' in timing or 'before meal' in timing or
                'fasting' in instructions.lower() or 'sunrise' in timing
            )
            
            if is_before_food:
                before_food_items.append([medicine_display, instruction_display, breakfast_slot, lunch_slot, dinner_slot])
                logger.info(f"Added to Before Food: {medicine_name} - {schedule} - {timing}")
            else:
                after_food_items.append([medicine_display, instruction_display, breakfast_slot, lunch_slot, dinner_slot])
                logger.info(f"Added to After Food: {medicine_name} - {schedule} - {timing}")
        
        # Dynamically adjust table size based on medicines (minimum 3 rows each section)
        before_food_rows = max(3, len(before_food_items))
        after_food_rows = max(3, len(after_food_items))
        
        # Add before food items (expand as needed)
        while len(before_food_items) < before_food_rows:
            before_food_items.append(['', '', '', '', ''])
        
        for item in before_food_items[:before_food_rows]:
            medicine_table_data.append(item)
        
        # After Food section header
        medicine_table_data.append(['After Food / உணவுக்குப் பின்', '', 'Breakfast\nகாலை', 'Lunch\nமதியம்', 'Dinner\nஇரவு'])
        
        # Add after food items (expand as needed)
        while len(after_food_items) < after_food_rows:
            after_food_items.append(['', '', '', '', ''])
        
        for item in after_food_items[:after_food_rows]:
            medicine_table_data.append(item)
            
        logger.info(f"Medicine table created with {len(before_food_items)} before food and {len(after_food_items)} after food medicines")
        
        medicine_table = Table(medicine_table_data, colWidths=[2*inch, 1.2*inch, 0.9*inch, 0.9*inch, 0.9*inch])
        medicine_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # "Before Food" header styling
            ('BACKGROUND', (0, 1), (-1, 1), navy),
            ('TEXTCOLOR', (0, 1), (-1, 1), black),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            
            # "After Food" header styling  
            ('BACKGROUND', (0, 5), (-1, 5), navy),
            ('TEXTCOLOR', (0, 5), (-1, 5), black),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('ALIGN', (0, 5), (-1, 5), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -1), 8),
            ('ALIGN', (0, 2), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 2), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(medicine_table)
        story.append(Spacer(1, 15))
        
        # External Therapy section (exactly as in template with box)
        external_therapy_text = getattr(prescription, 'external_therapy', '')
        external_therapy_data = [
            ['External Therapy (Bahya Chikitsa) / புற சிகிச்சை:'],
            [''],
            [external_therapy_text if external_therapy_text else ''],
            [''],
            ['']
        ]
        
        external_therapy_table = Table(external_therapy_data, colWidths=[5.8*inch], rowHeights=[20, 15, 25, 15, 15])
        external_therapy_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, black),
            ('LINEBELOW', (0, 0), (0, 0), 1, black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(external_therapy_table)
        story.append(Spacer(1, 12))
        
        # Next Review and Doctor Signature (as in template)
        review_data = [
            ['Next Review / அடுத்த பரிசோதனை: _______________', '', '', "Doctor's Sign / கையொப்பம்"],
            ['', '', '', ''],
            ['', '', '', ''],
            ['', '', '', '']
        ]
        
        review_table = Table(review_data, colWidths=[3.5*inch, 0.5*inch, 0.5*inch, 1.5*inch])
        review_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(review_table)
        story.append(Spacer(1, 15))
        
        # Footer with complete company information (exactly as in template)
        footer_info = f"""
        <para align=center fontSize=8>
        <b>Empowering Health through Authentic Ayurveda</b><br/>
        📍 Serving Nationwide | +91-89689 68156 | www.ayureze.in 🌐<br/>
        💬 For follow-up consultation, scan the QR code<br/>
        ✉️Email: support@ayureze.in | Instagram: @ayureze.health<br/><br/>
        <b>Reg.Off: Ayurease Healthcare Pvt Ltd,</b><br/>
        157E/4, Main Road, North Kankankulam,<br/>
        Kovilpatti, Tamilnadu- 628503<br/>
        Gst: 33ABACA2891B1Z6
        </para>
        """
        story.append(Paragraph(footer_info, small_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated Ayureze prescription PDF for patient: {getattr(prescription.patient, 'name', 'Unknown')}")
        return pdf_data
        
    except Exception as e:
        logger.error(f"Failed to generate Ayureze prescription PDF: {e}")
        raise