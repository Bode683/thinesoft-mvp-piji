from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Tenant

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "tenant", "is_staff", "is_superuser")
    list_filter = ("role", "tenant", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name", "company")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Roles & Tenant", {"fields": ("role", "tenant")}),
        (
            "Profile",
            {"fields": ("phone_number", "bio", "url", "company", "location", "birth_date", "password_updated")},
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "tenant",
                    "phone_number",
                    "company",
                ),
            },
        ),
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
