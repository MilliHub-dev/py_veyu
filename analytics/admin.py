# analytics/admin.py
from django.contrib import admin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .models import AnalyticsData
import json

@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'customers', 'dealers', 'mechanics', 'orders', 'revenue')
    list_filter = ['date']
    
    def changelist_view(self, request, extra_context=None):
        # Get aggregated metrics
        metrics = {
            'total_customers': AnalyticsData.objects.aggregate(total=Sum('customers'))['total'] or 0,
            'total_dealers': AnalyticsData.objects.aggregate(total=Sum('dealers'))['total'] or 0,
            'total_orders': AnalyticsData.objects.aggregate(total=Sum('orders'))['total'] or 0,
            'total_revenue': AnalyticsData.objects.aggregate(total=Sum('revenue'))['total'] or 0,
        }
        
        # Get monthly data for charts
        monthly_data = AnalyticsData.objects.order_by('date')
        
        # Format data for charts
        chart_data = {
            'labels': [date.strftime('%Y-%m-%d') for date in monthly_data.values_list('date', flat=True)],
            'customers': list(monthly_data.values_list('customers', flat=True)),
            'dealers': list(monthly_data.values_list('dealers', flat=True)),
            'mechanics': list(monthly_data.values_list('mechanics', flat=True)),
            'orders': list(monthly_data.values_list('orders', flat=True)),
            'revenue': [float(rev) for rev in monthly_data.values_list('revenue', flat=True)],
        }
        
        # Create extra context
        context = {
            'metrics': metrics,
            'monthly_data': chart_data,
        }
        
        # Update extra context
        extra_context = extra_context or {}
        extra_context.update(context)
        
        return super().changelist_view(request, extra_context=extra_context)
    
    change_list_template = 'admin/analytics/analytics_change_list.html'