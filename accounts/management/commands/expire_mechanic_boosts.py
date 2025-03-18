from django.core.management.base import BaseCommand
from django.utils.timezone import now
from accounts.models import MechanicBoost

class Command(BaseCommand):
    help = "Automatically expire mechanic boosts when their end_date passes."

    def handle(self, *args, **kwargs):
        expired_boosts = MechanicBoost.objects.filter(end_date__lt=now().date(), active=True)
        count = expired_boosts.update(active=False)  # Bulk update for efficiency
        self.stdout.write(self.style.SUCCESS(f"Expired {count} boosted mechanics."))
