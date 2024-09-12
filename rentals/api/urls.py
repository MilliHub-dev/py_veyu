from django.urls import path
from .views import (
    ListingsView,
    CreateListingView,
)


app_name = 'rentals_api'


urlpatterns = [
    path('listings/', ListingsView.as_view(), name='listings'),
    path('listings/add/', CreateListingView.as_view(), name='add-listing'),
]




