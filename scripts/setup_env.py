#!/usr/bin/env python3
"""
Environment Setup Helper Script

This script helps users set up their environment variables for Vercel deployment
by creating a .env file from the template and providing guidance.

Usage:
    python scripts/setup_env.py
"""

import os
import shutil
from pathlib import Path

def main():
    """Main setup function."""
    print("🚀 Veyu Environment Setup Helper")
    print("=" * 40)
    
    project_root = Path(__file__).parent.parent
    env_example = project_root / '.env.example'
    env_file = project_root / '.env'
    
    # Check if .env.example exists
    if not env_example.exists():
        print("❌ .env.example file not found!")
        return 1
    
    # Check if .env already exists
    if env_file.exists():
        response = input("📁 .env file already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("✅ Keeping existing .env file")
            print("💡 You can manually compare with .env.example for new variables")
            return 0
    
    # Copy .env.example to .env
    try:
        shutil.copy2(env_example, env_file)
        print("✅ Created .env file from template")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return 1
    
    print("\n📝 Next steps:")
    print("1. Edit the .env file with your actual values:")
    print(f"   - Open: {env_file}")
    print("   - Replace placeholder values with real credentials")
    print("\n2. Generate a Django secret key:")
    print("   python scripts/validate_env.py --generate-secret-key")
    print("\n3. Get required service credentials:")
    print("   - Database: Set up PostgreSQL (Neon, Supabase, etc.)")
    print("   - Email: Get SMTP credentials (Brevo, Gmail, SendGrid)")
    print("   - Media: Create Cloudinary account")
    print("   - SMS: Create Africa's Talking account")
    print("\n4. Validate your configuration:")
    print("   python scripts/validate_env.py")
    print("\n5. For Vercel deployment, set environment variables:")
    print("   vercel env add VARIABLE_NAME")
    
    print("\n🎯 Critical variables to set:")
    critical_vars = [
        "DJANGO_SECRET_KEY",
        "DATABASE_URL", 
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "CLOUDINARY_URL",
        "AFRICAS_TALKING_API_KEY"
    ]
    
    for var in critical_vars:
        print(f"   - {var}")
    
    return 0

if __name__ == '__main__':
    exit(main())