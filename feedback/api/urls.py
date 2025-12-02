from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tickets', views.SupportTicketViewSet, basename='support-ticket')

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', views.list_tags, name='list-tags'),
    path('tags/create/', views.create_tag, name='create-tag'),
    path('categories/', views.list_categories, name='list-categories'),
    path('categories/create/', views.create_category, name='create-category'),
    path('stats/', views.ticket_stats, name='ticket-stats'),
]
