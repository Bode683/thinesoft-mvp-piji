from django.contrib import admin
from .models import Payment, PaymentGatewayConfig, PaymentLog

@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'variant', 'is_active', 'priority']
    list_filter = ['is_active', 'variant']
    list_editable = ['is_active', 'priority']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'variant', 'total', 'currency', 'user', 'created']
    list_filter = ['status', 'variant', 'currency', 'created']
    search_fields = ['id', 'order_id', 'user__username']
    readonly_fields = ['created', 'modified']

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['payment', 'event_type', 'message', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['payment__id', 'message']