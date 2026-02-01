"""
Custom User model with Keycloak integration.

NO role field - roles come from:
- request.auth_context.realm_roles (platform-level)
- TenantMembership.role (tenant-scoped)

NO tenant FK - use TenantMembership for multi-tenant access
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user with Keycloak integration.

    This is a lean user model - authorization information comes from:
    - request.auth_context.realm_roles for platform-level roles (from JWT)
    - TenantMembership.role for tenant-scoped roles (from database)
    """
    keycloak_id = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="Keycloak user ID from 'sub' claim"
    )

    # Profile fields only
    phone_number = models.CharField(max_length=32, blank=True)
    bio = models.TextField(blank=True)
    company = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=150, blank=True)

    class Meta(AbstractUser.Meta):
        pass

    def save(self, *args, **kwargs):
        # Set unusable password for Keycloak users (they authenticate via IDP)
        if self.keycloak_id and not self.has_usable_password():
            self.set_unusable_password()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username
