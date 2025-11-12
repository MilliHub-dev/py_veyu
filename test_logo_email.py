#!/usr/bin/env python
"""
Test email with logo to verify it displays correctly.
"""
import os
import sys
import django
from pathlib import Path
import requests

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()