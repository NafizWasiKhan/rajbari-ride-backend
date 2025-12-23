from django.contrib import admin
from .models import Payment, Wallet, Transaction

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'ride', 'amount', 'status', 'provider', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('transaction_id', 'ride__id')
    readonly_fields = ('transaction_id', 'ride', 'amount', 'provider', 'val_id', 'created_at', 'updated_at')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'wallet', 'amount', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('wallet__user__username', 'description')
    readonly_fields = ('timestamp',)
