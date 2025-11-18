"""
Test suite for verifying model relationships between BusinessVerificationSubmission,
Dealership, and Mechanic models.

This test file verifies:
- OneToOneField relationships are correctly configured
- CASCADE deletion behavior works as expected
- related_name='verification_submission' is accessible
"""

from django.test import TestCase
from django.db import IntegrityError
from accounts.models import Account, Dealership, Mechanic, BusinessVerificationSubmission


class BusinessVerificationRelationshipTestCase(TestCase):
    """Test BusinessVerificationSubmission relationships with Dealership and Mechanic"""
    
    def setUp(self):
        """Create test accounts and profiles"""
        # Create dealer account and profile
        self.dealer_account = Account.objects.create_user(
            email='dealer@test.com',
            password='testpass123',
            user_type='dealer',
            first_name='Test',
            last_name='Dealer'
        )
        self.dealership = Dealership.objects.create(
            user=self.dealer_account,
            business_name='Test Dealership',
            phone_number='+2348012345678'
        )
        
        # Create mechanic account and profile
        self.mechanic_account = Account.objects.create_user(
            email='mechanic@test.com',
            password='testpass123',
            user_type='mechanic',
            first_name='Test',
            last_name='Mechanic'
        )
        self.mechanic = Mechanic.objects.create(
            user=self.mechanic_account,
            business_name='Test Mechanic Shop',
            phone_number='+2348087654321'
        )
    
    def test_dealership_verification_submission_relationship(self):
        """Test OneToOneField relationship between Dealership and BusinessVerificationSubmission"""
        # Create verification submission for dealership
        submission = BusinessVerificationSubmission.objects.create(
            business_type='dealership',
            dealership=self.dealership,
            business_name='Test Dealership',
            business_address='123 Test Street, Lagos',
            business_email='contact@testdealership.com',
            business_phone='+2348012345678',
            status='pending'
        )
        
        # Verify relationship from dealership to submission
        self.assertEqual(self.dealership.verification_submission, submission)
        
        # Verify relationship from submission to dealership
        self.assertEqual(submission.dealership, self.dealership)
        
        # Verify related_name is correct
        self.assertTrue(hasattr(self.dealership, 'verification_submission'))
    
    def test_mechanic_verification_submission_relationship(self):
        """Test OneToOneField relationship between Mechanic and BusinessVerificationSubmission"""
        # Create verification submission for mechanic
        submission = BusinessVerificationSubmission.objects.create(
            business_type='mechanic',
            mechanic=self.mechanic,
            business_name='Test Mechanic Shop',
            business_address='456 Repair Avenue, Abuja',
            business_email='contact@testmechanic.com',
            business_phone='+2348087654321',
            status='pending'
        )
        
        # Verify relationship from mechanic to submission
        self.assertEqual(self.mechanic.verification_submission, submission)
        
        # Verify relationship from submission to mechanic
        self.assertEqual(submission.mechanic, self.mechanic)
        
        # Verify related_name is correct
        self.assertTrue(hasattr(self.mechanic, 'verification_submission'))
    
    def test_cascade_deletion_dealership(self):
        """Test CASCADE deletion when Dealership is deleted"""
        # Create verification submission
        submission = BusinessVerificationSubmission.objects.create(
            business_type='dealership',
            dealership=self.dealership,
            business_name='Test Dealership',
            business_address='123 Test Street, Lagos',
            business_email='contact@testdealership.com',
            business_phone='+2348012345678',
            status='pending'
        )
        submission_id = submission.id
        
        # Verify submission exists
        self.assertTrue(
            BusinessVerificationSubmission.objects.filter(id=submission_id).exists()
        )
        
        # Delete dealership
        self.dealership.delete()
        
        # Verify submission was cascade deleted
        self.assertFalse(
            BusinessVerificationSubmission.objects.filter(id=submission_id).exists()
        )
    
    def test_cascade_deletion_mechanic(self):
        """Test CASCADE deletion when Mechanic is deleted"""
        # Create verification submission
        submission = BusinessVerificationSubmission.objects.create(
            business_type='mechanic',
            mechanic=self.mechanic,
            business_name='Test Mechanic Shop',
            business_address='456 Repair Avenue, Abuja',
            business_email='contact@testmechanic.com',
            business_phone='+2348087654321',
            status='pending'
        )
        submission_id = submission.id
        
        # Verify submission exists
        self.assertTrue(
            BusinessVerificationSubmission.objects.filter(id=submission_id).exists()
        )
        
        # Delete mechanic
        self.mechanic.delete()
        
        # Verify submission was cascade deleted
        self.assertFalse(
            BusinessVerificationSubmission.objects.filter(id=submission_id).exists()
        )
    
    def test_one_to_one_constraint_dealership(self):
        """Test that only one BusinessVerificationSubmission can exist per Dealership"""
        # Create first submission
        BusinessVerificationSubmission.objects.create(
            business_type='dealership',
            dealership=self.dealership,
            business_name='Test Dealership',
            business_address='123 Test Street, Lagos',
            business_email='contact@testdealership.com',
            business_phone='+2348012345678',
            status='pending'
        )
        
        # Attempt to create second submission for same dealership
        with self.assertRaises(IntegrityError):
            BusinessVerificationSubmission.objects.create(
                business_type='dealership',
                dealership=self.dealership,
                business_name='Test Dealership 2',
                business_address='789 Another Street, Lagos',
                business_email='contact2@testdealership.com',
                business_phone='+2348012345679',
                status='pending'
            )
    
    def test_one_to_one_constraint_mechanic(self):
        """Test that only one BusinessVerificationSubmission can exist per Mechanic"""
        # Create first submission
        BusinessVerificationSubmission.objects.create(
            business_type='mechanic',
            mechanic=self.mechanic,
            business_name='Test Mechanic Shop',
            business_address='456 Repair Avenue, Abuja',
            business_email='contact@testmechanic.com',
            business_phone='+2348087654321',
            status='pending'
        )
        
        # Attempt to create second submission for same mechanic
        with self.assertRaises(IntegrityError):
            BusinessVerificationSubmission.objects.create(
                business_type='mechanic',
                mechanic=self.mechanic,
                business_name='Test Mechanic Shop 2',
                business_address='789 Service Road, Abuja',
                business_email='contact2@testmechanic.com',
                business_phone='+2348087654322',
                status='pending'
            )
    
    def test_business_verification_status_property_dealership(self):
        """Test business_verification_status property on Dealership"""
        # Test when no submission exists
        self.assertEqual(self.dealership.business_verification_status, 'not_submitted')
        
        # Create submission
        BusinessVerificationSubmission.objects.create(
            business_type='dealership',
            dealership=self.dealership,
            business_name='Test Dealership',
            business_address='123 Test Street, Lagos',
            business_email='contact@testdealership.com',
            business_phone='+2348012345678',
            status='pending'
        )
        
        # Refresh from database
        self.dealership.refresh_from_db()
        
        # Test property returns correct status
        self.assertEqual(self.dealership.business_verification_status, 'pending')
    
    def test_business_verification_status_property_mechanic(self):
        """Test business_verification_status property on Mechanic"""
        # Test when no submission exists
        self.assertEqual(self.mechanic.business_verification_status, 'not_submitted')
        
        # Create submission
        BusinessVerificationSubmission.objects.create(
            business_type='mechanic',
            mechanic=self.mechanic,
            business_name='Test Mechanic Shop',
            business_address='456 Repair Avenue, Abuja',
            business_email='contact@testmechanic.com',
            business_phone='+2348087654321',
            status='verified'
        )
        
        # Refresh from database
        self.mechanic.refresh_from_db()
        
        # Test property returns correct status
        self.assertEqual(self.mechanic.business_verification_status, 'verified')
    
    def test_on_delete_cascade_configuration(self):
        """Verify on_delete=CASCADE is configured correctly in model definition"""
        # Get the field from the model
        dealership_field = BusinessVerificationSubmission._meta.get_field('dealership')
        mechanic_field = BusinessVerificationSubmission._meta.get_field('mechanic')
        
        # Verify CASCADE is configured
        from django.db.models import CASCADE
        self.assertEqual(dealership_field.remote_field.on_delete, CASCADE)
        self.assertEqual(mechanic_field.remote_field.on_delete, CASCADE)
    
    def test_related_name_configuration(self):
        """Verify related_name='verification_submission' is configured correctly"""
        # Get the field from the model
        dealership_field = BusinessVerificationSubmission._meta.get_field('dealership')
        mechanic_field = BusinessVerificationSubmission._meta.get_field('mechanic')
        
        # Verify related_name
        self.assertEqual(dealership_field.remote_field.related_name, 'verification_submission')
        self.assertEqual(mechanic_field.remote_field.related_name, 'verification_submission')
