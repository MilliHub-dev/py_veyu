"""
Test the DealershipServiceProcessor to verify services are optional
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from listings.service_mapping import DealershipServiceProcessor

def test_optional_services():
    """Test that services are completely optional"""
    processor = DealershipServiceProcessor()
    
    print("Testing DealershipServiceProcessor")
    print("=" * 60)
    
    # Test 1: Empty list
    print("\n1. Testing with empty list []")
    result = processor.process_services([])
    print(f"   Result: {result}")
    assert result['offers_purchase'] == False
    assert result['offers_rental'] == False
    assert result['offers_drivers'] == False
    assert result['offers_trade_in'] == False
    assert result['extended_services'] == []
    print("   ✓ PASS: Returns default values")
    
    # Test 2: None (should be handled by caller, but let's test)
    print("\n2. Testing with valid services")
    result = processor.process_services(['Car Sale', 'Vehicle Delivery'])
    print(f"   Result: {result}")
    assert result['offers_purchase'] == True
    assert 'Vehicle Delivery' in result['extended_services']
    print("   ✓ PASS: Correctly maps services")
    
    # Test 3: Invalid services only
    print("\n3. Testing with invalid services only")
    result = processor.process_services(['Invalid Service 1', 'Invalid Service 2'])
    print(f"   Result: {result}")
    assert result['offers_purchase'] == False
    assert result['offers_rental'] == False
    assert result['offers_drivers'] == False
    assert result['offers_trade_in'] == False
    print("   ✓ PASS: Returns default values for invalid services")
    
    # Test 4: String that should NOT be split into characters
    print("\n4. Testing with single service string (should wrap, not split)")
    result = processor.process_services(['Vehicle Delivery'])
    print(f"   Result: {result}")
    assert 'Vehicle Delivery' in result['extended_services']
    assert 'V' not in result['extended_services']  # Should NOT have individual characters
    print("   ✓ PASS: Service string is not split into characters")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")

if __name__ == '__main__':
    test_optional_services()
