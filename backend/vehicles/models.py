from django.db import models
from users.models import Profile

class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., 'Bike', 'Car', 'SUV', 'Ambulance'
    description = models.TextField(null=True, blank=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2, default=2.00)
    image = models.ImageField(upload_to='vehicle_types/', null=True, blank=True)
    
    def __str__(self):
        return self.name

class Vehicle(models.Model):
    driver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, related_name='vehicles')
    
    make = models.CharField(max_length=50) # e.g., 'Toyota'
    model = models.CharField(max_length=50) # e.g., 'Premio'
    year = models.PositiveIntegerField()
    plate_number = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=20)
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    registration_document = models.FileField(upload_to='vehicle_docs/', null=True, blank=True)
    insurance_document = models.FileField(upload_to='vehicle_docs/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.color} {self.make} {self.model} ({self.plate_number})"
