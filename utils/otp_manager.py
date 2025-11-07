import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

logger = logging.getLogger(__name__)

class OTPManager:
    """Enhanced OTP management with rate limiting, delivery tracking, and resend functionality."""
    
    # Rate limiting settings
    MAX_OTP_REQUESTS_PER_HOUR = 5
    MAX_OTP_REQUESTS_PER_DAY = 20
    RESEND_COOLDOWN_MINUTES = 2
    
    # OTP settings
    DEFAULT_EXPIRY_MINUTES = 10
    DEFAULT_MAX_ATTEMPTS = 3
    
    def __init__(self):
        self.cache_prefix = 'otp_manager'
    
    def _get_rate_limit_key(self, user_id: int, channel: str, period: str) -> str:
        """Generate cache key for rate limiting."""
        return f"{self.cache_prefix}:rate_limit:{user_id}:{channel}:{period}"
    
    def _get_delivery_key(self, user_id: int, channel: str) -> str:
        """Generate cache key for delivery tracking."""
        return f"{self.cache_prefix}:delivery:{user_id}:{channel}"
    
    def _get_resend_key(self, user_id: int, channel: str) -> str:
        """Generate cache key for resend cooldown."""
        return f"{self.cache_prefix}:resend:{user_id}:{channel}"
    
    def check_rate_limit(self, user_id: int, channel: str) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limits for OTP requests.
        
        Returns:
            Dict with rate limit status and remaining counts
        """
        now = timezone.now()
        hour_key = self._get_rate_limit_key(user_id, channel, now.strftime('%Y%m%d%H'))
        day_key = self._get_rate_limit_key(user_id, channel, now.strftime('%Y%m%d'))
        
        hour_count = cache.get(hour_key, 0)
        day_count = cache.get(day_key, 0)
        
        result = {
            'allowed': True,
            'hour_count': hour_count,
            'day_count': day_count,
            'hour_limit': self.MAX_OTP_REQUESTS_PER_HOUR,
            'day_limit': self.MAX_OTP_REQUESTS_PER_DAY,
            'reset_hour': (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0),
            'reset_day': (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        }
        
        if hour_count >= self.MAX_OTP_REQUESTS_PER_HOUR:
            result['allowed'] = False
            result['reason'] = 'hourly_limit_exceeded'
            result['message'] = f'Too many OTP requests. Try again after {result["reset_hour"].strftime("%H:%M")}'
        elif day_count >= self.MAX_OTP_REQUESTS_PER_DAY:
            result['allowed'] = False
            result['reason'] = 'daily_limit_exceeded'
            result['message'] = 'Daily OTP limit exceeded. Try again tomorrow.'
        
        return result
    
    def check_resend_cooldown(self, user_id: int, channel: str) -> Dict[str, Any]:
        """
        Check if user is in resend cooldown period.
        
        Returns:
            Dict with cooldown status and remaining time
        """
        resend_key = self._get_resend_key(user_id, channel)
        last_sent = cache.get(resend_key)
        
        if not last_sent:
            return {'allowed': True, 'remaining_seconds': 0}
        
        elapsed = time.time() - last_sent
        cooldown_seconds = self.RESEND_COOLDOWN_MINUTES * 60
        
        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            return {
                'allowed': False,
                'remaining_seconds': remaining,
                'message': f'Please wait {remaining} seconds before requesting another OTP'
            }
        
        return {'allowed': True, 'remaining_seconds': 0}
    
    def increment_rate_limit(self, user_id: int, channel: str):
        """Increment rate limit counters."""
        now = timezone.now()
        hour_key = self._get_rate_limit_key(user_id, channel, now.strftime('%Y%m%d%H'))
        day_key = self._get_rate_limit_key(user_id, channel, now.strftime('%Y%m%d'))
        
        # Increment counters with appropriate expiry
        cache.set(hour_key, cache.get(hour_key, 0) + 1, 3600)  # 1 hour
        cache.set(day_key, cache.get(day_key, 0) + 1, 86400)   # 24 hours
    
    def set_resend_cooldown(self, user_id: int, channel: str):
        """Set resend cooldown timer."""
        resend_key = self._get_resend_key(user_id, channel)
        cache.set(resend_key, time.time(), self.RESEND_COOLDOWN_MINUTES * 60)
    
    def track_delivery_attempt(self, user_id: int, channel: str, otp_id: str, status: str, 
                              error_message: str = None) -> Dict[str, Any]:
        """
        Track OTP delivery attempt.
        
        Args:
            user_id: User ID
            channel: Delivery channel (email/sms)
            otp_id: OTP instance ID
            status: Delivery status (sent/failed/delivered/bounced)
            error_message: Error message if delivery failed
        
        Returns:
            Dict with tracking information
        """
        delivery_key = self._get_delivery_key(user_id, channel)
        
        # Get existing delivery history
        delivery_history = cache.get(delivery_key, [])
        
        # Add new delivery attempt
        delivery_attempt = {
            'otp_id': otp_id,
            'status': status,
            'timestamp': time.time(),
            'channel': channel,
            'error_message': error_message
        }
        
        delivery_history.append(delivery_attempt)
        
        # Keep only last 10 attempts
        delivery_history = delivery_history[-10:]
        
        # Store for 24 hours
        cache.set(delivery_key, delivery_history, 86400)
        
        logger.info(f"OTP delivery tracked: user={user_id}, channel={channel}, status={status}")
        
        return delivery_attempt
    
    def get_delivery_history(self, user_id: int, channel: str) -> List[Dict[str, Any]]:
        """Get OTP delivery history for user and channel."""
        delivery_key = self._get_delivery_key(user_id, channel)
        return cache.get(delivery_key, [])
    
    def get_delivery_stats(self, user_id: int, channel: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get delivery statistics for the specified time period.
        
        Returns:
            Dict with delivery statistics
        """
        delivery_history = self.get_delivery_history(user_id, channel)
        cutoff_time = time.time() - (hours * 3600)
        
        # Filter recent attempts
        recent_attempts = [
            attempt for attempt in delivery_history 
            if attempt['timestamp'] > cutoff_time
        ]
        
        stats = {
            'total_attempts': len(recent_attempts),
            'successful': len([a for a in recent_attempts if a['status'] in ['sent', 'delivered']]),
            'failed': len([a for a in recent_attempts if a['status'] in ['failed', 'bounced']]),
            'success_rate': 0,
            'last_attempt': None,
            'last_success': None,
            'last_failure': None
        }
        
        if stats['total_attempts'] > 0:
            stats['success_rate'] = (stats['successful'] / stats['total_attempts']) * 100
            stats['last_attempt'] = max(recent_attempts, key=lambda x: x['timestamp'])
        
        # Find last success and failure
        successful_attempts = [a for a in recent_attempts if a['status'] in ['sent', 'delivered']]
        failed_attempts = [a for a in recent_attempts if a['status'] in ['failed', 'bounced']]
        
        if successful_attempts:
            stats['last_success'] = max(successful_attempts, key=lambda x: x['timestamp'])
        
        if failed_attempts:
            stats['last_failure'] = max(failed_attempts, key=lambda x: x['timestamp'])
        
        return stats
    
    def request_otp(self, user, channel: str, purpose: str = 'verification', 
                   ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Request a new OTP with comprehensive validation, rate limiting, and security logging.
        
        Args:
            user: User instance
            channel: Delivery channel ('email' or 'sms')
            purpose: OTP purpose ('verification', 'login', etc.)
            ip_address: Client IP address for security logging
            user_agent: Client user agent for security logging
        
        Returns:
            Dict with request result and OTP instance if successful
        """
        from accounts.models import OTP
        from utils.otp_security import otp_security_manager
        
        result = {
            'success': False,
            'otp': None,
            'message': '',
            'rate_limit': None,
            'cooldown': None,
            'security_status': None
        }
        
        try:
            # Check for security lockout first
            lockout_status = otp_security_manager.check_lockout_status(user.id, channel)
            if lockout_status['locked_out']:
                result['message'] = f"Account temporarily locked due to too many failed attempts. Try again in {lockout_status['remaining_seconds']} seconds."
                result['security_status'] = lockout_status
                
                # Log the blocked request
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='request',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message='Account locked out'
                )
                
                return result
            
            # Check rate limits
            rate_limit = self.check_rate_limit(user.id, channel)
            result['rate_limit'] = rate_limit
            
            if not rate_limit['allowed']:
                # Log rate limit violation
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='request',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=f'Rate limit exceeded: {rate_limit["message"]}'
                )
                
                result['message'] = rate_limit['message']
                return result
            
            # Check resend cooldown
            cooldown = self.check_resend_cooldown(user.id, channel)
            result['cooldown'] = cooldown
            
            if not cooldown['allowed']:
                # Log cooldown violation
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='request',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=f'Resend cooldown active: {cooldown["message"]}'
                )
                
                result['message'] = cooldown['message']
                return result
            
            # Check for existing active OTP
            existing_otp = OTP.objects.filter(
                valid_for=user,
                channel=channel,
                purpose=purpose,
                used=False
            ).order_by('-date_created').first()
            
            if existing_otp and existing_otp.is_valid_for_verification():
                # Log existing OTP reuse
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='request',
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=existing_otp.code,
                    error_message='Returned existing active OTP'
                )
                
                # Return existing OTP if still valid
                result['success'] = True
                result['otp'] = existing_otp
                result['message'] = f'Active OTP already exists. Expires in {int((existing_otp.expires_at - timezone.now()).total_seconds() / 60)} minutes.'
                return result
            
            # Create new OTP
            with transaction.atomic():
                # Mark any existing OTPs as used
                OTP.objects.filter(
                    valid_for=user,
                    channel=channel,
                    purpose=purpose,
                    used=False
                ).update(used=True)
                
                # Create new OTP
                otp = OTP.objects.create(
                    valid_for=user,
                    channel=channel,
                    purpose=purpose
                )
            
            # Update rate limiting and cooldown
            self.increment_rate_limit(user.id, channel)
            self.set_resend_cooldown(user.id, channel)
            
            # Log successful OTP creation
            otp_security_manager.log_otp_attempt(
                user_id=user.id,
                channel=channel,
                action='request',
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                otp_code=otp.code
            )
            
            result['success'] = True
            result['otp'] = otp
            result['message'] = 'OTP created successfully'
            
            logger.info(f"OTP requested successfully: user={user.email}, channel={channel}, purpose={purpose}")
            
            return result
            
        except Exception as e:
            # Log error
            try:
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='request',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=f'System error: {str(e)}'
                )
            except Exception as log_error:
                logger.error(f"Failed to log OTP security event: {str(log_error)}")
            
            logger.error(f"Error requesting OTP for user {user.email}: {str(e)}", exc_info=True)
            result['message'] = 'An error occurred while creating OTP'
            return result
    
    def send_otp_email(self, user, otp_instance) -> Dict[str, Any]:
        """
        Send OTP via email with delivery tracking.
        
        Returns:
            Dict with sending result and tracking information
        """
        from accounts.utils.email_notifications import send_otp_email
        
        result = {
            'success': False,
            'message': '',
            'delivery_id': None,
            'tracking': None
        }
        
        try:
            # Track delivery attempt
            delivery_id = f"otp_{otp_instance.id}_{int(time.time())}"
            
            # Attempt to send email
            email_sent = send_otp_email(
                user=user,
                otp_code=otp_instance.code,
                validity_minutes=int((otp_instance.expires_at - timezone.now()).total_seconds() / 60)
            )
            
            if email_sent:
                # Track successful delivery attempt
                tracking = self.track_delivery_attempt(
                    user_id=user.id,
                    channel='email',
                    otp_id=str(otp_instance.id),
                    status='sent'
                )
                
                result['success'] = True
                result['message'] = 'OTP sent to your email address'
                result['delivery_id'] = delivery_id
                result['tracking'] = tracking
                
                logger.info(f"OTP email sent successfully to {user.email}")
            else:
                # Track failed delivery attempt
                tracking = self.track_delivery_attempt(
                    user_id=user.id,
                    channel='email',
                    otp_id=str(otp_instance.id),
                    status='failed',
                    error_message='Email sending failed'
                )
                
                result['message'] = 'Failed to send OTP email'
                result['tracking'] = tracking
                
                logger.error(f"Failed to send OTP email to {user.email}")
            
            return result
            
        except Exception as e:
            # Track failed delivery attempt
            tracking = self.track_delivery_attempt(
                user_id=user.id,
                channel='email',
                otp_id=str(otp_instance.id),
                status='failed',
                error_message=str(e)
            )
            
            result['message'] = f'Error sending OTP email: {str(e)}'
            result['tracking'] = tracking
            
            logger.error(f"Error sending OTP email to {user.email}: {str(e)}", exc_info=True)
            return result
    
    def send_otp_sms(self, user, otp_instance, phone_number: str) -> Dict[str, Any]:
        """
        Send OTP via SMS with enhanced delivery tracking and validation.
        
        Returns:
            Dict with sending result and tracking information
        """
        from utils.sms import send_sms, validate_phone_number, SMSDeliveryResult
        
        result = {
            'success': False,
            'message': '',
            'delivery_id': None,
            'tracking': None,
            'phone_validation': None
        }
        
        try:
            # Validate phone number first
            phone_validation = validate_phone_number(phone_number)
            result['phone_validation'] = phone_validation
            
            if not phone_validation['valid']:
                error_msg = f"Invalid phone number: {phone_validation['message']}"
                tracking = self.track_delivery_attempt(
                    user_id=user.id,
                    channel='sms',
                    otp_id=str(otp_instance.id),
                    status='failed',
                    error_message=error_msg
                )
                
                result['message'] = error_msg
                result['tracking'] = tracking
                return result
            
            # Track delivery attempt
            delivery_id = f"otp_{otp_instance.id}_{int(time.time())}"
            
            # Prepare SMS message with better formatting
            validity_minutes = int((otp_instance.expires_at - timezone.now()).total_seconds() / 60)
            sms_message = f"Your Veyu verification code is: {otp_instance.code}. Valid for {validity_minutes} minutes. Do not share this code with anyone."
            
            # Attempt to send SMS using enhanced SMS service
            sms_result = send_sms(
                message=sms_message,
                recipient=phone_validation['normalized'],
                fail_silently=True  # We handle errors ourselves
            )
            
            # Handle different return types (SMSDeliveryResult or boolean for backward compatibility)
            if isinstance(sms_result, SMSDeliveryResult):
                if sms_result.success:
                    # Track successful delivery attempt
                    tracking = self.track_delivery_attempt(
                        user_id=user.id,
                        channel='sms',
                        otp_id=str(otp_instance.id),
                        status='sent'
                    )
                    
                    result['success'] = True
                    result['message'] = sms_result.message
                    result['delivery_id'] = delivery_id
                    result['tracking'] = tracking
                    result['sms_details'] = sms_result.details
                    
                    logger.info(f"OTP SMS sent successfully to {phone_validation['normalized']} - {sms_result.message}")
                else:
                    # Track failed delivery attempt
                    tracking = self.track_delivery_attempt(
                        user_id=user.id,
                        channel='sms',
                        otp_id=str(otp_instance.id),
                        status='failed',
                        error_message=sms_result.message
                    )
                    
                    result['message'] = f'SMS delivery failed: {sms_result.message}'
                    result['tracking'] = tracking
                    result['sms_details'] = sms_result.details
                    
                    logger.error(f"Failed to send OTP SMS to {phone_validation['normalized']}: {sms_result.message}")
            
            elif sms_result:  # Boolean True (backward compatibility)
                # Track successful delivery attempt
                tracking = self.track_delivery_attempt(
                    user_id=user.id,
                    channel='sms',
                    otp_id=str(otp_instance.id),
                    status='sent'
                )
                
                result['success'] = True
                result['message'] = 'OTP sent to your phone number'
                result['delivery_id'] = delivery_id
                result['tracking'] = tracking
                
                logger.info(f"OTP SMS sent successfully to {phone_validation['normalized']}")
            
            else:  # Boolean False or None
                # Track failed delivery attempt
                tracking = self.track_delivery_attempt(
                    user_id=user.id,
                    channel='sms',
                    otp_id=str(otp_instance.id),
                    status='failed',
                    error_message='SMS sending returned false'
                )
                
                result['message'] = 'Failed to send OTP SMS'
                result['tracking'] = tracking
                
                logger.error(f"Failed to send OTP SMS to {phone_validation['normalized']}")
            
            return result
            
        except Exception as e:
            # Track failed delivery attempt
            tracking = self.track_delivery_attempt(
                user_id=user.id,
                channel='sms',
                otp_id=str(otp_instance.id),
                status='failed',
                error_message=str(e)
            )
            
            result['message'] = f'Error sending OTP SMS: {str(e)}'
            result['tracking'] = tracking
            
            logger.error(f"Error sending OTP SMS to {phone_number}: {str(e)}", exc_info=True)
            return result
    
    def verify_otp(self, user, otp_code: str, channel: str, purpose: str = 'verification', 
                  ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Verify OTP with comprehensive validation, security tracking, and brute force protection.
        
        Returns:
            Dict with verification result and security information
        """
        from accounts.models import OTP
        from utils.otp_security import otp_security_manager
        
        result = {
            'success': False,
            'message': '',
            'otp': None,
            'security_status': None
        }
        
        try:
            # Check for security lockout first
            lockout_status = otp_security_manager.check_lockout_status(user.id, channel)
            if lockout_status['locked_out']:
                result['message'] = f"Account temporarily locked due to too many failed attempts. Try again in {lockout_status['remaining_seconds']} seconds."
                result['security_status'] = lockout_status
                
                # Log the blocked attempt
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='verify',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=otp_code,
                    error_message='Account locked out'
                )
                
                return result
            
            # Find the OTP
            otp = OTP.objects.filter(
                valid_for=user,
                channel=channel,
                purpose=purpose,
                code=otp_code
            ).order_by('-date_created').first()
            
            if not otp:
                # Track failed attempt
                security_tracking = otp_security_manager.track_failed_attempt(user.id, channel, ip_address)
                result['security_status'] = security_tracking
                
                # Log the failed attempt
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='verify',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=otp_code,
                    error_message='OTP code not found'
                )
                
                result['message'] = 'Invalid OTP code'
                logger.warning(f"OTP verification failed - code not found: user={user.email}, code={otp_code}")
                return result
            
            # Verify the OTP
            if otp.verify(otp_code, user=user):
                # Reset failed attempt counters on successful verification
                otp_security_manager.reset_failed_attempts(user.id, channel)
                
                # Log successful verification
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='verify',
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=otp_code
                )
                
                result['success'] = True
                result['message'] = 'OTP verified successfully'
                result['otp'] = otp
                result['security_status'] = {'failed_attempts_reset': True}
                
                logger.info(f"OTP verified successfully: user={user.email}, channel={channel}")
            else:
                # Track failed attempt
                security_tracking = otp_security_manager.track_failed_attempt(user.id, channel, ip_address)
                result['security_status'] = security_tracking
                
                # Determine specific error message
                if otp.used:
                    error_message = 'OTP has already been used'
                elif otp.is_expired():
                    error_message = 'OTP has expired. Please request a new one.'
                elif otp.attempts >= otp.max_attempts:
                    error_message = 'Maximum verification attempts exceeded. Please request a new OTP.'
                else:
                    error_message = 'Invalid OTP code'
                
                # Log the failed attempt
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='verify',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=otp_code,
                    error_message=error_message
                )
                
                result['message'] = error_message
                logger.warning(f"OTP verification failed: user={user.email}, reason={error_message}")
            
            return result
            
        except Exception as e:
            # Track failed attempt due to error
            try:
                security_tracking = otp_security_manager.track_failed_attempt(user.id, channel, ip_address)
                result['security_status'] = security_tracking
                
                otp_security_manager.log_otp_attempt(
                    user_id=user.id,
                    channel=channel,
                    action='verify',
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    otp_code=otp_code,
                    error_message=f'System error: {str(e)}'
                )
            except Exception as log_error:
                logger.error(f"Failed to log OTP security event: {str(log_error)}")
            
            result['message'] = f'Error verifying OTP: {str(e)}'
            logger.error(f"Error verifying OTP for user {user.email}: {str(e)}", exc_info=True)
            return result

# Global instance
otp_manager = OTPManager()