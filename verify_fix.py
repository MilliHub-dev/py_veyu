"""
Verification script to confirm the dealership settings fix is in place
"""

import os
import sys

def check_file_content(filepath, search_strings, should_exist=True):
    """Check if certain strings exist or don't exist in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = []
    for search_str in search_strings:
        exists = search_str in content
        status = "✓" if (exists == should_exist) else "✗"
        expected = "present" if should_exist else "absent"
        actual = "present" if exists else "absent"
        results.append({
            'status': status,
            'search': search_str[:50] + '...' if len(search_str) > 50 else search_str,
            'expected': expected,
            'actual': actual,
            'passed': exists == should_exist
        })
    return results

print("=" * 80)
print("DEALERSHIP SETTINGS FIX VERIFICATION")
print("=" * 80)

# Check 1: Verify required fields validation was removed from SettingsView
print("\n1. Checking listings/api/dealership_views.py - SettingsView")
print("-" * 80)

# Read the file and check the SettingsView section specifically
with open('listings/api/dealership_views.py', 'r', encoding='utf-8') as f:
    content = f.read()
    # Find the SettingsView section
    settings_view_start = content.find('class SettingsView')
    settings_view_end = content.find('class ', settings_view_start + 1)
    if settings_view_end == -1:
        settings_view_end = len(content)
    settings_view_content = content[settings_view_start:settings_view_end]

results = []
# Check that the comment exists
has_comment = "# Note: All fields are optional for partial updates" in settings_view_content
results.append({
    'status': "✓" if has_comment else "✗",
    'search': "# Note: All fields are optional for partial updates",
    'expected': 'present',
    'actual': 'present' if has_comment else 'absent',
    'passed': has_comment
})

# Check that required_fields validation doesn't exist in SettingsView
has_required_validation = "required_fields = ['business_name'" in settings_view_content
results.append({
    'status': "✓" if not has_required_validation else "✗",
    'search': "required_fields = ['business_name'",
    'expected': 'absent',
    'actual': 'present' if has_required_validation else 'absent',
    'passed': not has_required_validation
})

for r in results:
    print(f"{r['status']} {r['search']}: Expected {r['expected']}, Found {r['actual']}")

all_passed = all(r['passed'] for r in results)

# Check 2: Verify services parsing fix
print("\n2. Checking service parsing fix in dealership_views.py")
print("-" * 80)
results2 = check_file_content(
    'listings/api/dealership_views.py',
    [
        "services = [str(services)]",  # Should exist (the fix)
        "services = list(services)",  # Should NOT exist (the bug)
    ]
)
results2[1]['expected'] = 'absent'
results2[1]['passed'] = not (results2[1]['actual'] == 'present')
results2[1]['status'] = "✓" if results2[1]['passed'] else "✗"

for r in results2:
    print(f"{r['status']} {r['search']}: Expected {r['expected']}, Found {r['actual']}")

all_passed = all_passed and all(r['passed'] for r in results2)

# Check 3: Verify service_mapping.py fix
print("\n3. Checking service parsing fix in service_mapping.py")
print("-" * 80)
results3 = check_file_content(
    'listings/service_mapping.py',
    [
        "selected_services = [selected_services]",  # Should exist (the fix)
        "raise ValidationError(\"At least one service must be selected\")",  # Should NOT exist
    ]
)
results3[1]['expected'] = 'absent'
results3[1]['passed'] = not (results3[1]['actual'] == 'present')
results3[1]['status'] = "✓" if results3[1]['passed'] else "✗"

for r in results3:
    print(f"{r['status']} {r['search']}: Expected {r['expected']}, Found {r['actual']}")

all_passed = all_passed and all(r['passed'] for r in results3)

# Check 4: Verify serializer fix
print("\n4. Checking serializer fix in serializers.py")
print("-" * 80)
results4 = check_file_content(
    'listings/api/serializers.py',
    [
        "services = serializers.ListField(read_only=True)",  # Should exist
    ]
)

for r in results4:
    print(f"{r['status']} {r['search']}: Expected {r['expected']}, Found {r['actual']}")

all_passed = all_passed and all(r['passed'] for r in results4)

# Final result
print("\n" + "=" * 80)
if all_passed:
    print("✓ ALL CHECKS PASSED - Fix is correctly applied to the code")
    print("\n⚠️  IMPORTANT: You need to RESTART your Django server for changes to take effect!")
    print("   - If running locally: Stop and restart 'python manage.py runserver'")
    print("   - If on Vercel: Redeploy or wait for automatic deployment")
else:
    print("✗ SOME CHECKS FAILED - Please review the code changes")
print("=" * 80)
