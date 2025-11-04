from django.urls import path, include

# Import views
from .views import (
    SignUpView,
    UpdateProfileView,
    BusinessVerificationView,
    CartView,
    NotificationView,
)
from .test_views import TestEmailView

# Import authentication URLs
from .auth_urls import urlpatterns as auth_urls

app_name = 'accounts_api'

urlpatterns = [
    # Authentication endpoints (login, register, password reset, etc.)
    path('', include(auth_urls)),
    
    # Business verification
    path('verify-business/', BusinessVerificationView.as_view(), name='verify-business'),
    
    # User profile
    path('profile/', UpdateProfileView.as_view(), name='update-profile'),
    
    # Cart
    path('cart/', CartView.as_view(), name='cart'),
    
    # Notifications
    path('notifications/', NotificationView.as_view(), name='notifications'),
    
    # Test email endpoint (for development)
    path('test-email/', TestEmailView.as_view(), name='test-email'),
    
    # Django REST Auth URLs
    path('auth/', include('dj_rest_auth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

