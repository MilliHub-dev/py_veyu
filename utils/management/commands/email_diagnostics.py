"""
Django management command for email system diagnostics and maintenance.
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from utils.mail import (
    validate_email_configuration,
    test_smtp_connection,
    get_email_backend_health,
    process_email_queue,
    get_email_queue_status
)


class Command(BaseCommand):
    help = 'Email system diagnostics and maintenance'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['validate', 'test-connection', 'health-check', 'process-queue', 'queue-status'],
            help='Action to perform'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=5,
            help='Maximum retry count for processing queue (default: 5)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )

    def handle(self, *args, **options):
        action = options['action']
        json_output = options['json']

        try:
            if action == 'validate':
                result = validate_email_configuration()
                self._output_result('Email Configuration Validation', result, json_output)
                
                if not result['valid']:
                    raise CommandError('Email configuration is invalid')

            elif action == 'test-connection':
                result = test_smtp_connection()
                self._output_result('SMTP Connection Test', result, json_output)
                
                if not result['success']:
                    raise CommandError(f"SMTP connection failed: {result.get('error', 'Unknown error')}")

            elif action == 'health-check':
                result = get_email_backend_health()
                self._output_result('Email Backend Health Check', result, json_output)
                
                if not result['healthy']:
                    self.stdout.write(
                        self.style.WARNING(f"Health check issues: {', '.join(result.get('issues', []))}")
                    )

            elif action == 'process-queue':
                max_retries = options['max_retries']
                result = process_email_queue(max_retries)
                self._output_result('Email Queue Processing', result, json_output)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed {result['processed']} emails: "
                        f"{result['sent']} sent, {result['failed']} failed, {result['skipped']} skipped"
                    )
                )

            elif action == 'queue-status':
                result = get_email_queue_status()
                self._output_result('Email Queue Status', result, json_output)
                
                if result.get('total', 0) > 0:
                    self.stdout.write(
                        self.style.WARNING(f"Queue contains {result['total']} emails")
                    )
                else:
                    self.stdout.write(self.style.SUCCESS("Email queue is empty"))

        except Exception as e:
            if json_output:
                self.stdout.write(json.dumps({'error': str(e)}, indent=2))
            else:
                raise CommandError(f"Command failed: {str(e)}")

    def _output_result(self, title, result, json_output):
        """Output result in either JSON or human-readable format."""
        if json_output:
            self.stdout.write(json.dumps(result, indent=2, default=str))
        else:
            self.stdout.write(self.style.HTTP_INFO(f"\n{title}:"))
            self.stdout.write("-" * (len(title) + 1))
            
            if isinstance(result, dict):
                self._print_dict(result, indent=0)
            else:
                self.stdout.write(str(result))

    def _print_dict(self, data, indent=0):
        """Print dictionary in a readable format."""
        prefix = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                self.stdout.write(f"{prefix}{key}:")
                self._print_dict(value, indent + 1)
            elif isinstance(value, list):
                self.stdout.write(f"{prefix}{key}:")
                for item in value:
                    self.stdout.write(f"{prefix}  - {item}")
            else:
                # Color code certain values
                if key in ['valid', 'success', 'healthy'] and value:
                    colored_value = self.style.SUCCESS(str(value))
                elif key in ['valid', 'success', 'healthy'] and not value:
                    colored_value = self.style.ERROR(str(value))
                elif key in ['errors'] and value:
                    colored_value = self.style.ERROR(str(value))
                elif key in ['warnings'] and value:
                    colored_value = self.style.WARNING(str(value))
                else:
                    colored_value = str(value)
                
                self.stdout.write(f"{prefix}{key}: {colored_value}")