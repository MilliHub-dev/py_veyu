from django.db import models
from utils import make_UUID
from django.utils import timezone



class DbModel(models.Model):
    uuid = models.UUIDField(default=make_UUID, blank=True)
    date_created = models.DateTimeField(auto_now_add=False, auto_now=True, auto_created=True)
    last_updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True




