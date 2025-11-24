from django.urls import path
from .dealership_views import (
   CreateListingView,
   ListingsView,
   DashboardView,
   ListingDetailView,
   DealershipView,
   SettingsView,
   OrderListView,
   AnalyticsView,
   BoostPricingView,
   ListingBoostView,
   ConfirmBoostPaymentView,
   MyBoostsView,
)

app_name = "dealership_api"

urlpatterns = [
   # Admin
    path('', DealershipView.as_view(), name='dealership'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('orders/', OrderListView.as_view(), name='orders'),
    path('listings/', ListingsView.as_view(), name='listings'),
    path('listings/create/', CreateListingView.as_view(), name='create-listing'),
    path('listings/<uuid:listing_id>/', ListingDetailView.as_view(), name='listing-detail'),
    path('settings/', SettingsView.as_view(), name='transactions'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    
    # Boost endpoints
    path('boost/pricing/', BoostPricingView.as_view(), name='boost-pricing'),
    path('boost/my-boosts/', MyBoostsView.as_view(), name='my-boosts'),
    path('boost/confirm-payment/', ConfirmBoostPaymentView.as_view(), name='confirm-boost-payment'),
    path('listings/<uuid:listing_id>/boost/', ListingBoostView.as_view(), name='listing-boost'),
    
    # path('orders/<uuid:order_id>/', VehicleDetailView.as_view(), name='order-detail'),
    # path('transactions/<uuid:transaction_id>/', VehicleDetailView.as_view(), name='transaction-detail'),
]