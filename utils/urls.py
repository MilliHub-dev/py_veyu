from django.urls import path
from .views import (
    index_view,
    chat_view,
    payment_webhook,
    verification_webhook,
    email_relay,
    email_health_check,
    email_config_validation,
    email_connection_test,
    email_test_send,
    process_email_queue_endpoint,
    database_health_check,
    database_info,
    system_health_check,
)
from .version_check import version_check



app_name = 'utils'


urlpatterns = [
    # Version check endpoint
    path('version/', version_check, name='version_check'),
    
    # path('', index_view, name='home'),
    path('emailer/', email_relay),
    path('hooks/payment-webhook/', payment_webhook),
    path('hooks/verification/', verification_webhook),
    
    # Email health check and diagnostic endpoints
    path('email/health/', email_health_check, name='email_health_check'),
    path('email/config/validate/', email_config_validation, name='email_config_validation'),
    path('email/connection/test/', email_connection_test, name='email_connection_test'),
    path('email/test/send/', email_test_send, name='email_test_send'),
    path('email/queue/process/', process_email_queue_endpoint, name='process_email_queue'),
    
    # Database health check and diagnostic endpoints
    path('database/health/', database_health_check, name='database_health_check'),
    path('database/info/', database_info, name='database_info'),
    path('system/health/', system_health_check, name='system_health_check'),
    
    path('<template>/', index_view, name='email'),
    # path('<room_name>/', chat_view, name='email'),
]


