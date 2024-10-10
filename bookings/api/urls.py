from django.urls import path
from .views import (
    MechanicBookingView,
    MechanicListView,
    BookingUpdateView,
    MechanicServiceHistory,
)


app_name = 'bookings_api'

urlpatterns = [
    path('mechanics/', MechanicListView.as_view()),
    path('mechanics/<mech_id>/', MechanicBookingView.as_view()),
    path('mechanics/<mech_id>/history/', MechanicServiceHistory.as_view()),
    path('<booking_id>/', BookingUpdateView.as_view()),
]


