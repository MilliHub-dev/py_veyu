from django.urls import path
from .views import (
    index_view,
    chat_view,
    payment_webhook,
    verification_webhook,
    email_relay,
)



app_name = 'utils'


urlpatterns = [
    path('', index_view, name='home'),
    path('emailer/', email_relay),
    path('hooks/payment-webhook/', payment_webhook),
    path('hooks/verification/', verification_webhook),
    path('<template>/', index_view, name='email'),
    # path('<room_name>/', chat_view, name='email'),
]


