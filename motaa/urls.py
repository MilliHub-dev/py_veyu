from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.api.urls', namespace='accounts_api')),
    path('api/rentals/', include('rentals.api.urls', namespace='rentals_api')),
    path('api/v1/wallet', include('wallet.urls')),
    path('', include('utils.urls', namespace='utils')),
    path('api/v1/wallet', include('wallet.urls')),

     #JWT Token Views
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





admin.site.index_title = 'MOTAA ADMINISTRATION'
admin.site.site_header = 'MOTAA ADMIN'
admin.site.site_title = 'MOTAA ADMIN'