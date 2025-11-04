from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import SignUpView, LoginView, VerifyEmailView, VerifyPhoneNumberView
from .password_reset_views import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    # Authentication
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    
    # Phone verification
    path('verify-phone/', VerifyPhoneNumberView.as_view(), name='verify-phone'),
    
    # Password reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
