from django.utils import timezone
from django.db import models
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import permissions
from .models import Ride, ScheduledRideRequest, ChatMessage
from .serializers import (
    RideCreateSerializer, RideSerializer, RideStatusSerializer, 
    ScheduledRideRequestSerializer, ChatMessageSerializer
)
from .utils import calculate_distance, calculate_fare
from vehicles.models import VehicleType, Vehicle
from .assignment import find_nearest_driver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class CurrentRideView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ride = Ride.objects.filter(
            models.Q(rider=user) | models.Q(driver=user)
        ).exclude(status__in=['CANCELLED', 'FINISHED']).order_by('-created_at').first()
        
        if ride:
            return Response(RideSerializer(ride).data)
        return Response({"detail": "No active ride"}, status=status.HTTP_404_NOT_FOUND)

class FareEstimateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            pickup_lat = float(data.get('pickup_lat'))
            pickup_lng = float(data.get('pickup_lng'))
            drop_lat = float(data.get('drop_lat'))
            drop_lng = float(data.get('drop_lng'))

            distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
            
            # Fetch vehicle type rates
            vehicle_type_id = data.get('requested_vehicle_type')
            v_type = None
            if vehicle_type_id:
                v_type = VehicleType.objects.filter(id=vehicle_type_id).first()
            
            if v_type:
                fare = calculate_fare(
                    distance_km, 
                    base_fare=v_type.base_fare, 
                    per_km_rate=v_type.per_km_rate,
                    per_minute_rate=v_type.per_minute_rate
                )
            else:
                fare = calculate_fare(distance_km) # Uses defaults

            return Response({
                "distance_km": round(distance_km, 2),
                "estimated_fare": fare
            }, status=status.HTTP_200_OK)

        except (TypeError, ValueError) as e:
            return Response({"error": "Invalid coordinates provided."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RideCreateView(generics.CreateAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideCreateSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        try:
            pickup_lat = serializer.validated_data['pickup_lat']
            pickup_lng = serializer.validated_data['pickup_lng']
            drop_lat = serializer.validated_data['drop_lat']
            drop_lng = serializer.validated_data['drop_lng']
            
            distance = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
            
            v_type = serializer.validated_data.get('requested_vehicle_type')
            if v_type:
                fare = calculate_fare(
                    distance,
                    base_fare=v_type.base_fare,
                    per_km_rate=v_type.per_km_rate,
                    per_minute_rate=v_type.per_minute_rate
                )
            else:
                fare = calculate_fare(distance)
            
            ride = serializer.save(
                rider=self.request.user,
                distance_km=distance,
                estimated_fare=fare,
                status='REQUESTED'
            )

            # Broadcast to all drivers
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'drivers_notification',
                {
                    'type': 'new_ride_request',
                    'ride': RideSerializer(ride).data
                }
            )
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # Log it in the server console
            raise serializers.ValidationError({"error": f"Internal error during creation: {str(e)}"})

class RideUpdateStatusView(generics.UpdateAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(RideSerializer(instance).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RideDetailView(generics.RetrieveAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

class DriverActionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            action = request.data.get('action') # 'ACCEPT' or 'REJECT'
            user = request.user
            
            if user.profile.role != 'DRIVER':
                 return Response({"error": "Only drivers can perform this action"}, status=status.HTTP_403_FORBIDDEN)

            if action == 'ACCEPT':
                ride.driver = user
                ride.status = 'ASSIGNED'
                
                # If there was a pending negotiation, mark it as accepted
                if ride.negotiation_status == 'PENDING':
                    ride.negotiation_status = 'ACCEPTED'
                
                ride.save()
                return Response({"status": "Ride Assigned", "ride": RideSerializer(ride).data})
            
            elif action == 'REJECT':
                ride.rejected_drivers.add(user)
                ride.save()
                
                # Reassign
                next_driver = find_nearest_driver(ride)
                msg = "Searching for next driver"
                if next_driver:
                    msg = f"Reassigning to {next_driver.username}"
                    # In a real app, we'd notify next_driver via websocket/push.
                    # Here we just acknowledge.
                else:
                    msg = "No other drivers available"
                
                return Response({"status": "Rejected", "message": msg})
            
            else:
                return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)

# --- Scheduled Rides ---

class ScheduledRideCreateView(generics.CreateAPIView):
    serializer_class = RideCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        pickup_lat = serializer.validated_data['pickup_lat']
        pickup_lng = serializer.validated_data['pickup_lng']
        drop_lat = serializer.validated_data['drop_lat']
        drop_lng = serializer.validated_data['drop_lng']
        
        distance = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
        fare = calculate_fare(distance)
        
        save_kwargs = {
            'is_scheduled': True,
            'distance_km': distance,
            'estimated_fare': fare
        }
        
        if user.profile.role == 'DRIVER':
            save_kwargs['driver'] = user
        else:
            save_kwargs['rider'] = user
            
        serializer.save(**save_kwargs)

class ScheduledRideListView(generics.ListAPIView):
    queryset = Ride.objects.filter(is_scheduled=True, scheduled_datetime__gt=timezone.now() - timezone.timedelta(hours=1))
    serializer_class = RideSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Ride.objects.filter(is_scheduled=True, scheduled_datetime__gt=timezone.now() - timezone.timedelta(hours=1), available_seats__gt=0)

class RequestSeatView(generics.CreateAPIView):
    serializer_class = ScheduledRideRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)
        # Notify driver (Optional requirement)
        ride = serializer.validated_data['ride']
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{ride.id}',
            {
                'type': 'seat_requested',
                'passenger_name': self.request.user.username,
                'seats': serializer.validated_data.get('seats_requested', 1)
            }
        )

class HandleSeatRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            seat_request = ScheduledRideRequest.objects.get(pk=pk)
            ride = seat_request.ride
            
            creator = ride.driver if ride.driver else ride.rider
            if creator != request.user:
                return Response({"error": "Only the ride creator can approve/reject requests"}, status=status.HTTP_403_FORBIDDEN)
            
            action = request.data.get('action') # 'APPROVE' or 'REJECT'
            
            if action == 'APPROVE':
                has_profile = hasattr(seat_request.passenger, 'profile')
                if not ride.driver and has_profile and seat_request.passenger.profile.role == 'DRIVER':
                    ride.driver = seat_request.passenger
                    # Driver taking the job doesn't necessarily consume a 'seat' from passengers' perspective
                    # but we mark the request approved.
                else:
                    if ride.available_seats < seat_request.seats_requested:
                        return Response({"error": "Not enough seats available"}, status=status.HTTP_400_BAD_REQUEST)
                    ride.available_seats -= seat_request.seats_requested

                seat_request.status = 'APPROVED'
                ride.save()
                seat_request.save()
                return Response({"status": "Approved"})
            
            elif action == 'REJECT':
                seat_request.status = 'REJECTED'
                seat_request.save()
                return Response({"status": "Rejected"})
            
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        except ScheduledRideRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyScheduledRequestsView(generics.ListAPIView):
    serializer_class = ScheduledRideRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        ride_id = self.request.query_params.get('ride_id')
        
        if ride_id:
            # If ride_id is provided, only show requests for that ride IF the user is the creator
            return ScheduledRideRequest.objects.filter(
                models.Q(ride__id=ride_id) & 
                (models.Q(ride__driver=user) | models.Q(ride__rider=user))
            )
            
        return ScheduledRideRequest.objects.filter(passenger=user)

class SendMessageView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class ListMessagesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        ride_id = self.request.query_params.get('ride_id')
        other_user_id = self.request.query_params.get('other_user_id')
        user = self.request.user

        qs = ChatMessage.objects.filter(ride_id=ride_id)
        
        if other_user_id:
            qs = qs.filter(
                models.Q(sender=user, receiver_id=other_user_id) |
                models.Q(sender_id=other_user_id, receiver=user)
            )
        else:
            # If other_user_id is not provided, show all messages for this ride that involve the current user
            qs = qs.filter(
                models.Q(sender=user) | models.Q(receiver=user)
            )
            
        return qs.order_by('timestamp')

class UserChatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get all messages where user is sender or receiver
        messages = ChatMessage.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related('ride', 'sender', 'receiver').order_by('-timestamp')
        
        # Group by (ride_id, other_user_id)
        chats = {}
        for msg in messages:
            other_user = msg.receiver if msg.sender == user else msg.sender
            chat_key = (msg.ride_id, other_user.id)
            if chat_key not in chats:
                chats[chat_key] = {
                    "ride_id": msg.ride_id,
                    "other_user_id": other_user.id,
                    "other_username": other_user.username,
                    "last_message": msg.content,
                    "timestamp": msg.timestamp,
                    "ride_status": msg.ride.status
                }
        
        return Response(list(chats.values()))

class AvailableRidesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RideSerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile') or user.profile.role != 'DRIVER' or not user.profile.is_online:
            return Ride.objects.none()
        
        # In a real app, filter by distance here. For Rajbari, just show all REQUESTED.
        return Ride.objects.filter(status='REQUESTED', driver__isnull=True).order_by('-id')
class RideHistoryView(generics.ListAPIView):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Ride.objects.filter(
            models.Q(rider=user) | models.Q(driver=user)
        ).order_by('-created_at')

class DriverStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'profile') or user.profile.role != 'DRIVER':
            return Response({"error": "Only drivers can access stats"}, status=status.HTTP_403_FORBIDDEN)
        
        # Total earnings from PAID rides
        total_rides = Ride.objects.filter(driver=user, status='PAID')
        total_earnings = total_rides.aggregate(models.Sum('estimated_fare'))['estimated_fare__sum'] or 0
        
        # Today's earnings
        today = timezone.now().date()
        today_earnings = total_rides.filter(created_at__date=today).aggregate(models.Sum('estimated_fare'))['estimated_fare__sum'] or 0
        
        return Response({
            "total_earnings": float(total_earnings),
            "today_earnings": float(today_earnings),
            "total_trips": total_rides.count()
        })

class MyRideRequestsView(generics.ListAPIView):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Ride.objects.filter(rider=user).order_by('-created_at')

class RideCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            if ride.rider != request.user:
                return Response({"error": "You are not authorized to cancel this ride."}, status=status.HTTP_403_FORBIDDEN)
            
            if ride.status not in ['REQUESTED', 'ASSIGNED']:
                return Response({"error": "Cannot cancel this ride."}, status=status.HTTP_400_BAD_REQUEST)
            
            ride.delete()
            
            return Response({"status": "Ride deleted successfully"})
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RideUpdateView(generics.UpdateAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideCreateSerializer # Use CreateSerializer for input validation regarding locations
    permission_classes = [IsAuthenticated]
    
    def perform_update(self, serializer):
        ride = self.get_object()
        if ride.rider != self.request.user:
            raise serializers.ValidationError("You permission to edit this ride.")
            
        if ride.status != 'REQUESTED':
             raise serializers.ValidationError("Only requested rides can be edited.")
        
        # Recalculate if locations changed
        pickup_lat = serializer.validated_data.get('pickup_lat', ride.pickup_lat)
        pickup_lng = serializer.validated_data.get('pickup_lng', ride.pickup_lng)
        drop_lat = serializer.validated_data.get('drop_lat', ride.drop_lat)
        drop_lng = serializer.validated_data.get('drop_lng', ride.drop_lng)
        
        distance = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
        
        v_type = serializer.validated_data.get('requested_vehicle_type', ride.requested_vehicle_type)
        if v_type:
            fare = calculate_fare(
                distance,
                base_fare=v_type.base_fare,
                per_km_rate=v_type.per_km_rate,
                per_minute_rate=v_type.per_minute_rate
            )
        else:
             fare = calculate_fare(distance)

        serializer.save(distance_km=distance, estimated_fare=fare)

