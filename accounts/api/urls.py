from django.urls import path
from django.contrib.auth import views as auth_views


from .views import (
    SignUpView,
    LoginView,
    MechanicListView,
     UpdateProfileView,
     VerifyEmailView,
     VerifyPhoneNumberView
)
from django.urls import include

app_name = 'accounts_api'

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('register/', SignUpView.as_view()),
    path('verify-phone-number/', VerifyPhoneNumberView.as_view()),
    path('verify-email/', VerifyEmailView.as_view()),
    path('update-profile/',  UpdateProfileView.as_view()),
    path("accounts/", include("django.contrib.auth.urls")),
    path('auth/', include('dj_rest_auth.urls')),
]

