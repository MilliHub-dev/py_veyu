from django.urls import path
from .views import (
    ListingsView,
    CreateListingView,
    ListingsDetailsView,
    VehicleView,
    VehicleDetailView,
    AvailableForRentView,
    BookCarRentalView,
    AvailableForRentDetailView,
    CreateVehicleView,
    BookCarRentalViewDetailView,
    AvailableForBuyingView,
    TestDriveRequestView,
    TradeInRequestViewSet,
    CompleteOrderView,
    ViewCarOffersView
)


app_name = 'rentals_api'

# English or spanish 😂🫴

urlpatterns = [
    # listing task 1
    # path('cars/', ListingsView.as_view(), name='cars'),
    # path('cars/add/', CreateListingView.as_view(), name='add-cars'),
    # path('cars/<uuid:uuid>/', ListingsDetailsView.as_view(), name='cars-detail'),
    # # Not so need but that was how it was stated in the docs
    # path('cars/<uuid:uuid>/update/', ListingsDetailsView.as_view(), name='cars-update'),
    # path('cars/<uuid:uuid>/delete/', ListingsDetailsView.as_view(), name='cars-delete'),

    # listing task 1
    path('cars/', VehicleView.as_view(), name='vehicle-view'),
    path('cars/create/', CreateVehicleView.as_view(), name='vehicle-create'),
    path('cars/<uuid:uuid>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    # Not so need but that was how it was stated in the docs
    path('cars/<uuid:uuid>/update/', VehicleDetailView.as_view(), name='vehicle-update'), 
    path('cars/<uuid:uuid>/delete/', VehicleDetailView.as_view(), name='vehicle-delete'),

    # Rentals task 2
    path('rentals/', AvailableForRentView.as_view(), name='rentals'),
    path('rentals/book/', BookCarRentalView.as_view(), name='book-car-rental'),
    path('rentals/<uuid:uuid>/', AvailableForRentDetailView.as_view(), name='rental-detail'),
    path('rentals/<uuid:uuid>/modify/', BookCarRentalViewDetailView.as_view(), name='rental-modify'), #for user

    # Buying task 3
    path('buy/', AvailableForBuyingView.as_view(), name='rentals'),
    path('buy/request-test-drive/', TestDriveRequestView.as_view(), name='rentals'),
    path('buy/trade-in/', TradeInRequestViewSet.as_view(), name='rentals'),

    path('complete-order/', CompleteOrderView.as_view()),

    # Selling task 4
    path('sell/', CreateVehicleView.as_view(), name='submit-car-for-sale'),
    path('sell/<uuid:uuid>/update/', VehicleDetailView.as_view(), name='vehicle-update'),
    path('sell/offers/', ViewCarOffersView.as_view(), name='view-car-offers'),
]




