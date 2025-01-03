from django.urls import path
from .views import (
    MechanicProfileView,
    MechanicListView,
    BookingUpdateView,
    MechanicSearchView,
    MechanicServiceHistory,
)


app_name = 'bookings_api'

urlpatterns = [
    path('', MechanicListView.as_view()),
    path('find/', MechanicSearchView.as_view()),
    path('<mech_id>/', MechanicProfileView.as_view()),
    path('<mech_id>/history/', MechanicServiceHistory.as_view()),
    path('bookings/<booking_id>/', BookingUpdateView.as_view()),
]


