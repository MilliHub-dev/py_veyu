from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rentals/', include('rentals.api.urls', namespace='rentals_api')),
    path('', include('utils.urls', namespace='utils')),
]
