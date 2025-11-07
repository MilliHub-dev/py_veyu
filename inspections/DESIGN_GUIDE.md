# Inspection Slip Design Guide

## Overview

The vehicle inspection slip PDF has been designed with a professional, modern UI that includes the Veyu branding and color scheme.

## Design Features

### 1. Logo Integration

The inspection slip includes the Veyu logo at the top of each document:

- **Logo Location**: Top center of the first page
- **Logo Size**: 2 inches wide × 0.8 inches high
- **Fallback**: If logo image is not found, a styled text logo is used

#### Creating the Logo

To create the Veyu logo for inspection reports:

```bash
python manage.py create_inspection_logo
```

This will create a logo at `static/images/veyu-logo.png`

The logo features:
- Veyu brand name in white text
- "Redefining Mobility" tagline
- Primary brand color (#2c5282) background
- Rounded corners for modern look

### 2. Color Scheme

The design uses a professional color palette:

| Color | Hex Code | Usage |
|-------|----------|-------|
| Primary Blue | #2c5282 | Headers, borders, logo background |
| Accent Blue | #4299e1 | Accents and highlights |
| Dark Gray | #1a202c | Body text |
| Medium Gray | #4a5568 | Labels and secondary text |
| Light Gray | #718096 | Footer text |
| Background Gray | #f7fafc | Section backgrounds |
| Border Gray | #cbd5e0 | Borders and dividers |

#### Rating Colors

| Rating | Color | Hex Code |
|--------|-------|----------|
| Excellent | Light Green | #c6f6d5 |
| Good | Light Blue | #bee3f8 |
| Fair | Light Orange | #feebc8 |
| Poor | Light Red | #fed7d7 |

### 3. Typography

**Fonts:**
- Headers: Helvetica-Bold
- Body: Helvetica
- Emphasis: Helvetica-Oblique

**Font Sizes:**
- Main Title: 24pt
- Subtitle: 12pt
- Section Headers: 14pt
- Subsection Headers: 12pt
- Body Text: 10pt
- Labels: 10pt (bold)
- Footer: 8pt

### 4. Layout Components

#### Header Section
- Logo (centered)
- Decorative line (3pt, primary blue)
- Main title: "VEHICLE INSPECTION REPORT"
- Subtitle: "Professional Vehicle Inspection Service"
- Decorative line (1pt, border gray)
- Inspection ID badge with date

#### Section Headers
- Background color: #edf2f7
- Text color: Primary blue
- Top border: 3pt primary blue
- Padding: 10pt top/bottom, 15pt left
- Font: 14pt Helvetica-Bold

#### Information Tables
- Alternating row backgrounds
- Border lines between rows (#e2e8f0)
- Labels in bold, medium gray
- Values in dark gray
- Padding: 8pt top/bottom

#### Inspection Results
- Section icons (emoji) for visual identification
- Color-coded condition ratings
- Visual rating indicators (●●●●, ●●●○, etc.)
- Highlighted background for condition fields

#### Signature Section
- Styled signature boxes with borders
- Role icons for each signer
- Name pre-filled for each party
- Date fields
- Legal disclaimer note

#### Footer
- Horizontal rule (2pt, primary blue)
- Company information (left aligned)
- Generation timestamp (right aligned)
- Website and contact info
- Confidentiality disclaimer

### 5. Visual Elements

#### Icons
The design uses emoji icons for visual clarity:
- 🚗 Exterior
- 🪑 Interior
- ⚙️ Engine
- 🔧 Mechanical
- 🛡️ Safety
- 📄 Documentation
- 👨‍🔧 Inspector
- 👤 Customer
- 🏢 Dealer
- 📅 Date

#### Rating Indicators
Visual dots show rating at a glance:
- Excellent: ●●●● (4 filled dots)
- Good: ●●●○ (3 filled dots)
- Fair: ●●○○ (2 filled dots)
- Poor: ●○○○ (1 filled dot)

#### Decorative Elements
- Horizontal rules for section separation
- Rounded corners on signature boxes
- Background colors for emphasis
- Border highlights for important sections

### 6. Page Layout

**Margins:**
- Top: 72pt (1 inch)
- Bottom: 18pt
- Left: 72pt (1 inch)
- Right: 72pt (1 inch)

**Page Size:** A4 (210mm × 297mm)

**Spacing:**
- Between sections: 20pt
- Between subsections: 15pt
- Between items: 10pt
- After headers: 12pt

### 7. Template Types

#### Standard Template
- Basic inspection information
- All inspection sections
- Photos (optional)
- Recommendations (optional)
- Signature section

#### Detailed Template
- Extended inspection information
- Detailed analysis
- Additional notes sections
- Comprehensive photo documentation

#### Legal Compliance Template
- All standard content
- Legal disclaimers
- Compliance certifications
- Regulatory information
- Extended signature section

### 8. Branding Guidelines

#### Logo Usage
- Always use the official Veyu logo
- Maintain aspect ratio
- Ensure adequate white space around logo
- Use on white or light backgrounds

#### Color Usage
- Primary blue for main branding elements
- Use rating colors only for condition indicators
- Maintain sufficient contrast for readability
- Use gray tones for hierarchy

#### Typography
- Use Helvetica font family consistently
- Bold for emphasis and headers
- Regular weight for body text
- Italic for notes and disclaimers

### 9. Accessibility

The design follows accessibility best practices:
- High contrast text (WCAG AA compliant)
- Clear visual hierarchy
- Readable font sizes (minimum 8pt)
- Color is not the only indicator (icons + text)
- Structured layout for screen readers

### 10. Customization

To customize the design, modify these sections in `inspections/services.py`:

**Colors:**
```python
def _setup_custom_styles(self):
    # Modify color values in ParagraphStyle definitions
```

**Logo:**
```python
def _get_logo_path(self):
    # Update logo file paths
```

**Layout:**
```python
def _build_standard_content(self):
    # Modify content structure and spacing
```

**Rating Colors:**
```python
def _get_rating_color(self, rating: str):
    # Update rating color mappings
```

## Best Practices

1. **Consistency**: Use the same styling across all templates
2. **Branding**: Always include the Veyu logo and colors
3. **Readability**: Ensure text is clear and easy to read
4. **Professional**: Maintain a professional appearance
5. **Legal**: Include all required disclaimers and signatures
6. **Accessibility**: Follow accessibility guidelines
7. **Print-friendly**: Design works well in both digital and print formats

## Testing

Test the design by generating sample inspection reports:

```python
from inspections.services import DocumentManagementService

doc_service = DocumentManagementService()
document = doc_service.create_inspection_document(
    inspection=inspection,
    template_type='standard',
    include_photos=True,
    include_recommendations=True
)
```

## Support

For design questions or customization requests, contact the development team.
