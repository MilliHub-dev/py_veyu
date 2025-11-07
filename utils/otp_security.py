import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

class OTPSecurityManager:
    """Manages OTP security features including rate limiting, audit logging, and brute force protection."""
    
    # Security settings
    MAX_FAILED_ATTEMPTS_PER_HOUR = 10
    MAX_FAILED_ATTEMPTS_PER_DAY = 50
    LOCKOUT_DURATION_MINUTES = 30
    SUSPICIOUS_ACTIVITY_THRESHOLD = 20
    
    # Cache prefixes
    CACHE_PREFIX = 'otp_security'
    FAILED_ATTEMPTS_PREFIX = f'{CACHE_PREFIX}:failed_attempts'
    LOCKOUT_PREFIX = f'{CACHE_PREFIX}:lockout'
    AUDIT_PREFIX = f'{CACHE_PREFIX}:audit'
    SUSPICIOUS_PREFIX = f'{CACHE_PREFIX}:suspicious'
    
    def __init__(self):
        self.cache_timeout = 86400  # 24 hours
    
    def _get_cache_key(self, prefix: str, user_id: int, channel: str = None, extra: str = None) -> str:
        """Generate cache key for security tracking."""
        key_parts = [prefix, str(user_id)]
        if channel:
            key_parts.append(channel)
        if extra:
            key_parts.append(extra)
        return ':'.join(key_parts)
    
    def _get_ip_hash(self, ip_address: str) -> str:
        """Get hashed IP address for privacy."""
        if not ip_address:
            return 'unknown'
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    def log_otp_attempt(self, user_id: int, channel: str, action: str, success: bool, 
                       ip_address: str = None, user_agent: str = None, 
                       otp_code: str = None, error_message: str = None) -> Dict[str, Any]:
        """
        Log OTP attempt for audit purposes.
        
        Args:
            user_id: User ID
            channel: OTP channel (email/sms)
            action: Action type (request/verify)
            success: Whether the action was successful
            ip_address: Client IP address
            user_agent: Client user agent
            otp_code: OTP code (will be hashed for security)
            error_message: Error message if failed
            
        Returns:
            Dict with audit log entry
        """
        timestamp = time.time()
        audit_entry = {
            'user_id': user_id,
            'channel': channel,
            'action': action,
            'success': success,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat(),
            'ip_hash': self._get_ip_hash(ip_address) if ip_address else None,
            'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest()[:16] if user_agent else None,
            'otp_hash': hashlib.sha256(otp_code.encode()).hexdigest()[:8] if otp_code else None,
            'error_message': error_message
        }
        
        # Store in cache with user-specific key
        audit_key = self._get_cache_key(self.AUDIT_PREFIX, user_id, channel, str(int(timestamp)))
        cache.set(audit_key, audit_entry, self.cache_timeout)
        
        # Also store in a list for easy retrieval
        audit_list_key = self._get_cache_key(self.AUDIT_PREFIX, user_id, 'list')
        audit_list = cache.get(audit_list_key, [])
        audit_list.append(audit_entry)
        
        # Keep only last 100 entries per user
        audit_list = audit_list[-100:]
        cache.set(audit_list_key, audit_list, self.cache_timeout)
        
        # Log to application logger
        log_message = f"OTP {action} {'succeeded' if success else 'failed'} for user {user_id} via {channel}"
        if not success and error_message:
            log_message += f": {error_message}"
        
        if success:
            logger.info(log_message)
        else:
            logger.warning(log_message)
        
        return audit_entry
    
    def track_failed_attempt(self, user_id: int, channel: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Track failed OTP verification attempt.
        
        Returns:
            Dict with tracking information and lockout status
        """
        now = timezone.now()
        hour_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d%H'))
        day_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d'))
        
        # Increment counters
        hour_count = cache.get(hour_key, 0) + 1
        day_count = cache.get(day_key, 0) + 1
        
        cache.set(hour_key, hour_count, 3600)  # 1 hour
        cache.set(day_key, day_count, 86400)   # 24 hours
        
        # Check if lockout is needed
        lockout_triggered = False
        lockout_reason = None
        
        if hour_count >= self.MAX_FAILED_ATTEMPTS_PER_HOUR:
            lockout_triggered = True
            lockout_reason = 'hourly_limit_exceeded'
        elif day_count >= self.MAX_FAILED_ATTEMPTS_PER_DAY:
            lockout_triggered = True
            lockout_reason = 'daily_limit_exceeded'
        
        result = {
            'hour_count': hour_count,
            'day_count': day_count,
            'lockout_triggered': lockout_triggered,
            'lockout_reason': lockout_reason
        }
        
        # Apply lockout if triggered
        if lockout_triggered:
            self._apply_lockout(user_id, channel, lockout_reason, ip_address)
            result['lockout_until'] = self._get_lockout_expiry(user_id, channel)
        
        # Check for suspicious activity
        if day_count >= self.SUSPICIOUS_ACTIVITY_THRESHOLD:
            self._flag_suspicious_activity(user_id, channel, day_count, ip_address)
        
        return result
    
    def _apply_lockout(self, user_id: int, channel: str, reason: str, ip_address: str = None):
        """Apply security lockout for user and channel."""
        lockout_key = self._get_cache_key(self.LOCKOUT_PREFIX, user_id, channel)
        lockout_data = {
            'reason': reason,
            'applied_at': time.time(),
            'expires_at': time.time() + (self.LOCKOUT_DURATION_MINUTES * 60),
            'ip_hash': self._get_ip_hash(ip_address) if ip_address else None
        }
        
        cache.set(lockout_key, lockout_data, self.LOCKOUT_DURATION_MINUTES * 60)
        
        logger.warning(f"OTP lockout applied for user {user_id} on {channel}: {reason}")
    
    def _get_lockout_expiry(self, user_id: int, channel: str) -> Optional[datetime]:
        """Get lockout expiry time."""
        lockout_key = self._get_cache_key(self.LOCKOUT_PREFIX, user_id, channel)
        lockout_data = cache.get(lockout_key)
        
        if lockout_data and 'expires_at' in lockout_data:
            return datetime.fromtimestamp(lockout_data['expires_at'])
        
        return None
    
    def _flag_suspicious_activity(self, user_id: int, channel: str, attempt_count: int, ip_address: str = None):
        """Flag suspicious activity for further investigation."""
        suspicious_key = self._get_cache_key(self.SUSPICIOUS_PREFIX, user_id, channel)
        suspicious_data = {
            'flagged_at': time.time(),
            'attempt_count': attempt_count,
            'ip_hash': self._get_ip_hash(ip_address) if ip_address else None,
            'channel': channel
        }
        
        cache.set(suspicious_key, suspicious_data, self.cache_timeout)
        
        logger.error(f"SUSPICIOUS ACTIVITY: User {user_id} has {attempt_count} failed OTP attempts on {channel}")
        
        # You could add additional actions here like:
        # - Send alert to administrators
        # - Temporarily disable account
        # - Require additional verification
    
    def check_lockout_status(self, user_id: int, channel: str) -> Dict[str, Any]:
        """
        Check if user is currently locked out.
        
        Returns:
            Dict with lockout status and details
        """
        lockout_key = self._get_cache_key(self.LOCKOUT_PREFIX, user_id, channel)
        lockout_data = cache.get(lockout_key)
        
        if not lockout_data:
            return {'locked_out': False}
        
        current_time = time.time()
        expires_at = lockout_data.get('expires_at', 0)
        
        if current_time >= expires_at:
            # Lockout has expired, remove it
            cache.delete(lockout_key)
            return {'locked_out': False}
        
        return {
            'locked_out': True,
            'reason': lockout_data.get('reason', 'unknown'),
            'applied_at': datetime.fromtimestamp(lockout_data.get('applied_at', 0)),
            'expires_at': datetime.fromtimestamp(expires_at),
            'remaining_seconds': int(expires_at - current_time)
        }
    
    def get_failed_attempt_counts(self, user_id: int, channel: str) -> Dict[str, int]:
        """Get current failed attempt counts."""
        now = timezone.now()
        hour_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d%H'))
        day_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d'))
        
        return {
            'hour_count': cache.get(hour_key, 0),
            'day_count': cache.get(day_key, 0),
            'hour_limit': self.MAX_FAILED_ATTEMPTS_PER_HOUR,
            'day_limit': self.MAX_FAILED_ATTEMPTS_PER_DAY
        }
    
    def reset_failed_attempts(self, user_id: int, channel: str):
        """Reset failed attempt counters (e.g., after successful verification)."""
        now = timezone.now()
        hour_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d%H'))
        day_key = self._get_cache_key(self.FAILED_ATTEMPTS_PREFIX, user_id, channel, now.strftime('%Y%m%d'))
        
        cache.delete(hour_key)
        cache.delete(day_key)
        
        logger.info(f"Reset failed attempt counters for user {user_id} on {channel}")
    
    def get_audit_log(self, user_id: int, channel: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get audit log entries for user.
        
        Args:
            user_id: User ID
            channel: Optional channel filter
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        if channel:
            audit_list_key = self._get_cache_key(self.AUDIT_PREFIX, user_id, 'list')
            audit_list = cache.get(audit_list_key, [])
            # Filter by channel
            filtered_list = [entry for entry in audit_list if entry.get('channel') == channel]
            return filtered_list[-limit:]
        else:
            audit_list_key = self._get_cache_key(self.AUDIT_PREFIX, user_id, 'list')
            audit_list = cache.get(audit_list_key, [])
            return audit_list[-limit:]
    
    def get_security_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive security summary for user.
        
        Returns:
            Dict with security status and statistics
        """
        summary = {
            'user_id': user_id,
            'channels': {},
            'overall_status': 'normal',
            'alerts': []
        }
        
        for channel in ['email', 'sms']:
            # Check lockout status
            lockout_status = self.check_lockout_status(user_id, channel)
            
            # Get failed attempt counts
            attempt_counts = self.get_failed_attempt_counts(user_id, channel)
            
            # Check for suspicious activity
            suspicious_key = self._get_cache_key(self.SUSPICIOUS_PREFIX, user_id, channel)
            suspicious_data = cache.get(suspicious_key)
            
            channel_summary = {
                'locked_out': lockout_status['locked_out'],
                'failed_attempts': attempt_counts,
                'suspicious_activity': bool(suspicious_data),
                'recent_audit_entries': len(self.get_audit_log(user_id, channel, 10))
            }
            
            if lockout_status['locked_out']:
                channel_summary['lockout_details'] = lockout_status
                summary['overall_status'] = 'locked_out'
                summary['alerts'].append(f'{channel.upper()} channel is locked out until {lockout_status["expires_at"]}')
            
            if suspicious_data:
                summary['overall_status'] = 'suspicious' if summary['overall_status'] == 'normal' else summary['overall_status']
                summary['alerts'].append(f'Suspicious activity detected on {channel.upper()} channel')
            
            summary['channels'][channel] = channel_summary
        
        return summary
    
    def cleanup_expired_data(self):
        """Clean up expired security data (should be run periodically)."""
        # This is a placeholder for cleanup logic
        # In a production environment, you might want to implement this
        # to clean up old audit logs and expired lockouts
        logger.info("OTP security data cleanup completed")

# Global security manager instance
otp_security_manager = OTPSecurityManager()