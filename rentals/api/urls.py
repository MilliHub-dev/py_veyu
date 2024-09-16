from django.urls import path
from .views import (
    ListingsView,
    CreateListingView,
    VehicleView,
    VehicleDetailView,
    AvailableForRentView,
    BookCarRentalView,
    AvailableForRentDetailView,
    CreateVehicleView
)


app_name = 'rentals_api'

# English or spanish 😂🫴

urlpatterns = [
    # listing
    path('listings/', ListingsView.as_view(), name='listings'),
    path('listings/add/', CreateListingView.as_view(), name='add-listing'),

    # cars
    path('cars/', VehicleView.as_view(), name='vehicle-view'),
    path('cars/create/', CreateVehicleView.as_view(), name='vehicle-create'),
    path('cars/<uuid:uuid>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    # Not so need but that was how it was stated in the docs
    path('cars/<uuid:uuid>/update/', VehicleDetailView.as_view(), name='vehicle-update'), 
    path('cars/<uuid:uuid>/delete/', VehicleDetailView.as_view(), name='vehicle-delete'),

    # Rentals
    path('', AvailableForRentView.as_view(), name='rentals'),
    path('book/', BookCarRentalView.as_view(), name='book-car-rental'),
    path('<uuid:uuid>/', AvailableForRentDetailView.as_view(), name='rental-detail'),
]




