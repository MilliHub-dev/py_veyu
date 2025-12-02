"""
Service for generating inspection slips (booking confirmations)
"""
import os
import io
import qrcode
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import logging

logger = logging.getLogger(__name__)


class InspectionSlipService:
    """
    Service for generating inspection slips (payment confirmation documents)
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='SlipTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='SlipSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Info text
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#718096'),
            spaceAfter=5,
            fontName='Helvetica'
        ))
    
    def generate_inspection_slip(self, inspection):
        """
        Generate inspection slip PDF
        
        Args:
            inspection: VehicleInspection instance
            
        Returns:
            tuple: (ContentFile, filename)
        """
        try:
            # Create buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            # Build content
            story = []
            
            # Header with logo
            story.extend(self._create_header())
            
            # Title
            story.append(Paragraph("INSPECTION BOOKING SLIP", self.styles['SlipTitle']))
            story.append(Paragraph("Payment Confirmed", self.styles['SlipSubtitle']))
            
            # Slip number box
            story.append(self._create_slip_number_box(inspection))
            story.append(Spacer(1, 20))
            
            # Payment confirmation
            story.append(self._create_payment_section(inspection))
            story.append(Spacer(1, 15))
            
            # Vehicle details
            story.append(self._create_vehicle_section(inspection))
            story.append(Spacer(1, 15))
            
            # Customer details
            story.append(self._create_customer_section(inspection))
            story.append(Spacer(1, 15))
            
            # Dealer details
            story.append(self._create_dealer_section(inspection))
            story.append(Spacer(1, 15))
            
            # QR code for verification
            story.append(self._create_qr_section(inspection))
            story.append(Spacer(1, 15))
            
            # Instructions
            story.append(self._create_instructions_section())
            
            # Footer
            story.append(Spacer(1, 20))
            story.append(self._create_footer())
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inspection_slip_{inspection.inspection_number}_{timestamp}.pdf"
            
            # Create ContentFile
            pdf_file = ContentFile(pdf_content, name=filename)
            
            return pdf_file, filename
            
        except Exception as e:
            logger.error(f"Error generating inspection slip: {str(e)}")
            raise
    
    def _create_header(self):
        """Create header with Veyu branding"""
        elements = []
        
        # Veyu logo/branding
        logo_table = Table(
            [['VEYU']],
            colWidths=[2*inch]
        )
        logo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        logo_table.hAlign = 'CENTER'
        elements.append(logo_table)
        elements.append(Spacer(1, 5))
        
        # Tagline
        tagline = Paragraph(
            "Redefining Mobility",
            self.styles['InfoText']
        )
        tagline.hAlign = 'CENTER'
        elements.append(tagline)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_slip_number_box(self, inspection):
        """Create prominent slip number box"""
        slip_table = Table(
            [[f"Slip Number: {inspection.inspection_number}"]],
            colWidths=[4*inch]
        )
        slip_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c5282')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2c5282')),
        ]))
        slip_table.hAlign = 'CENTER'
        return slip_table
    
    def _create_payment_section(self, inspection):
        """Create payment confirmation section"""
        data = [
            ['Payment Status:', 'PAID ✓'],
            ['Amount Paid:', f'₦{inspection.inspection_fee:,.2f}'],
            ['Payment Date:', inspection.paid_at.strftime('%B %d, %Y at %I:%M %p') if inspection.paid_at else 'N/A'],
            ['Payment Method:', inspection.payment_method.upper() if inspection.payment_method else 'N/A'],
            ['Transaction Ref:', inspection.payment_transaction.tx_ref if inspection.payment_transaction else 'N/A'],
        ]
        
        table = Table(data, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#38a169')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        
        return table
    
    def _create_vehicle_section(self, inspection):
        """Create vehicle details section"""
        vehicle = inspection.vehicle
        
        data = [
            ['Vehicle Information', ''],
            ['Make & Model:', f"{vehicle.make} {vehicle.model}"],
            ['Year:', str(vehicle.year)],
            ['VIN:', vehicle.vin if hasattr(vehicle, 'vin') else 'N/A'],
            ['License Plate:', vehicle.license_plate if hasattr(vehicle, 'license_plate') else 'N/A'],
            ['Inspection Type:', inspection.get_inspection_type_display()],
        ]
        
        table = Table(data, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('SPAN', (0, 0), (-1, 0)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        
        return table
    
    def _create_customer_section(self, inspection):
        """Create customer details section"""
        customer = inspection.customer
        
        data = [
            ['Customer Information', ''],
            ['Name:', customer.user.name],
            ['Phone:', customer.user.phone_number],
            ['Email:', customer.user.email],
        ]
        
        table = Table(data, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('SPAN', (0, 0), (-1, 0)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        
        return table
    
    def _create_dealer_section(self, inspection):
        """Create dealer details section"""
        dealer = inspection.dealer
        
        data = [
            ['Dealership Information', ''],
            ['Name:', dealer.business_name],
            ['Location:', dealer.location if hasattr(dealer, 'location') else 'N/A'],
            ['Phone:', dealer.user.phone_number],
        ]
        
        table = Table(data, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('SPAN', (0, 0), (-1, 0)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        
        return table
    
    def _create_qr_section(self, inspection):
        """Create QR code for verification"""
        # Generate QR code
        qr_data = f"VEYU-INSPECTION:{inspection.inspection_number}:{inspection.id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Create image
        qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        qr_image.hAlign = 'CENTER'
        
        # Create table with QR and text
        qr_text = Paragraph(
            "<b>Scan to Verify</b><br/>Show this slip to the dealer",
            self.styles['InfoText']
        )
        
        return qr_image
    
    def _create_instructions_section(self):
        """Create instructions for customer"""
        instructions = """
        <b>Instructions:</b><br/>
        1. Show this slip to the dealer when you arrive for inspection<br/>
        2. The dealer will scan the QR code or verify the slip number<br/>
        3. The inspection will be conducted after verification<br/>
        4. You will receive the inspection report after completion<br/>
        <br/>
        <b>Important:</b> This slip is valid for one inspection only.
        """
        
        para = Paragraph(instructions, self.styles['InfoText'])
        
        return para
    
    def _create_footer(self):
        """Create footer with contact info"""
        footer_text = """
        <para align=center>
        <b>Veyu - Redefining Mobility</b><br/>
        For support, contact: support@veyu.com | +234 XXX XXX XXXX<br/>
        www.veyu.com
        </para>
        """
        
        return Paragraph(footer_text, self.styles['InfoText'])
