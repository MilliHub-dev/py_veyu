from utils.models import DbModel
from django.db import models
from django.core.validators import MinValueValidator




from django.db import models
from django.utils.timezone import now


class ListingAnalytics(DbModel):
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='listing_analytics')
    impressions = models.PositiveIntegerField(default=0)
    boosted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('listing', 'date_created')
        indexes = [
            models.Index(fields=['listing']),
            models.Index(fields=['date_created']),
            models.Index(fields=['impressions']),
            models.Index(fields=['boosted']),
        ]
        ordering = ['-date_created']

    def __str__(self):
        boost_status = " (Boosted)" if self.boosted else ""
        return f"{self.listing.title} - {self.date_created.strftime('%Y-%m-%d')}: {self.impressions} impressions{boost_status}"
    
    def __repr__(self):
        return f"<ListingAnalytics: {self.listing.id} - {self.impressions} impressions>"
    
    @property
    def performance_rating(self):
        """Returns performance rating based on impressions"""
        if self.impressions >= 1000:
            return "Excellent"
        elif self.impressions >= 500:
            return "Good"
        elif self.impressions >= 100:
            return "Average"
        else:
            return "Low"


class MechanicAnalytics(DbModel):
    mechanic = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE, related_name='mechanic_analytics')
    impressions = models.PositiveIntegerField(default=0)
    boosted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('mechanic', 'date_created')
        indexes = [
            models.Index(fields=['mechanic']),
            models.Index(fields=['date_created']),
            models.Index(fields=['impressions']),
            models.Index(fields=['boosted']),
        ]
        ordering = ['-date_created']

    def __str__(self):
        boost_status = " (Boosted)" if self.boosted else ""
        return f"{self.mechanic.business_name or self.mechanic.user.name} - {self.date_created.strftime('%Y-%m-%d')}: {self.impressions} impressions{boost_status}"
    
    def __repr__(self):
        return f"<MechanicAnalytics: {self.mechanic.id} - {self.impressions} impressions>"
    
    @property
    def performance_rating(self):
        """Returns performance rating based on impressions"""
        if self.impressions >= 500:
            return "Excellent"
        elif self.impressions >= 250:
            return "Good"
        elif self.impressions >= 50:
            return "Average"
        else:
            return "Low"

