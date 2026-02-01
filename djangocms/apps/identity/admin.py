"""
Identity admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin with Keycloak fields."""

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "keycloak_id",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name", "keycloak_id"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Keycloak",
            {
                "fields": ("keycloak_id",),
            },
        ),
        (
            "Profile",
            {
                "fields": ("phone_number", "bio", "company", "location"),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Keycloak",
            {
                "fields": ("keycloak_id",),
            },
        ),
    )

    readonly_fields = ["keycloak_id", "date_joined", "last_login"]
