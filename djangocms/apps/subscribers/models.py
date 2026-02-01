"""
Subscriber model.

Subscriber = business state, NOT an auth role.
Represents a user's subscription/entitlement within a tenant.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Subscriber(models.Model):
    """
    Subscriber = business state, NOT an auth role.

    Represents a user's subscription/entitlement within a tenant.
    This is used to track:
    - RADIUS authentication credentials
    - Data/time quotas
    - Subscription expiry

    Being a subscriber is determined by the existence and state of this model,
    NOT by any auth role.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriber_profile"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subscribers"
    )
    radius_username = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Username for RADIUS authentication"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the subscription is active"
    )
    data_limit_mb = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Data limit in megabytes (null = unlimited)"
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in minutes (null = unlimited)"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Subscription expiry date (null = never expires)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.radius_username} ({self.tenant.slug})"

    @property
    def is_valid(self) -> bool:
        """
        Check if subscription is currently valid.

        A subscription is valid if:
        - is_active is True
        - expires_at is None OR in the future
        """
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < timezone.now()

    @property
    def days_until_expiry(self) -> int | None:
        """Return days until expiry, or None if never expires."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)
