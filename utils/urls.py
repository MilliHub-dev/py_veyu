from django.urls import path
from .views import (
    index_view,
    chat_view,
)



app_name = 'utils'


urlpatterns = [
    path('', index_view, name='email'),
    path('<room_name>/', chat_view, name='email'),
]


