from django.core.management.base import BaseCommand
from django.utils.timezone import now
from listings.models import ListingBoost

class Command(BaseCommand):
    help = "Automatically expire boosted listings when their end_date passes."

    def handle(self, *args, **kwargs):
        expired_boosts = ListingBoost.objects.filter(end_date__lt=now().date(), active=True)
        count = expired_boosts.update(active=False)  # Bulk update for efficiency
        self.stdout.write(self.style.SUCCESS(f"Expired {count} boosted listings."))

    # TODO: notify dealer logic 

