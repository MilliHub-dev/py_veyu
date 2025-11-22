"""
Test script to verify services parsing logic
"""

import json

def test_services_parsing():
    """Test the services parsing logic that was fixed"""
    
    test_cases = [
        # Test case 1: Array of strings (correct format)
        {
            'input': ['Car Sale', 'Vehicle Delivery', 'Motorbike Sales & Leasing'],
            'expected_type': list,
            'expected_length': 3,
            'description': 'Array of service strings'
        },
        # Test case 2: JSON string array
        {
            'input': '["Car Sale", "Vehicle Delivery"]',
            'expected_type': list,
            'expected_length': 2,
            'description': 'JSON string array'
        },
        # Test case 3: Single string (should be wrapped in list)
        {
            'input': 'Vehicle Delivery',
            'expected_type': list,
            'expected_length': 1,
            'description': 'Single service string'
        },
    ]
    
    print("Testing Services Parsing Logic")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        services = test['input']
        print(f"\nTest {i}: {test['description']}")
        print(f"Input: {services}")
        print(f"Input type: {type(services)}")
        
        # Simulate the parsing logic from the fixed code
        if isinstance(services, list):
            print("✓ Already a list")
        elif isinstance(services, str):
            try:
                services = json.loads(services)
                print(f"✓ Parsed from JSON: {services}")
                if not isinstance(services, list):
                    print("✗ ERROR: JSON parsing resulted in non-list type")
                    continue
            except json.JSONDecodeError as e:
                print(f"✓ Not JSON, wrapping in list: [{services}]")
                services = [services]
        else:
            print(f"✓ Unexpected type, wrapping in list")
            services = [str(services)]
        
        # Validate result
        if not isinstance(services, list):
            print(f"✗ FAIL: Result is not a list: {type(services)}")
            continue
        
        # Filter and clean
        services = [str(s).strip() for s in services if s and isinstance(s, (str, int, float))]
        
        print(f"Final result: {services}")
        print(f"Result type: {type(services)}")
        print(f"Result length: {len(services)}")
        
        # Check if each item is a string (not individual characters)
        all_strings = all(isinstance(s, str) and len(s) > 1 for s in services)
        if all_strings:
            print("✓ PASS: All items are proper strings (not characters)")
        else:
            print("✗ FAIL: Some items are single characters")
            print(f"  Items: {services}")
        
        # Verify expected results
        if len(services) == test['expected_length']:
            print(f"✓ PASS: Length matches expected ({test['expected_length']})")
        else:
            print(f"✗ FAIL: Length {len(services)} != expected {test['expected_length']}")

if __name__ == '__main__':
    test_services_parsing()
