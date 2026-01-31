from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'phone_number', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'phone_number']
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'status', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['wallet__user__username', 'mpesa_receipt_number', 'description']
    readonly_fields = ['created_at']