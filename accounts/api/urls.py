from django.urls import path
from .views import (
    SignUpView,
    LoginView,
    VerificationView,
)

app_name = 'accounts_api'

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('register/', SignUpView.as_view()),
    path('verify/', VerificationView.as_view()),
]



