"""
Services for vehicle inspection system including PDF generation and document management
"""
import os
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
import logging
import os

from .models import VehicleInspection, InspectionDocument, InspectionPhoto, DigitalSignature

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """
    Service for generating inspection slip PDFs using ReportLab
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.logo_path = self._get_logo_path()
    
    def _get_logo_path(self):
        """Get the path to the Veyu logo"""
        # Check for logo in static files
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'veyu-logo.png'),
            os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'veyu-logo.png'),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _create_logo_header(self):
        """Create header with logo and company info"""
        elements = []
        
        if self.logo_path and os.path.exists(self.logo_path):
            # Add logo image
            try:
                logo = Image(self.logo_path, width=2*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 10))
            except Exception as e:
                logger.warning(f"Could not load logo: {str(e)}")
                # Fallback to text logo
                elements.extend(self._create_text_logo())
        else:
            # Create text-based logo if image not found
            elements.extend(self._create_text_logo())
        
        return elements
    
    def _create_text_logo(self):
        """Create a text-based logo as fallback"""
        elements = []
        
        # Create a styled text logo
        logo_table = Table(
            [['VEYU']],
            colWidths=[2*inch]
        )
        logo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 24),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        logo_table.hAlign = 'CENTER'
        elements.append(logo_table)
        elements.append(Spacer(1, 5))
        
        # Add tagline
        tagline = Paragraph(
            "Redefining Mobility",
            ParagraphStyle(
                name='Tagline',
                fontSize=10,
                textColor=colors.HexColor('#4a5568'),
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            )
        )
        elements.append(tagline)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF"""
        # Main title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d'),
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4a5568'),
            fontName='Helvetica-Oblique'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c5282'),
            fontName='Helvetica-Bold',
            borderPadding=5,
            leftIndent=0
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica-Bold'
        ))
        
        # Field label style
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            fontName='Helvetica-Bold'
        ))
        
        # Field value style
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a202c')
        ))
        
        # Info box style
        self.styles.add(ParagraphStyle(
            name='InfoBox',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c5282'),
            fontName='Helvetica-Oblique',
            leftIndent=10,
            rightIndent=10
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        ))
        
        # Rating badge styles
        self.styles.add(ParagraphStyle(
            name='RatingExcellent',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#22543d'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RatingGood',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c5282'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RatingFair',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#744210'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RatingPoor',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#742a2a'),
            fontName='Helvetica-Bold'
        ))
    
    def generate_inspection_pdf(
        self, 
        inspection: VehicleInspection, 
        template_type: str = 'standard',
        include_photos: bool = True,
        include_recommendations: bool = True,
        language: str = 'en'
    ) -> Tuple[ContentFile, str]:
        """
        Generate PDF document for vehicle inspection
        
        Returns:
            Tuple of (ContentFile, filename)
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content based on template type
            story = []
            
            if template_type == 'detailed':
                story = self._build_detailed_content(inspection, include_photos, include_recommendations)
            elif template_type == 'legal':
                story = self._build_legal_content(inspection, include_photos, include_recommendations)
            else:  # standard
                story = self._build_standard_content(inspection, include_photos, include_recommendations)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inspection_{inspection.id}_{template_type}_{timestamp}.pdf"
            
            # Create ContentFile
            content_file = ContentFile(pdf_content, name=filename)
            
            return content_file, filename
            
        except Exception as e:
            logger.error(f"Error generating PDF for inspection {inspection.id}: {str(e)}")
            raise
    
    def _build_standard_content(
        self, 
        inspection: VehicleInspection, 
        include_photos: bool, 
        include_recommendations: bool
    ) -> List:
        """Build content for standard inspection report"""
        story = []
        
        # Add logo header
        story.extend(self._create_logo_header())
        
        # Title section with decorative line
        story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#2c5282'), spaceBefore=5, spaceAfter=5))
        story.append(Paragraph("VEHICLE INSPECTION REPORT", self.styles['CustomTitle']))
        story.append(Paragraph("Professional Vehicle Inspection Service", self.styles['Subtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e0'), spaceBefore=5, spaceAfter=20))
        
        # Inspection ID badge
        inspection_badge = Table(
            [[f"Inspection ID: #{inspection.id}", f"Date: {inspection.inspection_date.strftime('%B %d, %Y')}"]],
            colWidths=[3*inch, 3*inch]
        )
        inspection_badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ]))
        story.append(inspection_badge)
        story.append(Spacer(1, 20))
        
        # Basic Information with colored header
        story.append(self._create_section_header("INSPECTION DETAILS"))
        
        # Overall rating badge with color coding
        rating_color = self._get_rating_color(inspection.overall_rating)
        rating_text = inspection.get_overall_rating_display() if inspection.overall_rating else 'Not Rated'
        
        basic_info = [
            ['Inspection Type:', inspection.get_inspection_type_display()],
            ['Overall Rating:', rating_text],
            ['Status:', inspection.get_status_display()],
            ['Completed:', inspection.completed_at.strftime('%B %d, %Y at %I:%M %p') if inspection.completed_at else 'In Progress'],
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 4*inch])
        basic_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (1, 1), (1, 1), rating_color),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.white if inspection.overall_rating in ['poor', 'fair'] else colors.HexColor('#1a202c')),
        ]))
        story.append(basic_table)
        story.append(Spacer(1, 20))
        
        # Vehicle Information with styled box
        story.append(self._create_section_header("VEHICLE INFORMATION"))
        
        vehicle_info = [
            ['Vehicle Name:', inspection.vehicle.name],
            ['Brand:', inspection.vehicle.brand],
            ['Model:', inspection.vehicle.model or 'N/A'],
            ['Color:', inspection.vehicle.color],
            ['Condition:', inspection.vehicle.get_condition_display()],
            ['Mileage:', f"{inspection.vehicle.mileage} km" if inspection.vehicle.mileage else 'N/A'],
        ]
        
        vehicle_table = Table(vehicle_info, colWidths=[2*inch, 4*inch])
        vehicle_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ]))
        story.append(vehicle_table)
        story.append(Spacer(1, 20))
        
        # Parties Information with icons
        story.append(self._create_section_header("PARTIES INVOLVED"))
        
        parties_info = [
            ['👨‍🔧 Inspector:', inspection.inspector.name],
            ['👤 Customer:', inspection.customer.user.name],
            ['🏢 Dealer:', inspection.dealer.business_name or inspection.dealer.user.name],
        ]
        
        parties_table = Table(parties_info, colWidths=[2*inch, 4*inch])
        parties_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(parties_table)
        story.append(Spacer(1, 20))
        
        # Inspection Results with visual indicators
        story.append(self._create_section_header("INSPECTION RESULTS"))
        
        # Add inspection sections with color-coded ratings
        sections = [
            ('🚗 Exterior', inspection.exterior_data),
            ('🪑 Interior', inspection.interior_data),
            ('⚙️ Engine', inspection.engine_data),
            ('🔧 Mechanical', inspection.mechanical_data),
            ('🛡️ Safety', inspection.safety_data),
            ('📄 Documentation', inspection.documentation_data),
        ]
        
        for section_name, section_data in sections:
            if section_data:
                # Section header with background
                story.append(Paragraph(f"{section_name}", self.styles['SubsectionHeader']))
                
                section_items = []
                for key, value in section_data.items():
                    formatted_key = key.replace('_', ' ').title()
                    formatted_value = str(value).title() if isinstance(value, str) else str(value)
                    
                    # Add color indicator for condition fields
                    if key.endswith('_condition') and value in ['excellent', 'good', 'fair', 'poor']:
                        section_items.append([
                            formatted_key + ':',
                            formatted_value,
                            self._get_rating_indicator(value)
                        ])
                    else:
                        section_items.append([formatted_key + ':', formatted_value, ''])
                
                if section_items:
                    section_table = Table(section_items, colWidths=[2.2*inch, 2.8*inch, 1*inch])
                    
                    # Apply styling with color coding
                    table_style = [
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
                        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7fafc')),
                    ]
                    
                    # Add color coding for condition rows
                    for i, item in enumerate(section_items):
                        if len(item) > 2 and item[2]:  # Has rating indicator
                            value = item[1].lower()
                            bg_color = self._get_rating_color(value)
                            table_style.append(('BACKGROUND', (2, i), (2, i), bg_color))
                    
                    section_table.setStyle(TableStyle(table_style))
                    story.append(section_table)
                    story.append(Spacer(1, 15))
        
        # Inspector Notes
        if inspection.inspector_notes:
            story.append(Paragraph("INSPECTOR NOTES", self.styles['SectionHeader']))
            story.append(Paragraph(inspection.inspector_notes, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Recommendations
        if include_recommendations and inspection.recommended_actions:
            story.append(Paragraph("RECOMMENDED ACTIONS", self.styles['SectionHeader']))
            for i, action in enumerate(inspection.recommended_actions, 1):
                story.append(Paragraph(f"{i}. {action}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Photos section
        if include_photos:
            photos = inspection.photos.all()
            if photos.exists():
                story.append(PageBreak())
                story.append(Paragraph("INSPECTION PHOTOS", self.styles['SectionHeader']))
                
                for photo in photos:
                    try:
                        # In a real implementation, you would download and include the actual images
                        story.append(Paragraph(f"{photo.get_category_display()}", self.styles['Heading4']))
                        if photo.description:
                            story.append(Paragraph(photo.description, self.styles['Normal']))
                        story.append(Spacer(1, 10))
                    except Exception as e:
                        logger.warning(f"Could not include photo {photo.id}: {str(e)}")
        
        # Signature section with styled boxes
        story.append(PageBreak())
        story.append(self._create_section_header("SIGNATURES & AUTHORIZATION"))
        story.append(Spacer(1, 20))
        
        # Signature boxes with better styling
        signature_boxes = [
            ['👨‍🔧 Inspector Signature', '📅 Date'],
            ['', ''],
            ['_' * 40, '_' * 20],
            [inspection.inspector.name, ''],
            ['', ''],
            ['👤 Customer Signature', '📅 Date'],
            ['', ''],
            ['_' * 40, '_' * 20],
            [inspection.customer.user.name, ''],
            ['', ''],
            ['🏢 Dealer Representative', '📅 Date'],
            ['', ''],
            ['_' * 40, '_' * 20],
            [inspection.dealer.business_name or inspection.dealer.user.name, ''],
        ]
        
        signature_table = Table(signature_boxes, colWidths=[4*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
            ('FONTNAME', (0, 10), (1, 10), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 5), (1, 5), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 10), (1, 10), colors.HexColor('#2c5282')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7fafc')),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#f7fafc')),
            ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#f7fafc')),
            ('BOX', (0, 0), (-1, 3), 1, colors.HexColor('#cbd5e0')),
            ('BOX', (0, 5), (-1, 8), 1, colors.HexColor('#cbd5e0')),
            ('BOX', (0, 10), (-1, 13), 1, colors.HexColor('#cbd5e0')),
        ]))
        story.append(signature_table)
        
        # Signature note
        story.append(Spacer(1, 20))
        signature_note = Paragraph(
            "<b>Note:</b> By signing this document, all parties acknowledge that they have reviewed the inspection "
            "results and agree to the findings as documented. Digital signatures are legally binding and verified "
            "through our secure signature system.",
            self.styles['InfoBox']
        )
        story.append(signature_note)
        
        # Footer with company info
        story.append(Spacer(1, 50))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2c5282')))
        story.append(Spacer(1, 10))
        
        # Footer content
        footer_data = [
            ['VEYU - Redefining Mobility', f"Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"],
            ['Vehicle Inspection System', 'www.veyu.cc | support@veyu.cc']
        ]
        
        footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#718096')),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(footer_table)
        
        # Disclaimer
        story.append(Spacer(1, 10))
        disclaimer = Paragraph(
            "This inspection report is confidential and intended solely for the parties involved. "
            "The information contained herein is accurate as of the inspection date and should not be used for any other purpose without authorization.",
            self.styles['Footer']
        )
        story.append(disclaimer)
        
        return story
    
    def _create_section_header(self, title: str):
        """Create a styled section header"""
        header_table = Table(
            [[title]],
            colWidths=[6*inch]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c5282')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('LINEABOVE', (0, 0), (-1, -1), 3, colors.HexColor('#2c5282')),
        ]))
        return header_table
    
    def _get_rating_color(self, rating: str):
        """Get color for rating"""
        rating_colors = {
            'excellent': colors.HexColor('#c6f6d5'),  # Light green
            'good': colors.HexColor('#bee3f8'),       # Light blue
            'fair': colors.HexColor('#feebc8'),       # Light orange
            'poor': colors.HexColor('#fed7d7'),       # Light red
        }
        return rating_colors.get(rating.lower() if rating else '', colors.HexColor('#f7fafc'))
    
    def _get_rating_indicator(self, rating: str):
        """Get visual indicator for rating"""
        indicators = {
            'excellent': '●●●●',
            'good': '●●●○',
            'fair': '●●○○',
            'poor': '●○○○',
        }
        return indicators.get(rating.lower() if rating else '', '')
    
    def _build_detailed_content(
        self, 
        inspection: VehicleInspection, 
        include_photos: bool, 
        include_recommendations: bool
    ) -> List:
        """Build content for detailed inspection report"""
        # For now, use standard content with additional details
        # In a real implementation, this would have more comprehensive sections
        return self._build_standard_content(inspection, include_photos, include_recommendations)
    
    def _build_legal_content(
        self, 
        inspection: VehicleInspection, 
        include_photos: bool, 
        include_recommendations: bool
    ) -> List:
        """Build content for legal compliance report"""
        # For now, use standard content with legal disclaimers
        # In a real implementation, this would include compliance certifications
        story = self._build_standard_content(inspection, include_photos, include_recommendations)
        
        # Add legal disclaimer
        story.append(PageBreak())
        story.append(Paragraph("LEGAL COMPLIANCE & DISCLAIMER", self.styles['SectionHeader']))
        
        disclaimer_text = """
        This inspection report has been prepared in accordance with applicable vehicle inspection standards 
        and regulations. The inspection was conducted by a qualified inspector and represents the condition 
        of the vehicle at the time of inspection. This report is valid for the purposes stated and should 
        not be used for any other purpose without proper authorization.
        
        The inspector and Veyu Platform disclaim any liability for damages or losses that may result from 
        reliance on this report beyond its intended scope and validity period.
        """
        
        story.append(Paragraph(disclaimer_text, self.styles['Normal']))
        
        return story


class DocumentManagementService:
    """
    Service for managing inspection documents and signatures
    """
    
    def __init__(self):
        self.pdf_service = PDFGenerationService()
    
    def create_inspection_document(
        self,
        inspection: VehicleInspection,
        template_type: str = 'standard',
        include_photos: bool = True,
        include_recommendations: bool = True,
        language: str = 'en',
        compliance_standards: List[str] = None
    ) -> InspectionDocument:
        """
        Create a new inspection document
        """
        try:
            # Generate PDF
            pdf_file, filename = self.pdf_service.generate_inspection_pdf(
                inspection=inspection,
                template_type=template_type,
                include_photos=include_photos,
                include_recommendations=include_recommendations,
                language=language
            )
            
            # Create document record
            document = InspectionDocument.objects.create(
                inspection=inspection,
                template_type=template_type,
                include_photos=include_photos,
                include_recommendations=include_recommendations,
                language=language,
                compliance_standards=compliance_standards or [],
                file_size=len(pdf_file.read()),
                page_count=self._estimate_page_count(inspection, include_photos)
            )
            
            # Reset file pointer and save
            pdf_file.seek(0)
            document.document_file.save(filename, pdf_file, save=True)
            
            # Create signature records for required parties
            self._create_signature_records(document)
            
            # Update document status
            document.status = 'ready'
            document.save()
            
            logger.info(f"Created inspection document {document.id} for inspection {inspection.id}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating inspection document for inspection {inspection.id}: {str(e)}")
            raise
    
    def _estimate_page_count(self, inspection: VehicleInspection, include_photos: bool) -> int:
        """Estimate the number of pages in the document"""
        base_pages = 2  # Basic info and inspection results
        
        if inspection.inspector_notes:
            base_pages += 1
        
        if include_photos and inspection.photos.exists():
            photo_pages = (inspection.photos.count() + 3) // 4  # 4 photos per page
            base_pages += photo_pages
        
        base_pages += 1  # Signature page
        
        return base_pages
    
    def _create_signature_records(self, document: InspectionDocument):
        """Create signature records for all required parties"""
        inspection = document.inspection
        
        # Inspector signature
        DigitalSignature.objects.create(
            document=document,
            signer=inspection.inspector,
            role='inspector'
        )
        
        # Customer signature
        DigitalSignature.objects.create(
            document=document,
            signer=inspection.customer.user,
            role='customer'
        )
        
        # Dealer signature
        DigitalSignature.objects.create(
            document=document,
            signer=inspection.dealer.user,
            role='dealer'
        )
    
    def submit_signature(
        self,
        document: InspectionDocument,
        signer_id: int,
        signature_data: Dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> DigitalSignature:
        """
        Submit a digital signature for a document
        """
        try:
            # Get signature record
            signature = document.signatures.get(signer_id=signer_id, status='pending')
            
            # Process signature
            signature.sign(signature_data, ip_address, user_agent)
            
            logger.info(f"Signature submitted for document {document.id} by user {signer_id}")
            return signature
            
        except DigitalSignature.DoesNotExist:
            logger.error(f"No pending signature found for user {signer_id} on document {document.id}")
            raise ValueError("No pending signature found for this user")
        except Exception as e:
            logger.error(f"Error submitting signature for document {document.id}: {str(e)}")
            raise
    
    def get_document_status(self, document: InspectionDocument) -> Dict:
        """
        Get comprehensive status of a document including signature progress
        """
        signatures = document.signatures.all()
        
        return {
            'document_id': document.id,
            'status': document.get_status_display(),
            'generated_at': document.generated_at,
            'expires_at': document.expires_at,
            'is_expired': document.is_expired,
            'total_signatures': signatures.count(),
            'completed_signatures': signatures.filter(status='signed').count(),
            'pending_signatures': signatures.filter(status='pending').count(),
            'signature_details': [
                {
                    'role': sig.get_role_display(),
                    'signer': sig.signer.name,
                    'status': sig.get_status_display(),
                    'signed_at': sig.signed_at
                }
                for sig in signatures
            ]
        }


class InspectionValidationService:
    """
    Service for validating inspection data and business logic
    """
    
    @staticmethod
    def validate_inspection_data(inspection_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate inspection data structure and required fields
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required sections
        required_sections = ['exterior', 'interior', 'engine', 'mechanical', 'safety']
        
        for section in required_sections:
            if section not in inspection_data:
                errors.append(f"Missing required section: {section}")
        
        # Validate condition values
        valid_conditions = ['excellent', 'good', 'fair', 'poor']
        
        for section_name, section_data in inspection_data.items():
            if isinstance(section_data, dict):
                for field, value in section_data.items():
                    if field.endswith('_condition') and value not in valid_conditions:
                        errors.append(f"Invalid condition value '{value}' in {section_name}.{field}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def calculate_overall_rating(inspection_data: Dict) -> str:
        """
        Calculate overall rating based on inspection data
        """
        condition_scores = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
        total_score = 0
        total_fields = 0
        
        for section_data in inspection_data.values():
            if isinstance(section_data, dict):
                for field, value in section_data.items():
                    if field.endswith('_condition') and value in condition_scores:
                        total_score += condition_scores[value]
                        total_fields += 1
        
        if total_fields == 0:
            return 'fair'  # Default rating
        
        average_score = total_score / total_fields
        
        if average_score >= 3.5:
            return 'excellent'
        elif average_score >= 2.5:
            return 'good'
        elif average_score >= 1.5:
            return 'fair'
        else:
            return 'poor'