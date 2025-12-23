from django.contrib import admin
from .models import Ride, RideReview, ChatMessage

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'driver', 'status', 'requested_vehicle_type', 'estimated_fare', 'created_at')
    list_filter = ('status', 'requested_vehicle_type', 'created_at')
    search_fields = ('rider__username', 'driver__username', 'pickup_address', 'drop_address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'start_time', 'end_time', 'cancellation_time')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('rider', 'driver', 'status')
        }),
        ('Location Info', {
            'fields': ('pickup_lat', 'pickup_lng', 'pickup_address', 'drop_lat', 'drop_lng', 'drop_address')
        }),
        ('Vehicle Info', {
            'fields': ('requested_vehicle_type', 'actual_vehicle')
        }),
        ('Financials', {
            'fields': ('distance_km', 'estimated_fare')
        }),
        ('Timing & Cancellation', {
            'fields': ('start_time', 'end_time', 'cancellation_time', 'cancellation_reason', 'cancelled_by')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['COMPLETED', 'PAID']:
            return self.readonly_fields + ('pickup_lat', 'pickup_lng', 'drop_lat', 'drop_lng', 'distance_km', 'estimated_fare', 'requested_vehicle_type', 'actual_vehicle')
        return self.readonly_fields

@admin.register(RideReview)
class RideReviewAdmin(admin.ModelAdmin):
    list_display = ('ride', 'rider_rating', 'driver_rating', 'created_at')
    list_filter = ('rider_rating', 'driver_rating')
    search_fields = ('ride__id', 'ride__rider__username', 'ride__driver__username')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('ride', 'sender', 'receiver', 'timestamp')
    search_fields = ('content', 'sender__username', 'receiver__username')
