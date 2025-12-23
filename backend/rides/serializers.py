from rest_framework import serializers
from .models import Ride, ScheduledRideRequest, ChatMessage
from .utils import calculate_distance, calculate_fare

class RideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = [
            'id', 'pickup_lat', 'pickup_lng', 'drop_lat', 'drop_lng', 
            'pickup_address', 'drop_address', 'status', 'distance_km', 
            'estimated_fare', 'proposed_fare', 'negotiation_status', 'rider', 'requested_vehicle_type',
            'is_scheduled', 'scheduled_datetime', 'available_seats'
        ]
        read_only_fields = ['id', 'status', 'distance_km', 'estimated_fare', 'rider', 'negotiation_status']

    def validate(self, data):
        pickup_lat = data['pickup_lat']
        pickup_lng = data['pickup_lng']
        drop_lat = data['drop_lat']
        drop_lng = data['drop_lng']
        is_scheduled = data.get('is_scheduled', False)
        scheduled_datetime = data.get('scheduled_datetime')
        
        from .utils import is_valid_coordinate, is_within_bangladesh
        from django.utils import timezone
        
        for lat, lng, label in [(pickup_lat, pickup_lng, "Pickup"), (drop_lat, drop_lng, "Drop")]:
            if not is_valid_coordinate(lat, lng):
                raise serializers.ValidationError(f"Invalid {label} coordinates.")
            if not is_within_bangladesh(lat, lng):
                raise serializers.ValidationError(f"{label} location must be within Bangladesh.")
        
        if is_scheduled:
            if not scheduled_datetime:
                raise serializers.ValidationError("Scheduled datetime is required for scheduled rides.")
            if scheduled_datetime < timezone.now():
                raise serializers.ValidationError("Scheduled datetime must be in the future.")
            if data.get('available_seats', 1) < 1:
                raise serializers.ValidationError("Available seats must be at least 1.")

        # Rounding for database precision
        data['pickup_lat'] = round(pickup_lat, 14)
        data['pickup_lng'] = round(pickup_lng, 14)
        data['drop_lat'] = round(drop_lat, 14)
        data['drop_lng'] = round(drop_lng, 14)

        return data


class RideSerializer(serializers.ModelSerializer):
    rider_username = serializers.CharField(source='rider.username', read_only=True, allow_null=True)
    driver_username = serializers.CharField(source='driver.username', read_only=True, allow_null=True)
    
    # Driver details for UI
    driver_name = serializers.CharField(source='driver.username', read_only=True, allow_null=True)
    driver_car_model = serializers.CharField(source='driver.profile.car_model', read_only=True, allow_null=True)
    driver_car_color = serializers.CharField(source='driver.profile.car_color', read_only=True, allow_null=True)
    driver_plate_number = serializers.CharField(source='driver.profile.plate_number', read_only=True, allow_null=True)
    driver_rating = serializers.DecimalField(source='driver.profile.rating', max_digits=3, decimal_places=2, read_only=True, allow_null=True)

    ride_type = serializers.SerializerMethodField()
    user_request_status = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            'id', 'rider', 'rider_username', 'driver', 'driver_username',
            'driver_name', 'driver_car_model', 'driver_car_color', 'driver_plate_number', 'driver_rating',
            'pickup_lat', 'pickup_lng', 'pickup_address', 
            'drop_lat', 'drop_lng', 'drop_address',
            'distance_km', 'estimated_fare', 'proposed_fare', 'negotiation_status', 'status', 'created_at',
            'requested_vehicle_type', 'actual_vehicle',
            'start_time', 'end_time', 'cancellation_time', 'cancellation_reason',
            'is_scheduled', 'scheduled_datetime', 'available_seats',
            'ride_type', 'user_request_status', 'creator_phone'
        ]

    def get_ride_type(self, obj):
        if obj.driver:
            return 'OFFER'
        return 'REQUEST'

    def get_user_request_status(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        req = ScheduledRideRequest.objects.filter(ride=obj, passenger=request.user).first()
        return req.status if req else None

    creator_phone = serializers.SerializerMethodField()

    def get_creator_phone(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Only show phone if they have an APPROVED request
        has_approved = ScheduledRideRequest.objects.filter(ride=obj, passenger=request.user, status='APPROVED').exists()
        if not has_approved:
            return None
            
        creator = obj.driver if obj.driver else obj.rider
        return creator.profile.phone_number if creator and hasattr(creator, 'profile') else None

class ScheduledRideRequestSerializer(serializers.ModelSerializer):
    passenger_username = serializers.CharField(source='passenger.username', read_only=True)
    passenger_phone = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledRideRequest
        fields = ['id', 'ride', 'passenger', 'passenger_username', 'passenger_phone', 'seats_requested', 'status', 'created_at']
        read_only_fields = ['id', 'passenger', 'status', 'created_at']

    def get_passenger_phone(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Only show phone to the ride creator
        creator = obj.ride.driver if obj.ride.driver else obj.ride.rider
        if request.user == creator:
            return obj.passenger.profile.phone_number
        return None

    def validate(self, data):
        ride = data['ride']
        seats_requested = data.get('seats_requested', 1)

        if not ride.is_scheduled:
            raise serializers.ValidationError("This ride is not available for scheduling.")
        
        if seats_requested > ride.available_seats:
            raise serializers.ValidationError(f"Only {ride.available_seats} seats available.")
        
        if ScheduledRideRequest.objects.filter(ride=ride, passenger=self.context['request'].user).exists():
            raise serializers.ValidationError("You have already requested a seat in this ride.")

        return data

class RideStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ['status', 'driver']
        extra_kwargs = {'driver': {'required': False}}

    def validate(self, data):
        return data

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'ride', 'sender', 'sender_username', 'receiver', 'content', 'timestamp']
        read_only_fields = ['id', 'sender', 'timestamp']
