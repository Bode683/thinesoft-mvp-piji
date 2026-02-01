"""
Business rules for subscriber operations.
"""
import logging
import secrets
import string
from typing import Optional
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.common.exceptions import (
    PermissionDeniedException,
    SubscriberNotFoundException,
)
from apps.tenants.models import Tenant
from apps.tenants import selectors as tenant_selectors
from .models import Subscriber
from . import selectors

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_radius_username(prefix: str = "sub") -> str:
    """
    Generate a unique RADIUS username.

    Args:
        prefix: Username prefix

    Returns:
        Unique username string
    """
    random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    username = f"{prefix}_{random_part}"

    # Ensure uniqueness
    while Subscriber.objects.filter(radius_username=username).exists():
        random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        username = f"{prefix}_{random_part}"

    return username


@transaction.atomic
def create_subscriber(
    user,
    tenant: Tenant,
    requesting_user=None,
    radius_username: Optional[str] = None,
    data_limit_mb: Optional[int] = None,
    time_limit_minutes: Optional[int] = None,
    expires_at=None,
    expires_in_days: Optional[int] = None,
) -> Subscriber:
    """
    Create a subscriber profile for a user.

    Args:
        user: User to create subscriber for
        tenant: Tenant the subscriber belongs to
        requesting_user: User making the request (for permission check)
        radius_username: Custom RADIUS username (auto-generated if not provided)
        data_limit_mb: Data limit in MB (optional)
        time_limit_minutes: Time limit in minutes (optional)
        expires_at: Expiry datetime (optional)
        expires_in_days: Alternative to expires_at - expire in N days

    Returns:
        Created Subscriber instance

    Raises:
        PermissionDeniedException: If requesting user lacks permission
    """
    # Check permissions
    if requesting_user and not requesting_user.is_superuser:
        if not tenant_selectors.user_is_tenant_admin(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant admins can create subscribers")

    # Generate radius_username if not provided
    if not radius_username:
        radius_username = generate_radius_username(prefix=tenant.slug[:10])

    # Calculate expires_at from expires_in_days if provided
    if expires_in_days is not None and expires_at is None:
        expires_at = timezone.now() + timedelta(days=expires_in_days)

    subscriber = Subscriber.objects.create(
        user=user,
        tenant=tenant,
        radius_username=radius_username,
        data_limit_mb=data_limit_mb,
        time_limit_minutes=time_limit_minutes,
        expires_at=expires_at,
    )

    logger.info(f"Created subscriber {radius_username} for {user.email} in {tenant.slug}")
    return subscriber


def update_subscriber(
    subscriber: Subscriber,
    requesting_user,
    **kwargs
) -> Subscriber:
    """
    Update subscriber details.

    Args:
        subscriber: Subscriber to update
        requesting_user: User making the request
        **kwargs: Fields to update

    Returns:
        Updated Subscriber instance
    """
    tenant = subscriber.tenant

    # Check permissions
    if not requesting_user.is_superuser:
        if not tenant_selectors.user_is_tenant_admin(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant admins can update subscribers")

    # Update allowed fields
    allowed_fields = ['is_active', 'data_limit_mb', 'time_limit_minutes', 'expires_at']
    update_fields = []

    for field in allowed_fields:
        if field in kwargs:
            setattr(subscriber, field, kwargs[field])
            update_fields.append(field)

    if update_fields:
        subscriber.save(update_fields=update_fields)
        logger.info(f"Updated subscriber {subscriber.radius_username}: {update_fields}")

    return subscriber


def activate_subscriber(subscriber: Subscriber, requesting_user) -> Subscriber:
    """
    Activate a subscriber.

    Args:
        subscriber: Subscriber to activate
        requesting_user: User making the request

    Returns:
        Updated Subscriber instance
    """
    return update_subscriber(subscriber, requesting_user, is_active=True)


def deactivate_subscriber(subscriber: Subscriber, requesting_user) -> Subscriber:
    """
    Deactivate a subscriber.

    Args:
        subscriber: Subscriber to deactivate
        requesting_user: User making the request

    Returns:
        Updated Subscriber instance
    """
    return update_subscriber(subscriber, requesting_user, is_active=False)


def extend_subscription(
    subscriber: Subscriber,
    requesting_user,
    days: int
) -> Subscriber:
    """
    Extend subscriber's expiration date.

    Args:
        subscriber: Subscriber to extend
        requesting_user: User making the request
        days: Number of days to extend

    Returns:
        Updated Subscriber instance
    """
    # If currently expired or no expiry, start from now
    if subscriber.expires_at is None or subscriber.expires_at < timezone.now():
        new_expires_at = timezone.now() + timedelta(days=days)
    else:
        new_expires_at = subscriber.expires_at + timedelta(days=days)

    return update_subscriber(subscriber, requesting_user, expires_at=new_expires_at)


def set_quotas(
    subscriber: Subscriber,
    requesting_user,
    data_limit_mb: Optional[int] = None,
    time_limit_minutes: Optional[int] = None
) -> Subscriber:
    """
    Set subscriber quotas.

    Args:
        subscriber: Subscriber to update
        requesting_user: User making the request
        data_limit_mb: Data limit in MB (None to clear)
        time_limit_minutes: Time limit in minutes (None to clear)

    Returns:
        Updated Subscriber instance
    """
    return update_subscriber(
        subscriber,
        requesting_user,
        data_limit_mb=data_limit_mb,
        time_limit_minutes=time_limit_minutes
    )


@transaction.atomic
def delete_subscriber(subscriber: Subscriber, requesting_user) -> None:
    """
    Delete a subscriber profile.

    Args:
        subscriber: Subscriber to delete
        requesting_user: User making the request

    Raises:
        PermissionDeniedException: If requesting user lacks permission
    """
    tenant = subscriber.tenant

    # Check permissions
    if not requesting_user.is_superuser:
        if not tenant_selectors.user_is_tenant_admin(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant admins can delete subscribers")

    radius_username = subscriber.radius_username
    subscriber.delete()
    logger.info(f"Deleted subscriber {radius_username} by {requesting_user.email}")


def bulk_deactivate_expired(tenant: Tenant) -> int:
    """
    Deactivate all expired subscribers in a tenant.

    Args:
        tenant: Tenant to process

    Returns:
        Number of subscribers deactivated
    """
    now = timezone.now()
    count = Subscriber.objects.filter(
        tenant=tenant,
        is_active=True,
        expires_at__lt=now
    ).update(is_active=False)

    if count > 0:
        logger.info(f"Deactivated {count} expired subscribers in {tenant.slug}")

    return count
