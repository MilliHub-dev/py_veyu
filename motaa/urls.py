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
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework import permissions
from utils.admin import motaa_admin

schema_view = get_schema_view(
    openapi.Info(
        title="Project API Documentation",
        default_version='v1',
        description="API documentation for Motaa",
    ),
    public=True,
    authentication_classes=[BasicAuthentication, SessionAuthentication],
    permission_classes=(permissions.AllowAny, permissions.IsAuthenticated),
)



urlpatterns = [
    # Admin
    path('admin/', motaa_admin.urls),
    path('old-admin/', admin.site.urls),
    
    # Api Documetation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # Redoc UI
    
    # API Endpoints
    path('api/v1/accounts/', include('accounts.api.urls', namespace='accounts_api')),
    path('api/v1/mechanics/', include('bookings.api.urls', namespace='bookings_api')),
    path('api/v1/listings/', include('listings.api.urls', namespace='listings_api')),
    path('api/v1/chat/', include('chat.api.urls', namespace="chat_api")),
    path('api/v1/wallet/', include('wallet.urls')),
    path('api/v1/admin/mechanics/', include('bookings.api.mechanic_urls', namespace='mechanics_api')),
    path('api/v1/admin/dealership/', include('listings.api.dealership_urls', namespace='dealership_api')),
    
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
    path('', include('utils.urls', namespace='utils')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





admin.site.index_title = 'MOTAA ADMINISTRATION'
admin.site.site_header = 'MOTAA ADMIN'
admin.site.site_title = 'MOTAA ADMIN'