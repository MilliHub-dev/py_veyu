"""
URL patterns for the log viewer system.
Provides endpoints for viewing, downloading, and refreshing log files.
"""

from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    # Main log list view - displays available log files
    path('', views.LogListView.as_view(), name='log_list'),
    
    # Log detail view - displays content of a specific log file
    path('<str:log_file>/', views.LogDetailView.as_view(), name='log_detail'),
    
    # Log download view - serves log files for download
    path('<str:log_file>/download/', views.LogDownloadView.as_view(), name='log_download'),
    
    # API endpoint for real-time log refresh
    path('api/refresh/<str:log_file>/', views.LogRefreshAPIView.as_view(), name='log_refresh_api'),
]