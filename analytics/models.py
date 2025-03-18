from utils.models import DbModel
from django.db import models
from django.core.validators import MinValueValidator




from django.db import models
from django.utils.timezone import now


class ListingAnalytics(DbModel):
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='analytics')
    impressions = models.PositiveIntegerField(default=0)
    boosted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('listing', 'date_created')

    def __str__(self):
        return f"{self.listing.title} - {self.date_created}: {self.impressions} impressions"


class MechanicAnalytics(DbModel):
    mechanic = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE, related_name='analytics')
    impressions = models.PositiveIntegerField(default=0)
    boosted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('mechanic', 'date_created')

    def __str__(self):
        return f"{self.mechanic.business_name} - {self.date_created}: {self.impressions} impressions"

