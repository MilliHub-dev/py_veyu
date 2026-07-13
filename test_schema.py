#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.test import Client

try:
    client = Client()
    response = client.get('/api/docs/?format=openapi')
    print(f"Schema generation status: {response.status_code}")
    print(f"Content type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code != 200:
        print(f"Error: {response.content}")
    else:
        print("Schema generated successfully")
        print(f"Content length: {len(response.content)} bytes")
        
except Exception as e:
    print(f"Schema generation failed: {e}")
    import traceback
    traceback.print_exc()
