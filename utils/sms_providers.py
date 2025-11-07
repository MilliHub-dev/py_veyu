import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from django.conf import settings

logger = logging.getLogger(__name__)

class SMSProvider(ABC):
    """Abstract base class for SMS providers."""
    
    @abstractmethod
    def send_sms(self, message: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """Send SMS and return result."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass

class AfricasTalkingProvider(SMSProvider):
    """Africa's Talking SMS provider."""
    
    def __init__(self):
        self.username = getattr(settings, 'SMS_USERNAME', 'Veyu')
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'Veyu')
        self._service = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Africa's Talking service."""
        try:
            import africastalking
            africastalking.initialize(self.username, self.api_key)
            self._service = africastalking.SMS
            logger.info("Africa's Talking SMS provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking: {str(e)}")
            self._service = None
    
    def send_sms(self, message: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """Send SMS via Africa's Talking."""
        if not self._service:
            return {
                'success': False,
                'message': 'Africa\'s Talking service not available',
                'provider': self.get_provider_name()
            }
        
        try:
            response = self._service.send(
                recipients=[recipient],
                message=message,
                sender_id=kwargs.get('sender_id', self.sender_id)
            )
            
            if response and 'SMSMessageData' in response:
                recipients_data = response['SMSMessageData'].get('Recipients', [])
                if recipients_data:
                    recipient_data = recipients_data[0]
                    status = recipient_data.get('status', 'Unknown')
                    success = status.lower() in ['success', 'sent']
                    
                    return {
                        'success': success,
                        'message': status,
                        'provider': self.get_provider_name(),
                        'message_id': recipient_data.get('messageId', ''),
                        'cost': recipient_data.get('cost', ''),
                        'raw_response': response
                    }
            
            return {
                'success': False,
                'message': 'Invalid response format',
                'provider': self.get_provider_name(),
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Africa's Talking SMS error: {str(e)}")
            return {
                'success': False,
                'message': f'Provider error: {str(e)}',
                'provider': self.get_provider_name()
            }
    
    def get_provider_name(self) -> str:
        return "AfricasTalking"
    
    def is_available(self) -> bool:
        return bool(self._service and self.api_key)

class TwilioProvider(SMSProvider):
    """Twilio SMS provider (fallback option)."""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
        self._client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Twilio client."""
        try:
            if self.account_sid and self.auth_token:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS provider initialized")
        except ImportError:
            logger.warning("Twilio library not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {str(e)}")
    
    def send_sms(self, message: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """Send SMS via Twilio."""
        if not self._client:
            return {
                'success': False,
                'message': 'Twilio client not available',
                'provider': self.get_provider_name()
            }
        
        try:
            message_obj = self._client.messages.create(
                body=message,
                from_=kwargs.get('from_number', self.from_number),
                to=recipient
            )
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'provider': self.get_provider_name(),
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'raw_response': {
                    'sid': message_obj.sid,
                    'status': message_obj.status,
                    'error_code': message_obj.error_code,
                    'error_message': message_obj.error_message
                }
            }
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {
                'success': False,
                'message': f'Provider error: {str(e)}',
                'provider': self.get_provider_name()
            }
    
    def get_provider_name(self) -> str:
        return "Twilio"
    
    def is_available(self) -> bool:
        return bool(self._client and self.account_sid and self.auth_token and self.from_number)

class VonageProvider(SMSProvider):
    """Vonage (formerly Nexmo) SMS provider (fallback option)."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'VONAGE_API_KEY', '')
        self.api_secret = getattr(settings, 'VONAGE_API_SECRET', '')
        self.from_number = getattr(settings, 'VONAGE_FROM_NUMBER', 'Veyu')
        self._client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Vonage client."""
        try:
            if self.api_key and self.api_secret:
                import vonage
                self._client = vonage.Client(key=self.api_key, secret=self.api_secret)
                logger.info("Vonage SMS provider initialized")
        except ImportError:
            logger.warning("Vonage library not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Vonage: {str(e)}")
    
    def send_sms(self, message: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """Send SMS via Vonage."""
        if not self._client:
            return {
                'success': False,
                'message': 'Vonage client not available',
                'provider': self.get_provider_name()
            }
        
        try:
            sms = vonage.Sms(self._client)
            response = sms.send_message({
                'from': kwargs.get('from_number', self.from_number),
                'to': recipient,
                'text': message
            })
            
            if response['messages']:
                message_data = response['messages'][0]
                success = message_data['status'] == '0'
                
                return {
                    'success': success,
                    'message': 'SMS sent successfully' if success else message_data.get('error-text', 'Unknown error'),
                    'provider': self.get_provider_name(),
                    'message_id': message_data.get('message-id', ''),
                    'status': message_data.get('status', ''),
                    'raw_response': response
                }
            
            return {
                'success': False,
                'message': 'No message data in response',
                'provider': self.get_provider_name(),
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Vonage SMS error: {str(e)}")
            return {
                'success': False,
                'message': f'Provider error: {str(e)}',
                'provider': self.get_provider_name()
            }
    
    def get_provider_name(self) -> str:
        return "Vonage"
    
    def is_available(self) -> bool:
        return bool(self._client and self.api_key and self.api_secret)

class SMSProviderManager:
    """Manages multiple SMS providers with fallback support."""
    
    def __init__(self):
        self.providers = [
            AfricasTalkingProvider(),  # Primary provider
            TwilioProvider(),          # Fallback 1
            VonageProvider(),          # Fallback 2
        ]
        self._log_provider_status()
    
    def _log_provider_status(self):
        """Log the status of all providers."""
        for provider in self.providers:
            status = "Available" if provider.is_available() else "Not Available"
            logger.info(f"SMS Provider {provider.get_provider_name()}: {status}")
    
    def get_available_providers(self) -> List[SMSProvider]:
        """Get list of available providers."""
        return [provider for provider in self.providers if provider.is_available()]
    
    def send_sms_with_fallback(self, message: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """
        Send SMS with automatic fallback to other providers if primary fails.
        
        Args:
            message: SMS message content
            recipient: Recipient phone number
            **kwargs: Additional parameters for SMS sending
            
        Returns:
            Dict with sending result and provider information
        """
        available_providers = self.get_available_providers()
        
        if not available_providers:
            return {
                'success': False,
                'message': 'No SMS providers available',
                'provider': None,
                'attempts': []
            }
        
        attempts = []
        
        for i, provider in enumerate(available_providers):
            try:
                logger.info(f"Attempting SMS via {provider.get_provider_name()} (attempt {i+1}/{len(available_providers)})")
                
                result = provider.send_sms(message, recipient, **kwargs)
                attempts.append({
                    'provider': provider.get_provider_name(),
                    'success': result['success'],
                    'message': result['message'],
                    'attempt_number': i + 1
                })
                
                if result['success']:
                    logger.info(f"SMS sent successfully via {provider.get_provider_name()}")
                    result['attempts'] = attempts
                    result['fallback_used'] = i > 0
                    return result
                else:
                    logger.warning(f"SMS failed via {provider.get_provider_name()}: {result['message']}")
                    
            except Exception as e:
                error_msg = f"Provider {provider.get_provider_name()} error: {str(e)}"
                logger.error(error_msg)
                attempts.append({
                    'provider': provider.get_provider_name(),
                    'success': False,
                    'message': error_msg,
                    'attempt_number': i + 1
                })
        
        # All providers failed
        return {
            'success': False,
            'message': f'All {len(available_providers)} SMS providers failed',
            'provider': None,
            'attempts': attempts,
            'fallback_used': True
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all SMS providers."""
        status = {
            'total_providers': len(self.providers),
            'available_providers': 0,
            'providers': []
        }
        
        for provider in self.providers:
            provider_info = {
                'name': provider.get_provider_name(),
                'available': provider.is_available(),
                'primary': provider == self.providers[0]
            }
            
            if provider_info['available']:
                status['available_providers'] += 1
            
            status['providers'].append(provider_info)
        
        return status

# Global SMS provider manager instance
sms_provider_manager = SMSProviderManager()