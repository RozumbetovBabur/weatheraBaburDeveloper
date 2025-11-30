# weatherapp/models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
class User(AbstractUser):
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='weatherapp_users',  # ⚡ related_name maslaw
        blank=True,
        help_text='The groups this user belongs to.'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='weatherapp_user_permissions',  # ⚡ related_name maslaw
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return self.username

class WeatherCache(models.Model):
    """
    Hár bir qala ushın sońǵı OpenWeather juwabı saqlanadı.
    city_key: unik identifikator  (mısalı " Tashkent" yamasa " Tashkent, uz")
    data: raw json nátiyje
    created_at: qashan júklengen
    """
    city_key = models.CharField(max_length=200, db_index=True)
    data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['city_key']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.city_key} @ {self.created_at.isoformat()}"
