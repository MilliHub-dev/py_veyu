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
    # path('orders/<uuid:order_id>/', VehicleDetailView.as_view(), name='order-detail'),
    # path('transactions/<uuid:transaction_id>/', VehicleDetailView.as_view(), name='transaction-detail'),
]