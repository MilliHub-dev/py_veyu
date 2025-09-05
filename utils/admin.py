from django.contrib.admin import AdminSite
from django.contrib.admin.sites import DefaultAdminSite
from django.utils.timezone import now, timedelta
from django.db.models import Count, Sum
from django.shortcuts import render
from accounts.models import (Customer, Dealer, Mechanic,)
from listings.models import Order
from django.urls import path, re_path
from django.template.response import TemplateResponse
from django.apps import apps
from django.http import Http404


class VeyuAdminSite(AdminSite):
    site_header = "My Custom Admin"
    site_title = "Analytics Dashboard"
    index_title = "Dashboard"
    name = 'veyu_admin'

    
    # def get_urls(self):
    #     custom_urls = [
    #         re_path(r'^(?P<app_label>\w+)/$', self.admin_view(self.app_index), name='app_list'),
    #     ]
    #     return custom_urls + super().get_urls()

    def index(self, request, extra_context=None):
        # Get the date 30 days ago
        thirty_days_ago = now() - timedelta(days=30)
        
        # Get aggregated metrics for the last 30 days
        metrics = {
            'total_customers': Customer.objects.count(),
            'total_dealers': Dealer.objects.count(),
            'total_orders': Order.objects.count(),
            # 'total_revenue': AnalyticsData.objects.aggregate(total=Sum('revenue'))['total'] or 0,
        }
        
        # Query the counts for each model (Customer, Dealer, Mechanic, Order) per day in the last 30 days
        customers_per_day = Customer.objects.filter(date_created__gte=thirty_days_ago).values('date_created__date').annotate(count=Count('id')).order_by('date_created__date')
        dealers_per_day = Dealer.objects.filter(date_created__gte=thirty_days_ago).values('date_created__date').annotate(count=Count('id')).order_by('date_created__date')
        mechanics_per_day = Mechanic.objects.filter(date_created__gte=thirty_days_ago).values('date_created__date').annotate(count=Count('id')).order_by('date_created__date')
        orders_per_day = Order.objects.filter(date_created__gte=thirty_days_ago).values('date_created__date').annotate(count=Count('id')).order_by('date_created__date')
        
        # Prepare the labels (dates) for the chart
        dates = sorted(set([item['date_created__date'] for item in customers_per_day] +
                           [item['date_created__date'] for item in dealers_per_day] +
                           [item['date_created__date'] for item in mechanics_per_day] +
                           [item['date_created__date'] for item in orders_per_day]))
        
        # Prepare the data for each model (Customer, Dealer, Mechanic, Order)
        def get_daily_counts(queryset, dates):
            return [next((item['count'] for item in queryset if item['date_created__date'] == date), 0) for date in dates]
        
        customer_counts = get_daily_counts(customers_per_day, dates)
        dealer_counts = get_daily_counts(dealers_per_day, dates)
        mechanic_counts = get_daily_counts(mechanics_per_day, dates)
        order_counts = get_daily_counts(orders_per_day, dates)
        
        # Prepare chart data (daily increases)
        chart_data = {
            'labels': [date.strftime('%Y-%m-%d') for date in dates],
            'customer_increase': customer_counts,
            'dealer_increase': dealer_counts,
            'mechanic_increase': mechanic_counts,
            'order_increase': order_counts
        }

        # Update extra context with analytics data
        extra_context = extra_context or {}
        extra_context.update({
            'metrics': metrics,
            'monthly_data': chart_data,
        })

        if request.method == 'POST':
            print("Making Changes...")

        return super().index(request, extra_context=extra_context)

    def app_index(self, request, app_label, extra_context={}):
        # return super().app_index(request, app_label, extra_context)
        app_config = apps.get_app_config(app_label)
        if not app_config:
            raise Http404("App not found")

        context = {
            **self.each_context(request),
            "title": app_config.verbose_name,
            "app_label": app_label,
            "app_list": [app for app in self.get_app_list(request) if app['app_label'] == app_label],
        }
        print("App List:", context['app_list'])
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/app_index.html", context)

# Create an instance of the custom admin site
# motaa_admin = MotaaAdminSite(name='motaa_admin')
veyu_admin = VeyuAdminSite()
