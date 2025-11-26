from django.db import models

# Create your models here.
from django.db import models

class PhoneixSpatialData(models.Model):
    longitude = models.FloatField()
    latitude = models.FloatField()
    vhi = models.FloatField()
    lst_temp = models.FloatField()
    lst_category = models.CharField(max_length=50)
    drought = models.CharField(max_length=50)
    flood_risk_level = models.IntegerField(choices=[(i, f'Level {i}') for i in range(1, 6)])
    user_intent = models.CharField(max_length=200, default='build house')
    ai_recommendation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    userId = models.CharField(max_length=100, default='anonymous', unique=False, null=False, blank=False)

    def __str__(self):
        return f"Risk {self.flood_risk_level} at ({self.longitude}, {self.latitude})"
    
class PhoneixUserData(models.Model):
    username = models.CharField(max_length=100, null=True, blank=True)
    userId = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.username} ({self.first_name} {self.last_name})"