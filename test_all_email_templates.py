#!/usr/bin/env python
"""
Test all email templates to ensure they're properly configured.
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.utils.email_notifications import (
    send_verification_email,
    send_welcome_email,
    send_password_reset_email,
    send_otp_email,
    send_business_verification_status,
    send_booking_confirmation,
    send_inspection_scheduled,
    send_order_confirmation,
    send_listing_published,
    send_purchase_confirmation,
    send_wallet_transaction,
    send_security_alert,
    send_rental_confirmation,
    send_promotion_email,
    send_reminder_email,
)

User = get_user_model()

def create_test_user():
    """Create or get a test user."""
    try:
        user = User.objects.get(email='ekeminieffiong22@gmail.com')
    except User.DoesNotExist:
        user = User(
            email='ekeminieffiong22@gmail.com',
            first_name='Test',
            last_name='User'
        )
    return user

def main():
    print("📧 COMPREHENSIVE EMAIL TEMPLATE TEST")
    print("=" * 60)
    
    user = create_test_user()
    results = {}
    
    # Test 1: Verification Email
    print("\n1. Testing verification email...")
    results['verification'] = send_verification_email(user, '123456')
    print("✅ Sent" if results['verification'] else "❌ Failed")
    
    # Test 2: Welcome Email
    print("\n2. Testing welcome email...")
    results['welcome'] = send_welcome_email(user)
    print("✅ Sent" if results['welcome'] else "❌ Failed")
    
    # Test 3: Password Reset Email
    print("\n3. Testing password reset email...")
    results['password_reset'] = send_password_reset_email(
        user, 
        'https://veyu.cc/reset-password/abc123'
    )
    print("✅ Sent" if results['password_reset'] else "❌ Failed")
    
    # Test 4: OTP Email
    print("\n4. Testing OTP email...")
    results['otp'] = send_otp_email(user, '654321', 30)
    print("✅ Sent" if results['otp'] else "❌ Failed")
    
    # Test 5: Business Verification Status
    print("\n5. Testing business verification email...")
    results['business_verification'] = send_business_verification_status(
        user, 
        'approved', 
        business_name='Test Motors'
    )
    print("✅ Sent" if results['business_verification'] else "❌ Failed")
    
    # Test 6: Booking Confirmation
    print("\n6. Testing booking confirmation email...")
    results['booking'] = send_booking_confirmation(user, {
        'booking_reference': 'BK123456',
        'service': 'Oil Change',
        'date': '2025-11-15',
        'time': '10:00 AM'
    })
    print("✅ Sent" if results['booking'] else "❌ Failed")
    
    # Test 7: Inspection Scheduled
    print("\n7. Testing inspection scheduled email...")
    results['inspection'] = send_inspection_scheduled(user, {
        'inspection_reference': 'INS123456',
        'vehicle': 'Toyota Camry 2020',
        'date': '2025-11-16',
        'time': '2:00 PM'
    })
    print("✅ Sent" if results['inspection'] else "❌ Failed")
    
    # Test 8: Order Confirmation
    print("\n8. Testing order confirmation email...")
    results['order'] = send_order_confirmation(user, {
        'order_number': 'ORD123456',
        'total_amount': '₦50,000',
        'items': 'Vehicle Parts'
    })
    print("✅ Sent" if results['order'] else "❌ Failed")
    
    # Test 9: Listing Published
    print("\n9. Testing listing published email...")
    results['listing'] = send_listing_published(user, {
        'title': 'Toyota Camry 2020',
        'listing_url': 'https://veyu.cc/listings/123'
    })
    print("✅ Sent" if results['listing'] else "❌ Failed")
    
    # Test 10: Purchase Confirmation
    print("\n10. Testing purchase confirmation email...")
    results['purchase'] = send_purchase_confirmation(user, {
        'order_number': 'PUR123456',
        'vehicle': 'Honda Accord 2019',
        'amount': '₦2,500,000'
    })
    print("✅ Sent" if results['purchase'] else "❌ Failed")
    
    # Test 11: Wallet Transaction
    print("\n11. Testing wallet transaction email...")
    results['wallet'] = send_wallet_transaction(user, {
        'transaction_type': 'Credit',
        'amount': '₦10,000',
        'balance': '₦50,000'
    })
    print("✅ Sent" if results['wallet'] else "❌ Failed")
    
    # Test 12: Security Alert
    print("\n12. Testing security alert email...")
    results['security'] = send_security_alert(user, {
        'alert_type': 'New Login',
        'location': 'Lagos, Nigeria',
        'device': 'Chrome on Windows'
    })
    print("✅ Sent" if results['security'] else "❌ Failed")
    
    # Test 13: Rental Confirmation
    print("\n13. Testing rental confirmation email...")
    results['rental'] = send_rental_confirmation(user, {
        'rental_reference': 'RNT123456',
        'vehicle': 'Mercedes Benz C300',
        'start_date': '2025-11-20',
        'end_date': '2025-11-25'
    })
    print("✅ Sent" if results['rental'] else "❌ Failed")
    
    # Test 14: Promotion Email
    print("\n14. Testing promotion email...")
    results['promotion'] = send_promotion_email(user, {
        'subject': 'Special Black Friday Deals!',
        'offer': '20% off all listings',
        'promo_code': 'BF2025'
    })
    print("✅ Sent" if results['promotion'] else "❌ Failed")
    
    # Test 15: Reminder Email
    print("\n15. Testing reminder email...")
    results['reminder'] = send_reminder_email(user, {
        'subject': 'Upcoming Service Reminder',
        'message': 'Your vehicle service is due in 3 days'
    })
    print("✅ Sent" if results['reminder'] else "❌ Failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print("\n📬 Check your inbox at ekeminieffiong22@gmail.com")
    print("You should have received all the test emails!")
    
    if failed > 0:
        print("\n⚠️  Some emails failed. Check the logs above for details.")
    else:
        print("\n🎉 All email templates are working perfectly!")

if __name__ == "__main__":
    main()