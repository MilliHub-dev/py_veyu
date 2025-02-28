from django.urls import path
from .dealership_views import (
    # Admin Views
    CreateListingView,
    ListingsView,
    DashboardView,
    ListingsView,
    DealershipView,

)

app_name = "dealership_api"

urlpatterns = [
   # Admin
    path('', DealershipView.as_view(), name='dealership'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('orders/', VehicleDetailView.as_view(), name='orders'),
    path('listings/', ListingsView.as_view(), name='listings'),
    # path('transactions/', VehicleDetailView.as_view(), name='transactions'),
    path('listings/create/', CreateListingView.as_view(), name='create-listing'),
    # path('orders/<uuid:order_id>/', VehicleDetailView.as_view(), name='order-detail'),
    # path('listings/<uuid:listing_id>/', VehicleDetailView.as_view(), name='listing-detail'),
    # path('transactions/<uuid:transaction_id>/', VehicleDetailView.as_view(), name='transaction-detail'),
]