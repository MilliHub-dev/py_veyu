from django.urls import path
from .views import (
    SignUpView,
    login_view,
    verify_user_view
)

app_name = 'accounts_api'

urlpatterns = [
    path('login/', login_view),
    path('register/', SignUpView.as_view()),
    path('verify/', verify_user_view),
]



