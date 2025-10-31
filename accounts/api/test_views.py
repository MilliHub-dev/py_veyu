from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
import logging

logger = logging.getLogger('utils.mail')

class TestEmailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            logger.info("Testing email functionality...")
            
            # Test sending a simple email
            from django.core.mail import send_mail
            
            # Test 1: Simple email
            send_mail(
                'Test Email from Veyu',
                'This is a test email from Veyu.',
                settings.DEFAULT_FROM_EMAIL,
                ['test@example.com'],
                fail_silently=False,
            )
            
            # Test 2: Using our custom send_email function
            from utils.mail import send_email
            
            send_email(
                subject='Test Email with Template',
                recipients=['test@example.com'],
                message='This is a test email with template.',
                template='utils/templates/verification_email.html',
                context={
                    'name': 'Test User',
                    'verification_code': '123456'
                }
            )
            
            return Response({
                'success': True,
                'message': 'Test emails sent successfully. Check the logs and sent_emails directory.',
                'email_backend': settings.EMAIL_BACKEND,
                'email_file_path': getattr(settings, 'EMAIL_FILE_PATH', 'Not set')
            })
            
        except Exception as e:
            logger.error(f"Error in test email: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e),
                'email_backend': settings.EMAIL_BACKEND,
                'email_file_path': getattr(settings, 'EMAIL_FILE_PATH', 'Not set')
            }, status=500)
