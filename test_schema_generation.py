#!/usr/bin/env python3
"""
Test script to debug drf-yasg schema generation issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.test import RequestFactory
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

def test_schema_generation():
    """Test if schema generation works"""
    print("Testing drf-yasg schema generation...")
    
    try:
        # Create schema view like in urls.py
        api_info = openapi.Info(
            title="Veyu API Documentation",
            default_version='v1',
            description="Test schema generation",
        )
        
        schema_view = get_schema_view(
            api_info,
            public=True,
            authentication_classes=(),
            permission_classes=(permissions.AllowAny,),
        )
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/api/docs/?format=openapi')
        
        # Try to generate schema
        schema = schema_view(request=request)
        print(f"✅ Schema generation successful: {schema.status_code}")
        print(f"Content type: {schema.get('Content-Type', 'N/A')}")
        
        # Try to get the actual schema
        schema_json = schema.rendered_content
        print(f"Schema length: {len(schema_json)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_schema_generation()
    sys.exit(0 if success else 1)
