from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from analytics.models import AnalyticsData
import random

class Command(BaseCommand):
    help = 'Populate test analytics data with configurable parameters (max 100 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=50,
            help='Number of days to generate data for (max 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )
        parser.add_argument(
            '--min-revenue',
            type=float,
            default=1000,
            help='Minimum revenue amount'
        )
        parser.add_argument(
            '--max-revenue',
            type=float,
            default=5000,
            help='Maximum revenue amount'
        )

    def generate_random_data(self, min_revenue, max_revenue):
        """Generate random values for a single day's analytics data."""
        return {
            'customers': random.randint(100, 200),
            'dealers': random.randint(20, 50),
            'mechanics': random.randint(30, 80),
            'orders': random.randint(50, 150),
            'revenue': Decimal(str(round(random.uniform(min_revenue, max_revenue), 2)))
        }

    def handle(self, *args, **options):
        try:
            # Validate and limit the number of days
            days = min(options['days'], 100)
            if options['days'] > 100:
                self.stdout.write(
                    self.style.WARNING('Days limited to maximum of 100')
                )

            # Clear existing data if requested
            if options['clear']:
                AnalyticsData.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Cleared existing data'))

            # Calculate date range
            start_date = timezone.now().date() - timedelta(days=days-1)
            
            # Create all objects at once since we're limited to 100
            analytics_objects = [
                AnalyticsData(
                    date=start_date + timedelta(days=i),
                    **self.generate_random_data(
                        options['min_revenue'],
                        options['max_revenue']
                    )
                )
                for i in range(days)
            ]
            
            # Bulk create all objects
            AnalyticsData.objects.bulk_create(analytics_objects)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully populated {days} days of test data'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating data: {str(e)}')
            )