from django.db import models
from django.core.validators import MinValueValidator

class AnalyticsData(models.Model):
    date = models.DateField()
    customers = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    dealers = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    mechanics = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    orders = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    revenue = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['date']
        verbose_name = 'Analytics Data'
        verbose_name_plural = 'Analytics Data'

    def __str__(self):
        return f"Analytics for {self.date}"

    def clean(self):
        # Ensure date is a proper date object
        if isinstance(self.date, str):
            try:
                self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError({'date': 'Invalid date format'})