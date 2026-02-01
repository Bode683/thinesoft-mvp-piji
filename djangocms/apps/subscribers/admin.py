"""
Subscriber admin configuration.
"""
from django.contrib import admin
from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Admin for Subscriber model."""
    list_display = [
        'radius_username',
        'user',
        'tenant',
        'is_active',
        'is_valid_display',
        'expires_at',
        'created_at',
    ]
    list_filter = ['is_active', 'tenant', 'created_at', 'expires_at']
    search_fields = ['radius_username', 'user__email', 'user__username']
    raw_id_fields = ['user', 'tenant']
    readonly_fields = ['created_at', 'updated_at', 'is_valid_display']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('user', 'tenant', 'radius_username', 'is_active')
        }),
        ('Quotas', {
            'fields': ('data_limit_mb', 'time_limit_minutes'),
        }),
        ('Expiry', {
            'fields': ('expires_at', 'is_valid_display'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_valid_display(self, obj):
        """Display is_valid property."""
        return obj.is_valid
    is_valid_display.boolean = True
    is_valid_display.short_description = "Is Valid"
