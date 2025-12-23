from django.contrib import admin
from .models import VehicleType, Vehicle

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_fare', 'per_km_rate', 'per_minute_rate')
    search_fields = ('name',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver', 'vehicle_type', 'is_active', 'is_verified')
    list_filter = ('vehicle_type', 'is_active', 'is_verified')
    search_fields = ('plate_number', 'make', 'model', 'driver__user__username')
    autocomplete_fields = ('driver', 'vehicle_type')
