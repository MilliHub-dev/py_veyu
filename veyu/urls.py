from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

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
from utils.admin import veyu_admin

schema_view = get_schema_view(
    openapi.Info(
        title="Veyu API Documentation",
        default_version='v1',
        description="Comprehensive API documentation for Veyu - Redefining Mobility Platform. "
                   "This API provides endpoints for vehicle marketplace, mechanic services, "
                   "real-time chat, digital wallet, and user management.",
        terms_of_service="https://veyu.cc/terms/",
        contact=openapi.Contact(email="api@veyu.cc"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    authentication_classes=(),
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    # Admin
    path('admin/', veyu_admin.urls, name='admin'),
    # path('old-admin/', include(admin.site.urls)),  # Keep the old admin for reference, remove later if not needed

    # Api Documetation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # Redoc UI

    # API Endpoints
    path('api/v1/accounts/', include('accounts.api.urls', namespace='accounts_api')),
    # path('api/v1/mechanics/', include('bookings.api.urls', namespace='bookings_api')),
    path('api/v1/listings/', include('listings.api.urls', namespace='listings_api')),
    path('api/v1/chat/', include('chat.api.urls', namespace="chat_api")),
    path('api/v1/wallet/', include('wallet.urls')),
    path('api/v1/admin/mechanics/', include('bookings.api.mechanic_urls', namespace='mechanics_api')),
    path('api/v1/admin/dealership/', include('listings.api.dealership_urls', namespace='dealership_api')),
    path('api/v1/inspections/', include('inspections.urls', namespace='inspections_api')),

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
    
    # Log Viewer
    path('logs/', include('utils.log_urls', namespace='logs')),
    
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
    # path('', include('utils.urls', namespace='utils')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





admin.site.index_title = 'Veyu'
admin.site.site_header = 'Veyu'
admin.site.site_title = 'Veyu'