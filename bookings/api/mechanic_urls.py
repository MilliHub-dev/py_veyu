from django.urls import path
from .mechanic_views import (
    MechanicProfileView,
    MechanicOverview,
    BookingUpdateView,
    MechanicSearchView,
    BookingsView,
    MechanicSettingsView,
    MechanicDashboardView,
)


app_name = 'mechanics_api'

urlpatterns = [
    path('', MechanicOverview.as_view()),
    path('dashboard/', MechanicDashboardView.as_view()),
    path('bookings/', BookingsView.as_view()),
    path('settings/', MechanicSettingsView.as_view()),
    path('bookings/<booking_id>/', BookingUpdateView.as_view()),


    path('find/', MechanicSearchView.as_view()),
    path('<mech_id>/', MechanicProfileView.as_view()),
]


