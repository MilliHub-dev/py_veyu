"""
Django management command to create Veyu logo for inspection reports
Usage: python manage.py create_inspection_logo
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import os


class Command(BaseCommand):
    help = 'Create Veyu logo for inspection reports'

    def handle(self, *args, **options):
        self.stdout.write('Creating Veyu logo...')
        
        try:
            logo_path = self.create_veyu_logo()
            self.stdout.write(self.style.SUCCESS(f'Logo created successfully at: {logo_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create logo: {str(e)}'))
    
    def create_veyu_logo(self):
        """Create a simple Veyu logo"""
        # Create image with transparent background
        width, height = 400, 160
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Define colors
        primary_color = (44, 82, 130)  # #2c5282
        
        # Draw background rectangle with rounded corners
        draw.rounded_rectangle(
            [(10, 10), (width-10, height-10)],
            radius=20,
            fill=primary_color
        )
        
        # Try to use a nice font, fallback to default
        try:
            # Try to load a bold font
            font_large = ImageFont.truetype("arialbd.ttf", 60)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                font_large = ImageFont.truetype("Arial.ttf", 60)
                font_small = ImageFont.truetype("Arial.ttf", 20)
            except:
                # Fallback to default font
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Draw "VEYU" text
        text = "VEYU"
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 20
        
        # Draw text with white color
        draw.text((x, y), text, fill=(255, 255, 255), font=font_large)
        
        # Draw tagline
        tagline = "Redefining Mobility"
        bbox_tagline = draw.textbbox((0, 0), tagline, font=font_small)
        tagline_width = bbox_tagline[2] - bbox_tagline[0]
        
        x_tagline = (width - tagline_width) // 2
        y_tagline = y + text_height + 10
        
        draw.text((x_tagline, y_tagline), tagline, fill=(200, 200, 200), font=font_small)
        
        # Save the logo
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        logo_path = os.path.join(static_dir, 'veyu-logo.png')
        img.save(logo_path, 'PNG')
        
        return logo_path
