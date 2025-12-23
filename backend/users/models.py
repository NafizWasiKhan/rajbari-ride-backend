from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = (
        ('RIDER', 'Rider'),
        ('DRIVER', 'Driver'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='RIDER')
    is_online = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    
    # Verification System
    is_verified = models.BooleanField(default=False)
    VERIFICATION_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    
    # Common Addresses
    home_address = models.TextField(null=True, blank=True)
    work_address = models.TextField(null=True, blank=True)

    # Driver Specific Information (Legacy - to be moved to Vehicle model)
    car_model = models.CharField(max_length=50, null=True, blank=True)
    car_color = models.CharField(max_length=20, null=True, blank=True)
    plate_number = models.CharField(max_length=20, null=True, blank=True)
    
    # Rating & Stats
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    trips_completed = models.PositiveIntegerField(default=0)
    
    current_lat = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)

    def __str__(self):
        status = "✅" if self.is_verified else "❌"
        return f"{status} {self.user.username} ({self.role})"

class DriverDocument(models.Model):
    DOCUMENT_TYPES = (
        ('NID', 'National ID'),
        ('LICENSE', 'Driving License'),
        ('TIN', 'Tax Certificate'),
        ('UTILITY', 'Utility Bill (Address Proof)'),
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50)
    file_path = models.FileField(upload_to='driver_docs/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_type} for {self.profile.user.username}"

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

