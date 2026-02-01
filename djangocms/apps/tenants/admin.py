"""
Tenant admin configuration.
"""
from django.contrib import admin
from .models import Tenant, TenantMembership


class TenantMembershipInline(admin.TabularInline):
    """Inline for tenant memberships."""
    model = TenantMembership
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['joined_at']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin for Tenant model."""
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    inlines = [TenantMembershipInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'uuid', 'is_active')
        }),
        ('Contact', {
            'fields': ('email', 'url', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    """Admin for TenantMembership model."""
    list_display = ['user', 'tenant', 'role', 'joined_at']
    list_filter = ['role', 'tenant', 'joined_at']
    search_fields = ['user__email', 'user__username', 'tenant__name']
    raw_id_fields = ['user', 'tenant']
    readonly_fields = ['joined_at']
