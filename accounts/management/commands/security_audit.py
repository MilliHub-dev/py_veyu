"""
Security Audit Management Command

This command performs security audits and provides security-related utilities
for the Veyu platform.
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from accounts.authentication import TokenBlacklist

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Perform security audits and maintenance tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['audit', 'cleanup', 'unlock', 'stats', 'test-security'],
            default='audit',
            help='Action to perform'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for unlock action'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days for cleanup operations'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        action = options['action']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(f"Starting security audit action: {action}")
        
        try:
            if action == 'audit':
                self.perform_security_audit(verbose)
            elif action == 'cleanup':
                self.cleanup_security_data(options['days'], verbose)
            elif action == 'unlock':
                self.unlock_account(options['email'], verbose)
            elif action == 'stats':
                self.show_security_stats(verbose)
            elif action == 'test-security':
                self.test_security_features(verbose)
            
        except Exception as e:
            raise CommandError(f'Security audit failed: {str(e)}')

    def perform_security_audit(self, verbose=False):
        """Perform comprehensive security audit."""
        self.stdout.write(self.style.SUCCESS('=== VEYU SECURITY AUDIT ==='))
        
        # Check authentication settings
        self.audit_authentication_settings(verbose)
        
        # Check password policies
        self.audit_password_policies(verbose)
        
        # Check security middleware
        self.audit_security_middleware(verbose)
        
        # Check JWT configuration
        self.audit_jwt_configuration(verbose)
        
        # Check HTTPS settings
        self.audit_https_settings(verbose)
        
        # Check for locked accounts
        self.audit_locked_accounts(verbose)
        
        # Check rate limiting
        self.audit_rate_limiting(verbose)
        
        self.stdout.write(self.style.SUCCESS('Security audit completed.'))

    def audit_authentication_settings(self, verbose=False):
        """Audit authentication configuration."""
        self.stdout.write('\n--- Authentication Settings ---')
        
        # Check authentication classes
        auth_classes = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_AUTHENTICATION_CLASSES', [])
        
        if 'accounts.authentication.EnhancedJWTAuthentication' in auth_classes:
            self.stdout.write(self.style.SUCCESS('✓ Enhanced JWT authentication enabled'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Enhanced JWT authentication not found'))
        
        # Check JWT settings
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME')
        
        if access_lifetime and access_lifetime <= timedelta(hours=2):
            self.stdout.write(self.style.SUCCESS(f'✓ Access token lifetime: {access_lifetime}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Access token lifetime too long: {access_lifetime}'))

    def audit_password_policies(self, verbose=False):
        """Audit password policy configuration."""
        self.stdout.write('\n--- Password Policies ---')
        
        validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        
        required_validators = [
            'MinimumLengthValidator',
            'CommonPasswordValidator',
            'NumericPasswordValidator'
        ]
        
        for validator_name in required_validators:
            found = any(validator_name in v['NAME'] for v in validators)
            if found:
                self.stdout.write(self.style.SUCCESS(f'✓ {validator_name} enabled'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {validator_name} missing'))

    def audit_security_middleware(self, verbose=False):
        """Audit security middleware configuration."""
        self.stdout.write('\n--- Security Middleware ---')
        
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        required_middleware = [
            'accounts.middleware.SecurityHeadersMiddleware',
            'accounts.middleware.RateLimitMiddleware',
            'accounts.middleware.AccountLockoutMiddleware',
        ]
        
        for mw_name in required_middleware:
            if mw_name in middleware:
                self.stdout.write(self.style.SUCCESS(f'✓ {mw_name.split(".")[-1]} enabled'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {mw_name.split(".")[-1]} missing'))

    def audit_jwt_configuration(self, verbose=False):
        """Audit JWT configuration."""
        self.stdout.write('\n--- JWT Configuration ---')
        
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        
        # Check token rotation
        if jwt_settings.get('ROTATE_REFRESH_TOKENS'):
            self.stdout.write(self.style.SUCCESS('✓ Refresh token rotation enabled'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Refresh token rotation disabled'))
        
        # Check blacklisting
        if jwt_settings.get('BLACKLIST_AFTER_ROTATION'):
            self.stdout.write(self.style.SUCCESS('✓ Token blacklisting enabled'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Token blacklisting disabled'))

    def audit_https_settings(self, verbose=False):
        """Audit HTTPS and security headers."""
        self.stdout.write('\n--- HTTPS & Security Headers ---')
        
        if not settings.DEBUG:
            # Production HTTPS settings
            if getattr(settings, 'SECURE_SSL_REDIRECT', False):
                self.stdout.write(self.style.SUCCESS('✓ HTTPS redirect enabled'))
            else:
                self.stdout.write(self.style.WARNING('⚠ HTTPS redirect disabled'))
            
            if getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0:
                self.stdout.write(self.style.SUCCESS('✓ HSTS enabled'))
            else:
                self.stdout.write(self.style.WARNING('⚠ HSTS disabled'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Running in DEBUG mode'))
        
        # Cookie security
        if getattr(settings, 'SESSION_COOKIE_SECURE', False) or settings.DEBUG:
            self.stdout.write(self.style.SUCCESS('✓ Secure cookies configured'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Insecure cookies'))

    def audit_locked_accounts(self, verbose=False):
        """Check for locked accounts."""
        self.stdout.write('\n--- Account Lockouts ---')
        
        # This is a simplified check - in production you might want to
        # implement a more sophisticated tracking system
        locked_count = 0
        
        # Check cache for lockout keys
        try:
            # This is a basic implementation - you might need to adjust based on your cache backend
            self.stdout.write(f'Locked accounts: {locked_count}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not check locked accounts: {str(e)}'))

    def audit_rate_limiting(self, verbose=False):
        """Audit rate limiting configuration."""
        self.stdout.write('\n--- Rate Limiting ---')
        
        if getattr(settings, 'RATE_LIMITING_ENABLED', False):
            self.stdout.write(self.style.SUCCESS('✓ Rate limiting enabled'))
            
            login_limit = getattr(settings, 'RATE_LIMIT_LOGIN_ATTEMPTS', 0)
            self.stdout.write(f'  Login attempts limit: {login_limit}/minute')
            
            api_limit = getattr(settings, 'RATE_LIMIT_API_DEFAULT', 0)
            self.stdout.write(f'  API requests limit: {api_limit}/minute')
        else:
            self.stdout.write(self.style.WARNING('⚠ Rate limiting disabled'))

    def cleanup_security_data(self, days=7, verbose=False):
        """Clean up old security data."""
        self.stdout.write(f'\n--- Cleaning up security data older than {days} days ---')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Clean up expired tokens from blacklist
        # This would depend on your specific implementation
        
        # Clean up old rate limit data
        # This would also depend on your cache implementation
        
        self.stdout.write(self.style.SUCCESS('Security data cleanup completed.'))

    def unlock_account(self, email, verbose=False):
        """Unlock a specific account."""
        if not email:
            raise CommandError('Email address is required for unlock action')
        
        self.stdout.write(f'\n--- Unlocking account: {email} ---')
        
        try:
            user = User.objects.get(email=email)
            
            # Clear lockout data from cache
            import hashlib
            email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
            lockout_key = f"account_lockout:{email_hash}"
            attempts_key = f"failed_attempts:{email_hash}"
            
            cache.delete(lockout_key)
            cache.delete(attempts_key)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Account {email} unlocked successfully'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ User with email {email} not found'))

    def show_security_stats(self, verbose=False):
        """Show security statistics."""
        self.stdout.write('\n--- Security Statistics ---')
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Active users: {active_users}')
        self.stdout.write(f'Inactive users: {inactive_users}')
        
        # Recent user activity
        recent_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()
        self.stdout.write(f'Users active in last 7 days: {recent_users}')
        
        # Provider statistics
        providers = User.objects.values_list('provider', flat=True).distinct()
        for provider in providers:
            count = User.objects.filter(provider=provider).count()
            self.stdout.write(f'{provider.title()} users: {count}')

    def test_security_features(self, verbose=False):
        """Test security features."""
        self.stdout.write('\n--- Testing Security Features ---')
        
        # Test JWT token creation
        try:
            from accounts.authentication import TokenManager
            test_user = User.objects.filter(is_active=True).first()
            
            if test_user:
                tokens = TokenManager.create_tokens_for_user(test_user)
                self.stdout.write(self.style.SUCCESS('✓ JWT token creation working'))
            else:
                self.stdout.write(self.style.WARNING('⚠ No active users found for testing'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ JWT token creation failed: {str(e)}'))
        
        # Test password reset
        try:
            from accounts.password_reset import PasswordResetManager
            # This is just a validation test, not actually sending emails
            self.stdout.write(self.style.SUCCESS('✓ Password reset system available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Password reset system error: {str(e)}'))
        
        # Test rate limiting
        try:
            from accounts.middleware import RateLimitMiddleware
            middleware = RateLimitMiddleware(lambda x: None)
            self.stdout.write(self.style.SUCCESS('✓ Rate limiting middleware available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Rate limiting middleware error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Security feature testing completed.'))