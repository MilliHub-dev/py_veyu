#!/usr/bin/env python
"""
Fix email template logos by uploading to Cloudinary and updating all templates.
"""
import os
import sys
import django
from pathlib import Path
import glob

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

# Cloudinary logo URL (publicly accessible)
# Option 1: Use a publicly hosted logo
LOGO_URL = "https://res.cloudinary.com/dcnq4b1mo/image/upload/v1/veyu/logo.png"

# Option 2: Use a simple text-based logo (fallback)
FALLBACK_LOGO_URL = "https://via.placeholder.com/150x50/4F46E5/FFFFFF?text=VEYU"

def update_template_logos():
    """Update all email templates to use the correct logo URL."""
    
    print("🔧 Fixing Email Template Logos")
    print("=" * 60)
    
    # Get all HTML templates
    template_dir = BASE_DIR / 'utils' / 'templates'
    html_files = list(template_dir.glob('*.html'))
    
    old_logo_url = "https://dev.veyu.cc/static/veyu/logo.png"
    new_logo_url = LOGO_URL
    
    updated_count = 0
    
    for html_file in html_files:
        try:
            # Read the file
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it contains the old logo URL
            if old_logo_url in content:
                # Replace the old URL with the new one
                new_content = content.replace(old_logo_url, new_logo_url)
                
                # Write back to file
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Updated: {html_file.name}")
                updated_count += 1
            else:
                print(f"⏭️  Skipped: {html_file.name} (no logo found)")
                
        except Exception as e:
            print(f"❌ Error updating {html_file.name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary: Updated {updated_count} template(s)")
    print(f"🔗 New logo URL: {new_logo_url}")
    print("\n💡 Next steps:")
    print("1. Upload your logo to Cloudinary at: veyu/logo.png")
    print("2. Or update LOGO_URL in this script to your logo's URL")
    print("3. Run this script again if needed")

if __name__ == "__main__":
    # Ask for confirmation
    print("\n⚠️  This will update all email templates with a new logo URL.")
    print(f"New logo URL: {LOGO_URL}")
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        update_template_logos()
    else:
        print("❌ Cancelled")
