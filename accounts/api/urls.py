from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views
from .views import (
    SignUpView,
    UpdateProfileView,
    BusinessVerificationView,
    CartView,
    NotificationView,
    RegisterDeviceView,
    VerifyEmailUnauthenticatedView,
    LocationViewSet,
    ReferralView,
)
from .test_views import TestEmailView
from .document_views import (
    serve_verification_document,
    get_document_requirements,
    get_user_verification_documents,
)
from .otp_security_views import (
    OTPSecurityStatusView,
    OTPSecurityActionsView,
    OTPSystemStatusView,
)

# Import authentication URLs
from .auth_urls import urlpatterns as auth_urls

app_name = 'accounts_api'

# Create router for viewsets
router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = [
    # Authentication endpoints (login, register, password reset, etc.)
    path('', include(auth_urls)),
    
    # Location endpoints (viewset routes)
    path('', include(router.urls)),
    
    # Business verification
    path('verify-business/', BusinessVerificationView.as_view(), name='verify-business'),
    path('verification-status/', BusinessVerificationView.as_view(), name='verification-status'),
    
    # Document management
    path('verification/documents/<int:submission_id>/<str:document_type>/', 
         serve_verification_document, name='serve-verification-document'),
    path('verification/requirements/', 
         get_document_requirements, name='document-requirements'),
    path('verification/my-documents/', 
         get_user_verification_documents, name='my-verification-documents'),
    
    # User profile
    path('profile/', UpdateProfileView.as_view(), name='update-profile'),
    
    # Referral
    path('referral/', ReferralView.as_view(), name='referral'),

    # Cart
    path('cart/', CartView.as_view(), name='cart'),
    
    # Notifications
    path('notifications/', NotificationView.as_view(), name='notifications'),
    path('notifications/register-device/', RegisterDeviceView.as_view(), name='register-device'),
    
    # Unauthenticated email verification
    path('verify-email-unauthenticated/', VerifyEmailUnauthenticatedView.as_view(), name='verify-email-unauthenticated'),
    
    # Test email endpoint (for development)
    path('test-email/', TestEmailView.as_view(), name='test-email'),
    
    # OTP Security endpoints
    path('otp/security/status/', OTPSecurityStatusView.as_view(), name='otp-security-status'),
    path('otp/security/actions/', OTPSecurityActionsView.as_view(), name='otp-security-actions'),
    path('otp/system/status/', OTPSystemStatusView.as_view(), name='otp-system-status'),
    
    # Django REST Auth URLs
    path('auth/', include('dj_rest_auth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

