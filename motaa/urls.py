from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView



urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/v1/accounts/', include('accounts.api.urls', namespace='accounts_api')),
    path('api/v1/mechanics/', include('bookings.api.urls', namespace='bookings_api')),
    path('api/v1/listings/', include('listings.api.urls', namespace='listings_api')),
    path('api/v1/chat/', include('chat.api.urls', namespace="chat_api")),
    path('api/v1/wallet/', include('wallet.urls')),
    path('', include('utils.urls', namespace='utils')),
    
    # JWT Token Views
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Password Reset
    path('api/v1/password-reset/', PasswordResetView.as_view()),
    path(
        'api/v1/password-reset-confirm/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





admin.site.index_title = 'MOTAA ADMINISTRATION'
admin.site.site_header = 'MOTAA ADMIN'
admin.site.site_title = 'MOTAA ADMIN'