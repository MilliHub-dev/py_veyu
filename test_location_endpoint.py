"""
Quick test script to verify the Location API endpoint is working
"""
import requests
import json

# Test configuration
BASE_URL = "http://127.0.0.1:8000"  # Change to your local dev server
# BASE_URL = "https://your-vercel-app.vercel.app"  # Or your Vercel URL

# Test data
test_location = {
    "country": "NG",
    "state": "Lagos",
    "city": "Lagos",
    "address": "123 Main Street, Victoria Island",
    "zip_code": "100001",
    "lat": 6.5244,
    "lng": 3.3792,
    "google_place_id": "ChIJOwg_06VLOxARYcsicBLL3NI"
}

def test_location_endpoint():
    """Test the location endpoint"""
    print("Testing Location API Endpoint...")
    print(f"Base URL: {BASE_URL}")
    
    # You'll need to replace this with a valid auth token
    # Get it from login or use an existing token
    auth_token = "YOUR_AUTH_TOKEN_HERE"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    # Test POST - Create location
    print("\n1. Testing POST /api/v1/accounts/locations/")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/accounts/locations/",
            headers=headers,
            json=test_location
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            location_id = response.json().get('id')
            print(f"✓ Location created successfully with ID: {location_id}")
            
            # Test GET - List locations
            print("\n2. Testing GET /api/v1/accounts/locations/")
            response = requests.get(
                f"{BASE_URL}/api/v1/accounts/locations/",
                headers=headers
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            # Test GET - Retrieve specific location
            print(f"\n3. Testing GET /api/v1/accounts/locations/{location_id}/")
            response = requests.get(
                f"{BASE_URL}/api/v1/accounts/locations/{location_id}/",
                headers=headers
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        else:
            print(f"✗ Failed to create location")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Location API Endpoint Test")
    print("=" * 60)
    test_location_endpoint()
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)
