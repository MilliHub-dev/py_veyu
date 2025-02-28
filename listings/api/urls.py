from django.urls import path
from .views import (
    CheckoutView,
    MyListingsView,
    BuyListingView,
    RentListingView,
    BookCarRentalView,
    ListingSearchView,
    BuyListingDetailView,
    RentListingDetailView,
)


app_name = 'rentals_api'

# English or spanish 😂🫴

urlpatterns = [
    # retrieve recently viewed listings and favorites
    path('buy/', BuyListingView.as_view(), name='buy-listing'),
    path('find/', ListingSearchView.as_view(), name='find-cars'),
    path('rentals/', RentListingView.as_view(), name='rentals'),
    path('my-listings/', MyListingsView.as_view()),
    path('buy/<uuid>/', BuyListingDetailView.as_view(), name='buy-listing-detail'),
    path('rentals/<uuid>/', RentListingDetailView.as_view(), name='rental-detail'),
    # path('checkout/complete-order/', CompleteOrderView.as_view()),
    path('checkout/<uuid:listingId>/', CheckoutView.as_view(), name='checkout'),
    # path('rentals/<uuid:uuid>/modify/', BookCarRentalViewDetailView.as_view(), name='rental-modify'), #for user
    # path('checkout/pay/', CompleteOrderView.as_view()), # use to generate payment link
]




