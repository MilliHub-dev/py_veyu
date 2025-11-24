from django.core.management.base import BaseCommand
from listings.models import BoostPricing


class Command(BaseCommand):
    help = 'Initialize boost pricing with default values'

    def handle(self, *args, **options):
        pricing_data = [
            {'duration_type': 'daily', 'price': 1000.00},
            {'duration_type': 'weekly', 'price': 5000.00},
            {'duration_type': 'monthly', 'price': 15000.00},
        ]

        created_count = 0
        updated_count = 0

        for data in pricing_data:
            pricing, created = BoostPricing.objects.get_or_create(
                duration_type=data['duration_type'],
                defaults={'price': data['price'], 'is_active': True}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {pricing.get_duration_type_display()} pricing: ₦{pricing.price:,.2f}'
                    )
                )
            else:
                # Update price if it exists
                if pricing.price != data['price']:
                    pricing.price = data['price']
                    pricing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'↻ Updated {pricing.get_duration_type_display()} pricing: ₦{pricing.price:,.2f}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {pricing.get_duration_type_display()} pricing already exists: ₦{pricing.price:,.2f}'
                        )
                    )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Boost pricing initialization complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Admins can now modify these prices in the Django admin panel.'
            )
        )
