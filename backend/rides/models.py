from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Ride(models.Model):
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('ASSIGNED', 'Assigned'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('PAID', 'Paid'),
        ('FINISHED', 'Finished'),
    ]

    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_rider', null=True, blank=True)
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides_as_driver')
    rejected_drivers = models.ManyToManyField(User, related_name='rejected_rides', blank=True)
    
    pickup_lat = models.DecimalField(max_digits=22, decimal_places=16)
    pickup_lng = models.DecimalField(max_digits=22, decimal_places=16)
    pickup_address = models.TextField(null=True, blank=True)
    
    drop_lat = models.DecimalField(max_digits=22, decimal_places=16)
    drop_lng = models.DecimalField(max_digits=22, decimal_places=16)
    drop_address = models.TextField(null=True, blank=True)
    
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_fare = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Fare negotiation fields
    proposed_fare = models.IntegerField(null=True, blank=True, help_text="Passenger's proposed fare in BDT")
    negotiation_status = models.CharField(
        max_length=20,
        choices=[
            ('NONE', 'No Negotiation'),
            ('PENDING', 'Pending Driver Response'),
            ('ACCEPTED', 'Driver Accepted'),
            ('REJECTED', 'Driver Rejected')
        ],
        default='NONE'
    )
    
    is_scheduled = models.BooleanField(default=False)
    scheduled_datetime = models.DateTimeField(null=True, blank=True)
    available_seats = models.PositiveIntegerField(default=1)
    
    # Vehicle Related
    requested_vehicle_type = models.ForeignKey('vehicles.VehicleType', on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_rides')
    actual_vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_rides')
    
    # Timing & Cancellation
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_rides')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ride #{self.id} - {self.status}"

    def clean(self):
        from django.utils import timezone
        if self.is_scheduled:
            if not self.scheduled_datetime:
                raise ValidationError("Scheduled datetime is required for scheduled rides.")
            
            # Only validate future time on creation
            if not self.pk and self.scheduled_datetime < timezone.now():
                raise ValidationError("Scheduled datetime must be in the future.")
            
            # Allow 0 seats (fully booked), but not negative
            if self.available_seats < 0:
                raise ValidationError("Available seats cannot be negative.")

        # Strict state transition validation
        if self.pk:
            old_instance = Ride.objects.get(pk=self.pk)
            old_status = old_instance.status
            new_status = self.status

            if old_status in ['COMPLETED', 'PAID']:
                # Prevent modification of critical fields
                if (
                    self.pickup_lat != old_instance.pickup_lat or
                    self.pickup_lng != old_instance.pickup_lng or
                    self.drop_lat != old_instance.drop_lat or
                    self.drop_lng != old_instance.drop_lng or
                    self.estimated_fare != old_instance.estimated_fare or
                    self.distance_km != old_instance.distance_km
                ):
                     raise ValidationError("Cannot modify ride details after completion")

            if old_status == new_status:
                return

            strict_transitions = {
                'REQUESTED': ['ASSIGNED', 'CANCELLED'],
                'ASSIGNED': ['ONGOING', 'COMPLETED', 'CANCELLED'],
                'ONGOING': ['COMPLETED', 'CANCELLED'],
                'COMPLETED': ['PAID', 'FINISHED'], # Allow direct transition for cash payments
                'CANCELLED': [],
                'PAID': ['FINISHED'],
                'FINISHED': []
            }

            if new_status != old_status and new_status not in strict_transitions.get(old_status, []):
                 raise ValidationError(f"Invalid state transition from {old_status} to {new_status}")
                 
            if new_status == 'ASSIGNED' and not self.driver:
                raise ValidationError("Cannot move to ASSIGNED without a driver.")

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = Ride.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)
        
        # Notify about status change
        if is_new or old_status != self.status:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'ride_{self.id}',
                {
                    'type': 'ride_status_update',
                    'status': self.status,
                    'ride_id': self.id,
                    'amount_paid': str(self.estimated_fare) if self.estimated_fare else None, # Assuming estimated_fare is the amount paid for broadcast
                    'driver_name': self.driver.username if self.driver else None,
                    'rider_id': self.rider.id if self.rider else None,
                    'rider_username': self.rider.username if self.rider else None,
                }
            )

class ScheduledRideRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='scheduled_requests')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_requests')
    seats_requested = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ride', 'passenger')

    def __str__(self):
        return f"Request by {self.passenger.username} for Ride #{self.ride.id} - {self.status}"

class ChatMessage(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} on Ride {self.ride.id}"

class RideReview(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='review')
    
    # Rider rating the Driver
    rider_rating = models.PositiveSmallIntegerField(null=True, blank=True) # 1-5
    rider_comment = models.TextField(null=True, blank=True)
    
    # Driver rating the Rider
    driver_rating = models.PositiveSmallIntegerField(null=True, blank=True) # 1-5
    driver_comment = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Ride #{self.ride.id}"
