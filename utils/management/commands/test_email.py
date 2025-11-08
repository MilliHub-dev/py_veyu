"""
Django management command to test email functionality.
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from utils.mail import send_email, test_email_connection, validate_email_configuration, get_email_backend_health
import logging

logger = logging.getLogger('utils.mail')


class Command(BaseCommand):
    help = 'Test email functionality and configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='Test Email from Veyu',
            help='Subject for test email'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check configuration and connection, do not send email'
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Perform comprehensive health check'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        if options['verbose']:
            logging.getLogger('utils.mail').setLevel(logging.DEBUG)
        
        self.stdout.write(self.style.SUCCESS('=== Email System Test ==='))
        
        # Configuration check
        self.stdout.write('\n1. Configuration Check:')
        config_result = validate_email_configuration()
        
        if config_result['valid']:
            self.stdout.write(self.style.SUCCESS('✓ Configuration is valid'))
        else:
            self.stdout.write(self.style.ERROR('✗ Configuration issues found:'))
            for error in config_result['errors']:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            for warning in config_result['warnings']:
                self.stdout.write(self.style.WARNING(f'  ! {warning}'))
        
        # Connection test
        self.stdout.write('\n2. Connection Test:')
        connection_result = test_email_connection()
        
        if connection_result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Connection successful in {connection_result.get("connection_time", 0):.2f}s'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection failed: {connection_result.get("error", "Unknown error")}')
            )
        
        # Health check
        if options['health_check']:
            self.stdout.write('\n3. Health Check:')
            health_result = get_email_backend_health()
            
            status_style = {
                'healthy': self.style.SUCCESS,
                'warning': self.style.WARNING,
                'unhealthy': self.style.ERROR,
                'error': self.style.ERROR
            }.get(health_result.get('status', 'error'), self.style.ERROR)
            
            self.stdout.write(status_style(f'Status: {health_result.get("status", "unknown").upper()}'))
            
            if health_result.get('issues'):
                self.stdout.write('Issues found:')
                for issue in health_result['issues']:
                    self.stdout.write(f'  - {issue}')
        
        # Send test email
        if not options['check_only'] and options['to']:
            self.stdout.write(f'\n4. Sending Test Email to {options["to"]}:')
            
            try:
                success = send_email(
                    subject=options['subject'],
                    recipients=[options['to']],
                    message=f"""
This is a test email from the Veyu platform.

Email Backend: {settings.EMAIL_BACKEND}
Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
SSL Verify: {getattr(settings, 'EMAIL_SSL_VERIFY', 'Not set')}
Timeout: {settings.EMAIL_TIMEOUT}s

If you received this email, the email system is working correctly.

Best regards,
Veyu Team
                    """.strip(),
                    fail_silently=False
                )
                
                if success:
                    self.stdout.write(self.style.SUCCESS('✓ Test email sent successfully!'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Test email failed to send'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Test email failed: {e}'))
        
        elif not options['check_only'] and not options['to']:
            self.stdout.write(
                self.style.WARNING('\nTo send a test email, use: --to your@email.com')
            )
        
        # Summary
        self.stdout.write('\n=== Summary ===')
        if config_result['valid'] and connection_result['success']:
            self.stdout.write(self.style.SUCCESS('Email system appears to be working correctly.'))
        else:
            self.stdout.write(self.style.WARNING('Email system has issues that need attention.'))
        
        self.stdout.write('\nFor more help, run: python manage.py test_email --help')