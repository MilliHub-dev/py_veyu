"""
Django management command to check email connectivity and configuration.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from utils.email_detector import detect_network_connectivity, get_optimal_email_backend
import socket
import logging

logger = logging.getLogger('utils.mail')


class Command(BaseCommand):
    help = 'Check email connectivity and determine optimal backend'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--test-smtp',
            action='store_true',
            help='Test SMTP connectivity to configured host'
        )
    
    def handle(self, *args, **options):
        if options['verbose']:
            logging.getLogger('utils.mail').setLevel(logging.DEBUG)
        
        self.stdout.write(self.style.SUCCESS('=== Email Connectivity Check ==='))
        
        # 1. Check general network connectivity
        self.stdout.write('\n1. Network Connectivity:')
        has_network = detect_network_connectivity()
        
        if has_network:
            self.stdout.write(self.style.SUCCESS('✓ Network connectivity available'))
        else:
            self.stdout.write(self.style.ERROR('✗ No network connectivity detected'))
        
        # 2. Check SMTP connectivity
        self.stdout.write('\n2. SMTP Connectivity:')
        email_host = getattr(settings, 'EMAIL_HOST', '')
        email_port = getattr(settings, 'EMAIL_PORT', 587)
        
        if not email_host:
            self.stdout.write(self.style.WARNING('! No EMAIL_HOST configured'))
        else:
            self.stdout.write(f'Testing connection to {email_host}:{email_port}...')
            
            try:
                sock = socket.create_connection((email_host, email_port), timeout=10)
                sock.close()
                self.stdout.write(self.style.SUCCESS(f'✓ SMTP server reachable at {email_host}:{email_port}'))
            except socket.timeout:
                self.stdout.write(self.style.ERROR(f'✗ Connection timeout to {email_host}:{email_port}'))
            except socket.gaierror as e:
                self.stdout.write(self.style.ERROR(f'✗ DNS resolution failed: {e}'))
            except OSError as e:
                if e.errno == 101:
                    self.stdout.write(self.style.ERROR(f'✗ Network unreachable to {email_host}:{email_port}'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Connection failed: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Unexpected error: {e}'))
        
        # 3. Determine optimal backend
        self.stdout.write('\n3. Optimal Email Backend:')
        optimal_backend = get_optimal_email_backend()
        current_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
        
        self.stdout.write(f'Current backend: {current_backend}')
        self.stdout.write(f'Optimal backend: {optimal_backend}')
        
        if 'console' in optimal_backend.lower():
            self.stdout.write(self.style.WARNING('→ Console backend recommended (emails will be logged, not sent)'))
        elif 'smtp' in optimal_backend.lower() or 'Reliable' in optimal_backend:
            self.stdout.write(self.style.SUCCESS('→ SMTP backend recommended (emails will be sent via SMTP)'))
        elif 'Adaptive' in optimal_backend:
            self.stdout.write(self.style.SUCCESS('→ Adaptive backend (automatically chooses best option)'))
        
        # 4. Configuration summary
        self.stdout.write('\n4. Configuration Summary:')
        self.stdout.write(f'DEBUG mode: {getattr(settings, "DEBUG", False)}')
        self.stdout.write(f'USE_CONSOLE_EMAIL: {getattr(settings, "USE_CONSOLE_EMAIL", False)}')
        self.stdout.write(f'USE_SMTP_IN_DEV: {getattr(settings, "USE_SMTP_IN_DEV", False)}')
        self.stdout.write(f'EMAIL_HOST: {email_host or "Not set"}')
        self.stdout.write(f'EMAIL_PORT: {email_port}')
        self.stdout.write(f'EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", False)}')
        
        # 5. Recommendations
        self.stdout.write('\n5. Recommendations:')
        
        if not has_network:
            self.stdout.write(self.style.WARNING('• Server has no internet access - emails will be logged to console'))
            self.stdout.write('• This is normal for some production environments')
            self.stdout.write('• Consider using a local mail relay or external email service')
        elif not email_host:
            self.stdout.write(self.style.WARNING('• Configure EMAIL_HOST for SMTP delivery'))
        elif 'console' in optimal_backend.lower():
            self.stdout.write(self.style.WARNING('• SMTP not available - using console backend'))
        else:
            self.stdout.write(self.style.SUCCESS('• Email system should work normally'))
        
        self.stdout.write('\n=== Check Complete ===')
        
        # Test email sending if requested
        if options['test_smtp'] and has_network and email_host:
            self.stdout.write('\n6. Testing Email Send:')
            try:
                from utils.mail import send_email
                success = send_email(
                    subject='Connectivity Test',
                    recipients=['test@example.com'],
                    message='This is a connectivity test email.',
                    fail_silently=True
                )
                
                if success:
                    self.stdout.write(self.style.SUCCESS('✓ Email send test passed'))
                else:
                    self.stdout.write(self.style.WARNING('! Email send test failed (check logs)'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Email send test error: {e}'))