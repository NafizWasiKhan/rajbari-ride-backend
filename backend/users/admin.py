from django.contrib import admin
from .models import Profile, DriverDocument

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified', 'verification_status', 'is_online')
    list_filter = ('role', 'is_verified', 'verification_status', 'is_online')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('rating', 'trips_completed')

@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'document_type', 'is_verified', 'expiry_date')
    list_filter = ('document_type', 'is_verified')
    search_fields = ('profile__user__username', 'document_number')
