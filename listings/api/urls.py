from django.urls import path
from .views import (
    CheckoutView,
    MyListingsView,
    BuyListingView,
    RentListingView,
    ListingSearchView,
    BuyListingDetailView,
    RentListingDetailView,
    DealershipView,
    BookInspectionView,
    CheckoutDocumentView,
)


app_name = 'rentals_api'

# English or spanish 😂🫴

urlpatterns = [
    # retrieve recently viewed listings and favorites
    path('buy/', BuyListingView.as_view(), name='buy-listing'),
    path('find/', ListingSearchView.as_view(), name='find-cars'),
    path('rentals/', RentListingView.as_view(), name='rentals'),
    path('dealer/<uuid>/', DealershipView.as_view(), name='dealer'),
    path('dealer/<slug>/', DealershipView.as_view(), name='dealer'),
    path('my-listings/', MyListingsView.as_view()),
    path('buy/<uuid>/', BuyListingDetailView.as_view(), name='buy-listing-detail'),
    path('rentals/<uuid>/', RentListingDetailView.as_view(), name='rental-detail'),
    path('checkout/documents/', CheckoutDocumentView.as_view()),
    path('checkout/inspection/', BookInspectionView.as_view(), name='checkout-inspection'),
    path('checkout/<uuid:listingId>/', CheckoutView.as_view(), name='checkout'),
    # path('rentals/<uuid:uuid>/modify/', BookCarRentalViewDetailView.as_view(), name='rental-modify'), #for user
    # path('checkout/pay/', CompleteOrderView.as_view()), # use to generate payment link
]




