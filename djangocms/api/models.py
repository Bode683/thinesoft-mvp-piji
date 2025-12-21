from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import uuid

class Tenant(models.Model):
    """Represents an organization/tenant."""
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=160, unique=True, db_index=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user with role and optional tenant association."""

    class Roles(models.TextChoices):
        SUPERADMIN = "superadmin", "SuperAdmin"
        ADMIN = "admin", "Admin"
        TENANT_OWNER = "tenant_owner", "Tenant Owner"
        SUBSCRIBER = "subscriber", "Subscriber"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.SUBSCRIBER,
        help_text="Application role for coarse-grained permissions.",
    )
    tenant = models.ForeignKey(
        Tenant,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
        help_text="Optional tenant association for multitenancy.",
    )
    # Profile fields
    phone_number = models.CharField(max_length=32, blank=True)
    bio = models.TextField(blank=True)
    url = models.URLField(blank=True)
    company = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    password_updated = models.DateTimeField(null=True, blank=True)

    class Meta(AbstractUser.Meta):
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["role"]),
        ]

    def save(self, *args, **kwargs):
        """Make role the single source of truth for flags.

        - SUPERADMIN -> is_staff=True, is_superuser=True
        - ADMIN -> is_staff=True, is_superuser=False
        - Others -> is_staff=False, is_superuser=False
        """
        if self.role == self.Roles.SUPERADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role == self.Roles.ADMIN:
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

class Todo(models.Model):
    task = models.CharField(max_length = 180)
    timestamp = models.DateTimeField(auto_now_add = True, auto_now = False, blank = True)
    completed = models.BooleanField(default = False, blank = True)
    updated = models.DateTimeField(auto_now = True, blank = True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return self.task


class AuditLog(models.Model):
    """Audit sensitive user management actions."""
    class Actions(models.TextChoices):
        ROLE_CHANGED = "role_changed", "Role Changed"
        PASSWORD_RESET = "password_reset", "Password Reset"
        ACTIVATION_CHANGED = "activation_changed", "Activation Changed"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acted_logs",
        help_text="Who performed the action. Null if system/unknown.",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="audit_targets",
        help_text="The user affected by the action.",
    )
    action = models.CharField(max_length=64)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self) -> str:
        return f"{self.timestamp} {self.action} -> {getattr(self.target, 'username', self.target_id)}"