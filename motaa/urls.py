from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.api.urls', namespace='accounts_api')),
    path('api/rentals/', include('rentals.api.urls', namespace='rentals_api')),
    path('api/v1/wallet', include('wallet.urls')),
    path('', include('utils.urls', namespace='utils')),
]


admin.site.index_title = 'MOTAA ADMINISTRATION'
admin.site.site_header = 'MOTAA ADMIN'
admin.site.site_title = 'MOTAA ADMIN'