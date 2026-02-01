"""
Tenant and TenantMembership models.

Tenant = Organization/company entity
TenantMembership = User-tenant relationship with tenant-scoped role

THIS is where tenant authorization lives - NOT in Keycloak.
"""
from django.db import models
from django.conf import settings
import uuid


class Tenant(models.Model):
    """
    Organization/tenant entity.

    Tenants are the organizational unit for multi-tenancy.
    Users access tenants through TenantMembership.
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    """
    User-tenant relationship with tenant-scoped role.

    THIS is where tenant authorization lives:
    - owner: Full control over tenant
    - admin: Can manage members and settings
    - member: Regular access

    Note: Platform-level roles (platform_admin) come from Keycloak,
    not from this model.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships"
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tenant")
        indexes = [
            models.Index(fields=["tenant", "role"]),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.tenant.slug} ({self.role})"

    @property
    def is_owner(self) -> bool:
        """Check if this membership has owner role."""
        return self.role == self.Role.OWNER

    @property
    def is_admin(self) -> bool:
        """Check if this membership has admin or owner role."""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
