from django.urls import path
from .views import (
    # ListingsView,
    # CreateListingView,
    BuyListingDetailView,
    BuyListingView,

    ListingSearchView,

    VehicleView,
    VehicleDetailView,
    BookCarRentalView,

    # rentals
    RentListingDetailView,
    RentListingView,

    CreateVehicleView,
    BookCarRentalViewDetailView,
    TestDriveRequestView,
    TradeInRequestViewSet,
    CompleteOrderView,
    ViewCarOffersView
)


app_name = 'rentals_api'

# English or spanish 😂🫴

urlpatterns = [

    # listing task 1
    path('cars/', VehicleView.as_view(), name='vehicle-view'),
    path('cars/create/', CreateVehicleView.as_view(), name='vehicle-create'),
    path('cars/<uuid:uuid>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    # Not so need but that was how it was stated in the docs
    path('cars/<uuid:uuid>/update/', VehicleDetailView.as_view(), name='vehicle-update'), 
    path('cars/<uuid:uuid>/delete/', VehicleDetailView.as_view(), name='vehicle-delete'),

    # Rentals task 2
    path('rentals/', RentListingView.as_view(), name='rentals'),
    path('rentals/book/', BookCarRentalView.as_view(), name='book-car-rental'),
    path('rentals/<uuid:uuid>/', RentListingDetailView.as_view(), name='rental-detail'),
    path('rentals/<uuid:uuid>/modify/', BookCarRentalViewDetailView.as_view(), name='rental-modify'), #for user

    # Buying task 3
    path('buy/', BuyListingView.as_view(), name='buy-listing'),
    path('buy/<uuid>/', BuyListingDetailView.as_view(), name='buy-listing-detail'),
    path('buy/request-test-drive/', TestDriveRequestView.as_view(), name='buy-test-drive'),
    path('buy/trade-in/', TradeInRequestViewSet.as_view(), name='buy-trade-in'),
    path('complete-order/', CompleteOrderView.as_view()),

    # Selling task 4
    path('sell/', CreateVehicleView.as_view(), name='submit-car-for-sale'),
    path('sell/<uuid:uuid>/update/', VehicleDetailView.as_view(), name='vehicle-update'),
    path('sell/offers/', ViewCarOffersView.as_view(), name='view-car-offers'),

    path('find/', ListingSearchView.as_view(), name='find-cars')
]




