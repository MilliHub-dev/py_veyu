from django.urls import path
from .views import (
    SignUpView,
    LoginView,
    verify_user_view,
    MechanicListView,
)

app_name = 'accounts_api'

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('register/', SignUpView.as_view()),
    path('verify/', verify_user_view),
    path('mechanics/', MechanicListView.as_view()),
]



