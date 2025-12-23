"""
Catchy Prescription Renderer
Generates attractive, professional PDF prescriptions with bilingual support
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..shopify_models import PrescriptionRequest, PrescriptionItem

logger = logging.getLogger(__name__)

class CatchyPrescriptionRenderer:
    """Renders attractive, professional prescription PDFs"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 1.5 * cm
        self.brand_color = HexColor('#2E8B57')  # Sea Green - Ayurveda theme
        self.accent_color = HexColor('#FFD700')  # Gold accent
        self.text_color = HexColor('#333333')  # Dark gray
        self.light_gray = HexColor('#F5F5F5')  # Light background
        
        # Initialize fonts (fallback to default if custom fonts not available)
        self._setup_fonts()
        
        # Setup styles
        self.styles = self._create_styles()
    
    def _setup_fonts(self):
        """Setup custom fonts with fallback"""
        try:
            # Try to register custom fonts (Noto Sans for Unicode support)
            # For now, we'll use built-in fonts
            self.title_font = 'Helvetica-Bold'
            self.header_font = 'Helvetica-Bold'
            self.body_font = 'Helvetica'
            self.tamil_font = 'Helvetica'  # Fallback - ReportLab's built-in doesn't support Tamil well
            logger.info("Using built-in fonts for PDF rendering")
        except Exception as e:
            logger.warning(f"Font setup failed, using defaults: {e}")
            self.title_font = 'Helvetica-Bold'
            self.header_font = 'Helvetica-Bold'
            self.body_font = 'Helvetica'
            self.tamil_font = 'Helvetica'
    
    def _create_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Custom styles for catchy prescription
        styles.add(ParagraphStyle(
            name='CatchyTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.brand_color,
            fontName=self.title_font,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            name='CatchySubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.accent_color,
            fontName=self.header_font,
            alignment=TA_CENTER,
            spaceBefore=5,
            spaceAfter=15
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=self.brand_color,
            fontName=self.header_font,
            spaceBefore=15,
            spaceAfter=8,
            borderWidth=1,
            borderColor=self.brand_color,
            borderPadding=5,
            backColor=self.light_gray
        ))
        
        styles.add(ParagraphStyle(
            name='PatientInfo',
            parent=styles['Normal'],
            fontSize=10,
            fontName=self.body_font,
            textColor=self.text_color,
            spaceBefore=5,
            spaceAfter=5
        ))
        
        styles.add(ParagraphStyle(
            name='MedicineItem',
            parent=styles['Normal'],
            fontSize=10,
            fontName=self.body_font,
            textColor=self.text_color,
            leftIndent=10,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        return styles
    
    def _create_qr_code(self, data: str) -> Image:
        """Generate QR code for prescription tracking or payment"""
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to ReportLab Image
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            return Image(qr_buffer, width=2*cm, height=2*cm)
        except Exception as e:
            logger.warning(f"Failed to generate QR code: {e}")
            return None
    
    def _build_header(self, prescription: PrescriptionRequest) -> List:
        """Build catchy header section"""
        elements = []
        
        # Main title with brand styling
        title = Paragraph(
            "<b>🌿 AYUREZE HEALTHCARE 🌿</b>",
            self.styles['CatchyTitle']
        )
        elements.append(title)
        
        # Bilingual subtitle
        subtitle = Paragraph(
            "<i>Empowering Health through Authentic Ayurveda</i><br/>"
            "<font size=10>உண்மையான ஆயுர்வேதத்தின் மூலம் ஆரோக்கியத்தை வலுப்படுத்துதல்</font>",
            self.styles['CatchySubtitle']
        )
        elements.append(subtitle)
        
        # Contact info banner
        contact_info = Paragraph(
            "📞 +91-89689 68156 | 🌐 www.ayureze.in | ✉️ info@ayureze.in",
            self.styles['PatientInfo']
        )
        elements.append(contact_info)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_patient_doctor_section(self, prescription: PrescriptionRequest) -> List:
        """Build patient and doctor information section"""
        elements = []
        
        # Create patient and doctor info table
        patient = prescription.patient
        doctor = prescription.doctor
        
        # Prepare data for two-column layout
        data = [
            ['PATIENT DETAILS / நோயாளி விவரங்கள்', 'DOCTOR DETAILS / மருத்துவர் விவரங்கள்'],
            [
                f"👤 Name: {patient.name}\n"
                f"🎂 Age: {patient.age} years\n"
                f"🆔 Patient ID: {patient.patient_id or 'N/A'}\n"
                f"📞 Contact: {patient.contact or 'N/A'}",
                
                f"👨‍⚕️ Dr. {doctor.name if doctor else 'N/A'}\n"
                f"📋 Reg. No: {doctor.regn_no if doctor else 'N/A'}\n"
                f"📞 Contact: {doctor.contact if doctor else 'N/A'}\n"
                f"📅 Date: {datetime.now().strftime('%d/%m/%Y')}"
            ]
        ]
        
        # Create table with styling
        table = Table(data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), self.header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Content styling
            ('BACKGROUND', (0, 1), (-1, 1), self.light_gray),
            ('FONTNAME', (0, 1), (-1, 1), self.body_font),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, self.brand_color),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_diagnosis_section(self, prescription: PrescriptionRequest) -> List:
        """Build diagnosis and investigations section"""
        elements = []
        
        # Diagnosis header
        diag_header = Paragraph(
            "🔍 DIAGNOSIS (NIDANA) / நோய் கண்டறிதல்",
            self.styles['SectionHeader']
        )
        elements.append(diag_header)
        
        # Diagnosis content
        diagnosis_text = prescription.diagnosis or "Ayurvedic wellness consultation"
        diagnosis_para = Paragraph(f"<b>{diagnosis_text}</b>", self.styles['PatientInfo'])
        elements.append(diagnosis_para)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_medicines_section(self, prescription: PrescriptionRequest) -> List:
        """Build attractive medicines section with timing table"""
        elements = []
        
        # Medicines header
        med_header = Paragraph(
            "💊 PRESCRIBED MEDICINES / பரிந்துரைக்கப்பட்ட மருந்துகள்",
            self.styles['SectionHeader']
        )
        elements.append(med_header)
        
        # Create medicines table
        headers = ['Medicine / மருந்து', 'Dose / அளவு', 'Timing / நேரம்', 'Duration / காலம்']
        data = [headers]
        
        for item in prescription.prescriptions:
            # Format timing with emoji indicators
            timing_display = self._format_timing_display(item)
            
            data.append([
                f"🌿 {item.medicine}",
                item.dose,
                timing_display,
                item.duration or "As directed"
            ])
        
        # Create and style the medicines table
        med_table = Table(data, colWidths=[5*cm, 3*cm, 4*cm, 3*cm])
        med_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), self.header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Content styling
            ('FONTNAME', (0, 1), (-1, -1), self.body_font),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.light_gray, 'white']),
            ('GRID', (0, 0), (-1, -1), 1, self.brand_color),
        ]))
        
        elements.append(med_table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _format_timing_display(self, item: PrescriptionItem) -> str:
        """Format timing display with emojis and schedule info"""
        timing_map = {
            'before': '🍽️ Before meals',
            'after': '🍽️ After meals',
            'breakfast': '🌅 With breakfast',
            'lunch': '☀️ With lunch', 
            'dinner': '🌙 With dinner',
            'empty': '⏰ Empty stomach',
            'bedtime': '🛏️ Before sleep'
        }
        
        timing_lower = item.timing.lower()
        schedule = item.schedule.lower()
        
        # Enhanced timing display
        display = "🍽️ As directed"
        
        for key, value in timing_map.items():
            if key in timing_lower:
                display = value
                break
        
        # Add schedule info
        if 'once' in schedule or '1' in schedule:
            display += " (1x daily)"
        elif 'twice' in schedule or '2' in schedule:
            display += " (2x daily)"
        elif 'thrice' in schedule or '3' in schedule:
            display += " (3x daily)"
        
        return display
    
    def _build_instructions_section(self, prescription: PrescriptionRequest) -> List:
        """Build external therapy and instructions section"""
        elements = []
        
        # External therapy section
        if prescription.external_therapies:
            ext_header = Paragraph(
                "🌺 EXTERNAL THERAPY / புற சிகிச்சை",
                self.styles['SectionHeader']
            )
            elements.append(ext_header)
            
            for therapy in prescription.external_therapies:
                therapy_para = Paragraph(f"• {therapy}", self.styles['PatientInfo'])
                elements.append(therapy_para)
            
            elements.append(Spacer(1, 0.3*cm))
        
        # Doctor's notes
        if prescription.doctor_notes:
            notes_header = Paragraph(
                "📝 DOCTOR'S NOTES / மருத்துவர் குறிப்புகள்",
                self.styles['SectionHeader']
            )
            elements.append(notes_header)
            
            notes_para = Paragraph(prescription.doctor_notes, self.styles['PatientInfo'])
            elements.append(notes_para)
            elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_footer(self, prescription: PrescriptionRequest) -> List:
        """Build footer with QR code and signature"""
        elements = []
        
        # Create footer table with QR code and signature
        footer_data = [
            [
                "📱 Scan for Follow-up\nस्कैन फॉलो-अप के लिए\nபின்தொடர்ந்து ஸ்கேன் செய்யவும்",
                "Doctor's Signature\nமருத্துவর் கையொप்பம்\n\n_________________"
            ]
        ]
        
        # Add QR code if possible
        qr_data = f"Prescription for {prescription.patient.name} - {datetime.now().strftime('%Y%m%d')}"
        qr_code = self._create_qr_code(qr_data)
        
        if qr_code:
            footer_data[0][0] = qr_code
        
        footer_table = Table(footer_data, colWidths=[4*cm, 8*cm])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.body_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(footer_table)
        
        # Company footer
        company_footer = Paragraph(
            "<b>Ayurease Healthcare Pvt Ltd</b> | 157E/4, Main Road, North Kankankulam, Kovilpatti, Tamilnadu - 628503<br/>"
            "GST: 33ABACA2891B1Z6 | For consultation: +91-89689 68156 | support@ayureze.in",
            ParagraphStyle(
                'CompanyFooter',
                parent=self.styles['Normal'],
                fontSize=7,
                alignment=TA_CENTER,
                textColor=self.brand_color,
                spaceBefore=10
            )
        )
        elements.append(company_footer)
        
        return elements
    
    def generate_catchy_prescription(self, prescription: PrescriptionRequest) -> bytes:
        """Generate the complete catchy prescription PDF"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
                title=f"Prescription - {prescription.patient.name}"
            )
            
            # Build all sections
            elements = []
            elements.extend(self._build_header(prescription))
            elements.extend(self._build_patient_doctor_section(prescription))
            elements.extend(self._build_diagnosis_section(prescription))
            elements.extend(self._build_medicines_section(prescription))
            elements.extend(self._build_instructions_section(prescription))
            elements.extend(self._build_footer(prescription))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF bytes
            buffer.seek(0)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated catchy prescription PDF ({len(pdf_bytes)} bytes) for {prescription.patient.name}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate catchy prescription: {e}")
            raise ValueError(f"PDF generation failed: {e}")

# Global instance
catchy_renderer = CatchyPrescriptionRenderer()