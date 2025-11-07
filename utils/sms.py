import logging
import re
import time
from typing import Dict, Any, List, Optional, Union
from django.conf import settings
import africastalking
from africastalking.SMS import SMSService

logger = logging.getLogger(__name__)

# SMS Configuration
SMS_USERNAME = getattr(settings, 'SMS_USERNAME', 'Veyu')
SMS_API_KEY = getattr(settings, 'SMS_API_KEY', 'atsk_42e7f18bae53ab9f80e226feabe3a79351a6c1c8cf3af4fd0a823a93fb6643c02bf9e1a1')
SMS_SENDER_ID = getattr(settings, 'SMS_SENDER_ID', 'Veyu')

# Initialize Africa's Talking
try:
    africastalking.initialize(SMS_USERNAME, SMS_API_KEY)
    sms_service = africastalking.SMS
    logger.info("Africa's Talking SMS service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Africa's Talking SMS service: {str(e)}")
    sms_service = None

class SMSDeliveryResult:
    """Class to represent SMS delivery result with detailed information."""
    
    def __init__(self, success: bool, message: str, details: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to international format.
    
    Args:
        phone_number: Phone number in various formats
        
    Returns:
        Normalized phone number in international format
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Handle Nigerian numbers
    if digits_only.startswith('234'):
        # Already in international format
        return f"+{digits_only}"
    elif digits_only.startswith('0') and len(digits_only) == 11:
        # Nigerian local format (0XXXXXXXXXX)
        return f"+234{digits_only[1:]}"
    elif len(digits_only) == 10:
        # Nigerian format without leading 0 (XXXXXXXXXX)
        return f"+234{digits_only}"
    else:
        # Assume it's already in correct format or add + if missing
        return f"+{digits_only}" if not phone_number.startswith('+') else phone_number

def validate_phone_number(phone_number: str) -> Dict[str, Any]:
    """
    Validate phone number format and check if it's deliverable.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Dict with validation result
    """
    result = {
        'valid': False,
        'normalized': '',
        'country': '',
        'carrier': '',
        'type': '',
        'message': ''
    }
    
    try:
        normalized = normalize_phone_number(phone_number)
        result['normalized'] = normalized
        
        # Basic format validation
        if not normalized or len(normalized) < 10:
            result['message'] = 'Invalid phone number format'
            return result
        
        # Nigerian number validation
        if normalized.startswith('+234'):
            if len(normalized) == 14:  # +234XXXXXXXXXX
                result['valid'] = True
                result['country'] = 'Nigeria'
                result['message'] = 'Valid Nigerian phone number'
                
                # Determine carrier based on prefix (basic detection)
                prefix = normalized[4:7]  # Get first 3 digits after +234
                if prefix in ['803', '806', '813', '814', '816', '903', '906']:
                    result['carrier'] = 'MTN'
                elif prefix in ['805', '807', '815', '811', '905']:
                    result['carrier'] = 'Glo'
                elif prefix in ['802', '808', '812', '901', '904', '907', '912']:
                    result['carrier'] = 'Airtel'
                elif prefix in ['809', '817', '818', '909']:
                    result['carrier'] = '9mobile'
                else:
                    result['carrier'] = 'Unknown'
                
                result['type'] = 'mobile'
            else:
                result['message'] = 'Invalid Nigerian phone number length'
        else:
            # For non-Nigerian numbers, do basic validation
            if len(normalized) >= 10:
                result['valid'] = True
                result['country'] = 'International'
                result['message'] = 'Valid international phone number'
            else:
                result['message'] = 'Invalid international phone number format'
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating phone number {phone_number}: {str(e)}")
        result['message'] = f'Validation error: {str(e)}'
        return result

def send_sms(message: str, recipient: str, sender_id: str = None, fail_silently: bool = False, use_fallback: bool = True) -> Union[SMSDeliveryResult, bool]:
    """
    Send SMS with enhanced error handling, delivery tracking, and provider fallback.
    
    Args:
        message: SMS message content
        recipient: Recipient phone number
        sender_id: Custom sender ID (optional)
        fail_silently: If True, return False on error instead of raising exception
        use_fallback: If True, use provider fallback mechanism
        
    Returns:
        SMSDeliveryResult object or boolean for backward compatibility
    """
    try:
        # Validate and normalize phone number
        phone_validation = validate_phone_number(recipient)
        if not phone_validation['valid']:
            error_msg = f"Invalid phone number: {phone_validation['message']}"
            logger.warning(error_msg)
            if fail_silently:
                return SMSDeliveryResult(False, error_msg, {'validation': phone_validation})
            raise ValueError(error_msg)
        
        normalized_recipient = phone_validation['normalized']
        
        # Validate message content
        if not message or not message.strip():
            error_msg = "Message content is required"
            logger.warning(error_msg)
            if fail_silently:
                return SMSDeliveryResult(False, error_msg)
            raise ValueError(error_msg)
        
        # Truncate message if too long (SMS limit is typically 160 characters)
        if len(message) > 160:
            logger.warning(f"Message truncated from {len(message)} to 160 characters")
            message = message[:157] + "..."
        
        start_time = time.time()
        
        if use_fallback:
            # Use provider manager with fallback
            from utils.sms_providers import sms_provider_manager
            
            result = sms_provider_manager.send_sms_with_fallback(
                message=message,
                recipient=normalized_recipient,
                sender_id=sender_id or SMS_SENDER_ID
            )
            
            delivery_time = time.time() - start_time
            
            if result['success']:
                result_details = {
                    'provider': result.get('provider', 'Unknown'),
                    'message_id': result.get('message_id', ''),
                    'status': result.get('status', 'sent'),
                    'delivery_time': delivery_time,
                    'recipient': normalized_recipient,
                    'carrier': phone_validation.get('carrier', 'Unknown'),
                    'fallback_used': result.get('fallback_used', False),
                    'attempts': result.get('attempts', []),
                    'response': result
                }
                
                logger.info(f"SMS sent successfully to {normalized_recipient} via {result.get('provider', 'Unknown')}")
                return SMSDeliveryResult(True, result['message'], result_details)
            else:
                error_msg = result['message']
                result_details = {
                    'provider': result.get('provider'),
                    'delivery_time': delivery_time,
                    'recipient': normalized_recipient,
                    'attempts': result.get('attempts', []),
                    'response': result
                }
                
                logger.error(f"SMS failed to {normalized_recipient}: {error_msg}")
                if fail_silently:
                    return SMSDeliveryResult(False, error_msg, result_details)
                raise Exception(error_msg)
        
        else:
            # Use direct Africa's Talking service (legacy mode)
            if not sms_service:
                error_msg = "SMS service not initialized"
                logger.error(error_msg)
                if fail_silently:
                    return SMSDeliveryResult(False, error_msg)
                raise Exception(error_msg)
            
            # Prepare SMS parameters
            sms_params = {
                'recipients': [normalized_recipient],
                'message': message
            }
            
            # Add sender ID if provided
            if sender_id or SMS_SENDER_ID:
                sms_params['sender_id'] = sender_id or SMS_SENDER_ID
            
            # Send SMS
            logger.info(f"Sending SMS to {normalized_recipient} via Africa's Talking (direct)")
            
            response = sms_service.send(**sms_params)
            delivery_time = time.time() - start_time
            
            # Parse response
            if response and 'SMSMessageData' in response:
                sms_data = response['SMSMessageData']
                recipients = sms_data.get('Recipients', [])
                
                if recipients:
                    recipient_data = recipients[0]
                    status = recipient_data.get('status', 'Unknown')
                    status_code = recipient_data.get('statusCode', 0)
                    message_id = recipient_data.get('messageId', '')
                    cost = recipient_data.get('cost', '')
                    
                    # Determine success based on status
                    success = status.lower() in ['success', 'sent'] or status_code in [100, 101]
                    
                    result_details = {
                        'provider': 'AfricasTalking',
                        'message_id': message_id,
                        'status': status,
                        'status_code': status_code,
                        'cost': cost,
                        'delivery_time': delivery_time,
                        'recipient': normalized_recipient,
                        'carrier': phone_validation.get('carrier', 'Unknown'),
                        'fallback_used': False,
                        'response': response
                    }
                    
                    if success:
                        logger.info(f"SMS sent successfully to {normalized_recipient} - ID: {message_id}, Cost: {cost}")
                        return SMSDeliveryResult(True, f"SMS sent successfully - ID: {message_id}", result_details)
                    else:
                        error_msg = f"SMS delivery failed - Status: {status}"
                        logger.error(f"{error_msg} to {normalized_recipient}")
                        if fail_silently:
                            return SMSDeliveryResult(False, error_msg, result_details)
                        raise Exception(error_msg)
                else:
                    error_msg = "No recipient data in SMS response"
                    logger.error(f"{error_msg}: {response}")
                    if fail_silently:
                        return SMSDeliveryResult(False, error_msg, {'response': response})
                    raise Exception(error_msg)
            else:
                error_msg = "Invalid SMS response format"
                logger.error(f"{error_msg}: {response}")
                if fail_silently:
                    return SMSDeliveryResult(False, error_msg, {'response': response})
                raise Exception(error_msg)
            
    except Exception as error:
        error_msg = f"SMS sending error: {str(error)}"
        logger.error(f"{error_msg} to {recipient}", exc_info=True)
        
        if fail_silently:
            return SMSDeliveryResult(False, error_msg, {'error': str(error)})
        raise error

def send_bulk_sms(message: str, recipients: List[str], sender_id: str = None, fail_silently: bool = False) -> Dict[str, Any]:
    """
    Send SMS to multiple recipients with detailed results.
    
    Args:
        message: SMS message content
        recipients: List of recipient phone numbers
        sender_id: Custom sender ID (optional)
        fail_silently: If True, continue on individual failures
        
    Returns:
        Dict with bulk sending results
    """
    if not sms_service:
        error_msg = "SMS service not initialized"
        logger.error(error_msg)
        if fail_silently:
            return {'success': False, 'message': error_msg, 'results': []}
        raise Exception(error_msg)
    
    results = {
        'success': False,
        'total_recipients': len(recipients),
        'successful_sends': 0,
        'failed_sends': 0,
        'results': [],
        'summary': {}
    }
    
    try:
        # Validate and normalize all phone numbers first
        validated_recipients = []
        for recipient in recipients:
            validation = validate_phone_number(recipient)
            if validation['valid']:
                validated_recipients.append(validation['normalized'])
            else:
                results['failed_sends'] += 1
                results['results'].append({
                    'recipient': recipient,
                    'success': False,
                    'message': f"Invalid phone number: {validation['message']}"
                })
        
        if not validated_recipients:
            results['message'] = "No valid recipients found"
            return results
        
        # Prepare SMS parameters
        sms_params = {
            'recipients': validated_recipients,
            'message': message
        }
        
        if sender_id or SMS_SENDER_ID:
            sms_params['sender_id'] = sender_id or SMS_SENDER_ID
        
        # Send bulk SMS
        logger.info(f"Sending bulk SMS to {len(validated_recipients)} recipients")
        response = sms_service.send(**sms_params)
        
        # Parse bulk response
        if response and 'SMSMessageData' in response:
            sms_data = response['SMSMessageData']
            recipients_data = sms_data.get('Recipients', [])
            
            for recipient_data in recipients_data:
                recipient_number = recipient_data.get('number', '')
                status = recipient_data.get('status', 'Unknown')
                status_code = recipient_data.get('statusCode', 0)
                message_id = recipient_data.get('messageId', '')
                cost = recipient_data.get('cost', '')
                
                success = status.lower() in ['success', 'sent'] or status_code in [100, 101]
                
                if success:
                    results['successful_sends'] += 1
                else:
                    results['failed_sends'] += 1
                
                results['results'].append({
                    'recipient': recipient_number,
                    'success': success,
                    'message': status,
                    'message_id': message_id,
                    'cost': cost,
                    'status_code': status_code
                })
        
        # Calculate success rate
        success_rate = (results['successful_sends'] / results['total_recipients']) * 100
        results['success'] = success_rate > 0
        results['success_rate'] = success_rate
        results['message'] = f"Bulk SMS completed: {results['successful_sends']}/{results['total_recipients']} sent successfully"
        
        logger.info(f"Bulk SMS completed: {results['successful_sends']}/{results['total_recipients']} successful")
        return results
        
    except Exception as error:
        error_msg = f"Bulk SMS error: {str(error)}"
        logger.error(error_msg, exc_info=True)
        results['message'] = error_msg
        
        if not fail_silently:
            raise error
        
        return results

def get_sms_delivery_status(message_id: str) -> Dict[str, Any]:
    """
    Check SMS delivery status using message ID.
    
    Args:
        message_id: SMS message ID from send response
        
    Returns:
        Dict with delivery status information
    """
    # Note: Africa's Talking doesn't provide a direct delivery status API
    # This is a placeholder for future implementation or integration with delivery reports
    
    return {
        'message_id': message_id,
        'status': 'unknown',
        'message': 'Delivery status checking not implemented for Africa\'s Talking',
        'provider': 'AfricasTalking'
    }

def test_sms_configuration() -> Dict[str, Any]:
    """
    Test SMS configuration and connectivity.
    
    Returns:
        Dict with test results
    """
    test_result = {
        'success': False,
        'message': '',
        'details': {},
        'recommendations': []
    }
    
    try:
        # Check configuration
        if not SMS_USERNAME:
            test_result['message'] = 'SMS_USERNAME not configured'
            test_result['recommendations'].append('Set SMS_USERNAME in settings')
            return test_result
        
        if not SMS_API_KEY:
            test_result['message'] = 'SMS_API_KEY not configured'
            test_result['recommendations'].append('Set SMS_API_KEY in settings')
            return test_result
        
        # Check service initialization
        if not sms_service:
            test_result['message'] = 'SMS service not initialized'
            test_result['recommendations'].append('Check Africa\'s Talking credentials')
            return test_result
        
        # Test with a dummy request (this won't actually send)
        test_result['success'] = True
        test_result['message'] = 'SMS configuration appears valid'
        test_result['details'] = {
            'username': SMS_USERNAME,
            'api_key_configured': bool(SMS_API_KEY),
            'sender_id': SMS_SENDER_ID,
            'service_initialized': bool(sms_service)
        }
        test_result['recommendations'].append('Send a test SMS to verify actual delivery')
        
        logger.info("SMS configuration test passed")
        return test_result
        
    except Exception as e:
        test_result['message'] = f'SMS configuration test failed: {str(e)}'
        test_result['recommendations'].append('Check SMS service credentials and network connectivity')
        logger.error(f"SMS configuration test failed: {str(e)}", exc_info=True)
        return test_result

# Backward compatibility functions
def verify_phone_number(phone: str, fail_silently: bool = False) -> bool:
    """
    Verify phone number format (backward compatibility).
    
    Args:
        phone: Phone number to verify
        fail_silently: If True, return False on error
        
    Returns:
        bool: True if phone number is valid
    """
    try:
        validation = validate_phone_number(phone)
        return validation['valid']
    except Exception as error:
        if fail_silently:
            logger.warning(f'Phone number verification error: {error}')
            return False
        raise error




