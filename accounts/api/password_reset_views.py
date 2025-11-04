from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import OTP
from accounts.utils.email_notifications import send_password_reset_email
from utils.otp import make_random_otp

User = get_user_model()

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': True, 'message': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security reasons
            return Response(
                {'success': True, 'message': 'If an account exists with this email, a password reset link has been sent.'},
                status=status.HTTP_200_OK
            )
        
        # Generate a password reset token
        token = str(RefreshToken.for_user(user).access_token)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Send password reset email
        email_sent = send_password_reset_email(user, reset_link)
        
        if email_sent:
            return Response(
                {'success': True, 'message': 'Password reset link has been sent to your email.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': True, 'message': 'Failed to send password reset email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response(
                {'error': True, 'message': 'Token and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify the token and get the user
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
            
            # Set new password
            user.set_password(password)
            user.save()
            
            # Invalidate all user's refresh tokens
            user.auth_token_set.all().delete()
            
            return Response(
                {'success': True, 'message': 'Password has been reset successfully.'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': True, 'message': 'Invalid or expired token. Please request a new password reset.'},
                status=status.HTTP_400_BAD_REQUEST
            )
