import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rides.models import Ride

class RideConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.room_group_name = f'ride_{self.ride_id}'
        self.user = self.scope['user']

        # Verify User
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check permissions (Rider or Driver of this ride)
        is_authorized = await self.is_authorized_for_ride(self.ride_id, self.user)
        if not is_authorized:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive_json(self, content):
        message_type = content.get('type')
        
        if message_type == 'location_update':
            # Check if ride is ONGOING or ASSIGNED
            if not await self.is_ride_ongoing(self.ride_id):
                 return

            lat = content.get('lat')
            lng = content.get('lng')
            
            if lat is None or lng is None:
                return

            # Import helpers
            from rides.utils import is_within_bangladesh, calculate_distance
            import time

            # 1. Boundary Check
            if not is_within_bangladesh(lat, lng):
                await self.send_json({"error": "Location outside service area"})
                return

            # 2. Spoofing Detection (Speed Check)
            now = time.time()
            if hasattr(self, 'last_update'):
                last_lat = self.last_update['lat']
                last_lng = self.last_update['lng']
                last_time = self.last_update['time']
                
                dist = calculate_distance(last_lat, last_lng, lat, lng)
                time_diff = now - last_time # in seconds
                
                if time_diff > 0:
                    speed_kmh = (dist / time_diff) * 3600
                    # threshold 150 km/h for urban ride
                    if speed_kmh > 150:
                        await self.send_json({"error": "GPS Spoofing detected or invalid signal"})
                        return

            self.last_update = {'lat': lat, 'lng': lng, 'time': now}
            
            # Update User Profile (Persistence)
            await self.update_user_location(self.user, lat, lng)

            # Send message to room group including role and sender_id
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ride_location_update',
                    'lat': lat,
                    'lng': lng,
                    'user_id': self.user.id,
                    'role': self.user.profile.role
                }
            )

    # Receive message from room group
    async def ride_location_update(self, event):
        # Send message to WebSocket
        await self.send_json({
            'type': 'location_update',
            'lat': event['lat'],
            'lng': event['lng'],
            'user_id': event['user_id'],
            'role': event['role']
        })

    async def ride_status_update(self, event):
        await self.send_json({
            'type': 'status_update',
            'status': event['status'],
            'ride_id': event.get('ride_id'),
            'amount_paid': event.get('amount_paid'),
            'driver_name': event.get('driver_name'),
            'rider_id': event.get('rider_id'),
            'rider_username': event.get('rider_username')
        })

    @database_sync_to_async
    def is_authorized_for_ride(self, ride_id, user):
        try:
            ride = Ride.objects.get(pk=ride_id)
            return ride.rider == user or ride.driver == user
        except Ride.DoesNotExist:
            return False

    @database_sync_to_async
    def is_driver(self, user):
        return hasattr(user, 'profile') and user.profile.role == 'DRIVER'

    @database_sync_to_async
    def update_user_location(self, user, lat, lng):
            user.profile.current_lat = lat
            user.profile.current_lng = lng
            user.profile.save()

    @database_sync_to_async
    def is_ride_ongoing(self, ride_id):
        try:
            ride = Ride.objects.get(pk=ride_id)
            return ride.status in ['ASSIGNED', 'ONGOING']
        except Ride.DoesNotExist:
            return False

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated or not await self.is_driver(self.user):
            await self.close()
            return

        self.group_name = 'drivers_notification'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def new_ride_request(self, event):
        await self.send_json({
            'type': 'new_ride_request',
            'ride': event['ride']
        })

    @database_sync_to_async
    def is_driver(self, user):
        return hasattr(user, 'profile') and user.profile.role == 'DRIVER'
