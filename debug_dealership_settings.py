"""
Debug script to test dealership settings endpoint
Run this to see the actual error response from the API
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "https://dev.veyu.cc/api/v1/admin/dealership/settings/"
# Or use local: API_URL = "http://127.0.0.1:8000/api/v1/admin/dealership/settings/"

# Get JWT token from environment or prompt
JWT_TOKEN = os.getenv('JWT_TOKEN') or input("Enter your JWT token: ")

headers = {
    'Authorization': f'Bearer {JWT_TOKEN}',
    'Content-Type': 'application/json'
}

# Test 1: GET current settings
print("=" * 60)
print("TEST 1: Getting current dealership settings...")
print("=" * 60)
response = requests.get(API_URL, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    current_data = response.json().get('data', {})
    
    # Test 2: PUT with current data (should work)
    print("\n" + "=" * 60)
    print("TEST 2: Updating with current data...")
    print("=" * 60)
    
    # Prepare update payload
    update_payload = {
        'business_name': current_data.get('business_name'),
        'about': current_data.get('about'),
        'headline': current_data.get('headline'),
        'services': current_data.get('services', []),
        'contact_phone': current_data.get('contact_phone'),
        'contact_email': current_data.get('contact_email'),
    }
    
    # Add optional fields if present
    if current_data.get('slug'):
        update_payload['slug'] = current_data.get('slug')
    if current_data.get('location'):
        update_payload['location'] = current_data.get('location')
    
    print(f"Payload: {json.dumps(update_payload, indent=2)}")
    
    response = requests.put(API_URL, headers=headers, json=update_payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Identify the issue
    if response.status_code == 400:
        print("\n" + "=" * 60)
        print("ERROR ANALYSIS:")
        print("=" * 60)
        error_data = response.json()
        print(f"Error Message: {error_data.get('message')}")
        if 'details' in error_data:
            print(f"Details: {json.dumps(error_data['details'], indent=2)}")
        
        # Check services format
        print(f"\nServices type: {type(update_payload['services'])}")
        print(f"Services value: {update_payload['services']}")

else:
    print("\nCould not retrieve current settings. Check your JWT token.")
