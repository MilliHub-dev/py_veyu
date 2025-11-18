"""
Script to verify BusinessVerificationSubmission model relationships
without running full Django tests.

This script checks:
1. OneToOneField relationships exist
2. on_delete=CASCADE is configured
3. related_name='verification_submission' is set
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.db.models import CASCADE
from accounts.models import BusinessVerificationSubmission, Dealership, Mechanic


def verify_relationships():
    """Verify model relationships are correctly configured"""
    
    print("=" * 70)
    print("VERIFYING BUSINESSVERIFICATIONSUBMISSION MODEL RELATIONSHIPS")
    print("=" * 70)
    print()
    
    # Get the model fields
    dealership_field = BusinessVerificationSubmission._meta.get_field('dealership')
    mechanic_field = BusinessVerificationSubmission._meta.get_field('mechanic')
    
    # Check 1: Verify OneToOneField relationships
    print("✓ CHECK 1: OneToOneField Relationships")
    print("-" * 70)
    print(f"  Dealership field type: {dealership_field.__class__.__name__}")
    print(f"  Mechanic field type: {mechanic_field.__class__.__name__}")
    
    is_dealership_one_to_one = dealership_field.__class__.__name__ == 'OneToOneField'
    is_mechanic_one_to_one = mechanic_field.__class__.__name__ == 'OneToOneField'
    
    if is_dealership_one_to_one and is_mechanic_one_to_one:
        print("  ✓ PASS: Both fields are OneToOneField")
    else:
        print("  ✗ FAIL: Fields are not OneToOneField")
        return False
    print()
    
    # Check 2: Verify on_delete=CASCADE
    print("✓ CHECK 2: CASCADE Deletion Behavior")
    print("-" * 70)
    print(f"  Dealership on_delete: {dealership_field.remote_field.on_delete}")
    print(f"  Mechanic on_delete: {mechanic_field.remote_field.on_delete}")
    
    is_dealership_cascade = dealership_field.remote_field.on_delete == CASCADE
    is_mechanic_cascade = mechanic_field.remote_field.on_delete == CASCADE
    
    if is_dealership_cascade and is_mechanic_cascade:
        print("  ✓ PASS: Both fields use CASCADE deletion")
    else:
        print("  ✗ FAIL: CASCADE deletion not configured correctly")
        return False
    print()
    
    # Check 3: Verify related_name
    print("✓ CHECK 3: Related Name Configuration")
    print("-" * 70)
    print(f"  Dealership related_name: {dealership_field.remote_field.related_name}")
    print(f"  Mechanic related_name: {mechanic_field.remote_field.related_name}")
    
    is_dealership_related_name = dealership_field.remote_field.related_name == 'verification_submission'
    is_mechanic_related_name = mechanic_field.remote_field.related_name == 'verification_submission'
    
    if is_dealership_related_name and is_mechanic_related_name:
        print("  ✓ PASS: Both fields have correct related_name='verification_submission'")
    else:
        print("  ✗ FAIL: related_name not configured correctly")
        return False
    print()
    
    # Check 4: Verify reverse relationship exists
    print("✓ CHECK 4: Reverse Relationship Accessibility")
    print("-" * 70)
    
    # Check if Dealership has verification_submission attribute
    has_dealership_reverse = hasattr(Dealership, 'verification_submission')
    has_mechanic_reverse = hasattr(Mechanic, 'verification_submission')
    
    print(f"  Dealership.verification_submission exists: {has_dealership_reverse}")
    print(f"  Mechanic.verification_submission exists: {has_mechanic_reverse}")
    
    if has_dealership_reverse and has_mechanic_reverse:
        print("  ✓ PASS: Reverse relationships are accessible")
    else:
        print("  ✗ FAIL: Reverse relationships not accessible")
        return False
    print()
    
    # Check 5: Verify model docstrings document relationships
    print("✓ CHECK 5: Model Documentation")
    print("-" * 70)
    
    bvs_doc = BusinessVerificationSubmission.__doc__
    dealership_doc = Dealership.__doc__
    mechanic_doc = Mechanic.__doc__
    
    bvs_documented = bvs_doc and 'OneToOneField' in bvs_doc and 'CASCADE' in bvs_doc
    dealership_documented = dealership_doc and 'verification_submission' in dealership_doc
    mechanic_documented = mechanic_doc and 'verification_submission' in mechanic_doc
    
    print(f"  BusinessVerificationSubmission documented: {bvs_documented}")
    print(f"  Dealership documented: {dealership_documented}")
    print(f"  Mechanic documented: {mechanic_documented}")
    
    if bvs_documented and dealership_documented and mechanic_documented:
        print("  ✓ PASS: All models have relationship documentation")
    else:
        print("  ✗ FAIL: Some models lack relationship documentation")
        return False
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print("✓ All relationship checks passed!")
    print()
    print("Confirmed:")
    print("  • OneToOneField relationship between BusinessVerificationSubmission and Dealership")
    print("  • OneToOneField relationship between BusinessVerificationSubmission and Mechanic")
    print("  • on_delete=CASCADE configured for both relationships")
    print("  • related_name='verification_submission' set correctly")
    print("  • Reverse relationships accessible via .verification_submission")
    print("  • Model relationships documented in docstrings")
    print()
    print("CASCADE Deletion Behavior:")
    print("  • When a Dealership is deleted, its BusinessVerificationSubmission is deleted")
    print("  • When a Mechanic is deleted, its BusinessVerificationSubmission is deleted")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = verify_relationships()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
