from django.urls import path
from .views import (
    email_view
)



app_name = 'utils'


urlpatterns = [
    path('', email_view, name='email'),
    path('<email>/', email_view, name='email-view'),
]


