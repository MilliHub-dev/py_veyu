from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Dealership
from listings.service_mapping import DealershipServiceProcessor
from django.core.exceptions import ValidationError

User = get_user_model()


class DealershipServiceMappingTest(TestCase):
    """Test the DealershipServiceProcessor integration with the API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='dealer@test.com',
            password='testpass123',
            user_type='dealer'
        )
        self.dealership = Dealership.objects.create(
            user=self.user,
            business_name='Test Dealership',
            contact_email='dealer@test.com',
            contact_phone='+1234567890'
        )
        self.processor = DealershipServiceProcessor()
    
    def test_service_processor_basic_mapping(self):
        """Test that the service processor correctly maps basic services."""
        services = ['Car Sale', 'Car Leasing', 'Drivers']
        result = self.processor.process_services(services)
        
        self.assertTrue(result['offers_purchase'])
        self.assertTrue(result['offers_rental'])
        self.assertTrue(result['offers_drivers'])
        self.assertFalse(result['offers_trade_in'])
    
    def test_service_processor_case_insensitive(self):
        """Test that the service processor handles case-insensitive matching."""
        services = ['car sale', 'CAR LEASING', 'drivers']
        result = self.processor.process_services(services)
        
        self.assertTrue(result['offers_purchase'])
        self.assertTrue(result['offers_rental'])
        self.assertTrue(result['offers_drivers'])
    
    def test_service_processor_validation_error(self):
        """Test that the service processor raises ValidationError for empty services."""
        with self.assertRaises(ValidationError):
            self.processor.process_services([])
    
    def test_service_processor_unmapped_services(self):
        """Test that the service processor handles unmapped services gracefully."""
        services = ['Car Sale', 'Unknown Service']
        # Should not raise an error, but should log unmapped services
        result = self.processor.process_services(services)
        
        self.assertTrue(result['offers_purchase'])
        self.assertFalse(result['offers_rental'])
        self.assertFalse(result['offers_drivers'])
        self.assertFalse(result['offers_trade_in'])
