from django.urls import path

from .views import SignUpView, LoginView, VerifyEmailView, VerifyPhoneNumberView
from .auth_views import (
    EnhancedSignUpView, 
    EnhancedLoginView, 
    TokenRefreshView, 
    LogoutView
)
from .password_reset_views import (
    PasswordResetRequestView, 
    PasswordResetConfirmView,
    PasswordResetTokenValidationView
)

urlpatterns = [
    # Enhanced Authentication
    path('signup/', EnhancedSignUpView.as_view(), name='enhanced_signup'),
    path('login/', EnhancedLoginView.as_view(), name='enhanced_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Legacy Authentication (for backward compatibility)
    path('legacy/signup/', SignUpView.as_view(), name='legacy_signup'),
    path('legacy/login/', LoginView.as_view(), name='legacy_login'),
    
    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    
    # Phone verification
    path('verify-phone/', VerifyPhoneNumberView.as_view(), name='verify-phone'),
    
    # Password reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/validate/', PasswordResetTokenValidationView.as_view(), name='password_reset_validate'),
]
