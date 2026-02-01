"""
Read-only queries for subscribers.
"""
from typing import Optional
from django.db.models import QuerySet, Q
from django.utils import timezone
from datetime import timedelta

from apps.tenants.models import Tenant
from .models import Subscriber


def get_subscriber_by_user(user) -> Optional[Subscriber]:
    """
    Get subscriber profile for a user.

    Args:
        user: User instance

    Returns:
        Subscriber or None
    """
    try:
        return user.subscriber_profile
    except Subscriber.DoesNotExist:
        return None


def get_subscriber_by_radius_username(radius_username: str) -> Optional[Subscriber]:
    """
    Get subscriber by RADIUS username.

    Args:
        radius_username: RADIUS username

    Returns:
        Subscriber or None
    """
    return Subscriber.objects.filter(
        radius_username=radius_username
    ).select_related('user', 'tenant').first()


def get_tenant_subscribers(tenant: Tenant, active_only: bool = False) -> QuerySet[Subscriber]:
    """
    Get all subscribers of a tenant.

    Args:
        tenant: Tenant instance
        active_only: If True, only return active subscribers

    Returns:
        QuerySet of Subscriber objects
    """
    qs = Subscriber.objects.filter(tenant=tenant).select_related('user')
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by('-created_at')


def get_valid_subscribers(tenant: Tenant) -> QuerySet[Subscriber]:
    """
    Get all currently valid subscribers (active and not expired).

    Args:
        tenant: Tenant instance

    Returns:
        QuerySet of valid Subscriber objects
    """
    now = timezone.now()
    return Subscriber.objects.filter(
        tenant=tenant,
        is_active=True
    ).filter(
        # expires_at is NULL (never expires) or in the future
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    ).select_related('user')


def get_expiring_subscribers(tenant: Tenant, days: int = 7) -> QuerySet[Subscriber]:
    """
    Get subscribers expiring within the specified number of days.

    Args:
        tenant: Tenant instance
        days: Number of days to look ahead

    Returns:
        QuerySet of Subscriber objects
    """
    now = timezone.now()
    future = now + timedelta(days=days)

    return Subscriber.objects.filter(
        tenant=tenant,
        is_active=True,
        expires_at__isnull=False,
        expires_at__gte=now,
        expires_at__lte=future
    ).select_related('user').order_by('expires_at')


def get_expired_subscribers(tenant: Tenant) -> QuerySet[Subscriber]:
    """
    Get all expired subscribers (for cleanup or notification).

    Args:
        tenant: Tenant instance

    Returns:
        QuerySet of expired Subscriber objects
    """
    now = timezone.now()
    return Subscriber.objects.filter(
        tenant=tenant,
        expires_at__lt=now
    ).select_related('user')


def user_is_subscriber(user) -> bool:
    """
    Check if user has a subscriber profile.

    Args:
        user: User instance

    Returns:
        Boolean
    """
    return Subscriber.objects.filter(user=user).exists()


def user_is_active_subscriber(user) -> bool:
    """
    Check if user has an active and valid subscriber profile.

    Args:
        user: User instance

    Returns:
        Boolean
    """
    subscriber = get_subscriber_by_user(user)
    return subscriber is not None and subscriber.is_valid


def count_tenant_subscribers(tenant: Tenant, active_only: bool = False) -> int:
    """
    Count subscribers in a tenant.

    Args:
        tenant: Tenant instance
        active_only: If True, only count active subscribers

    Returns:
        Integer count
    """
    qs = Subscriber.objects.filter(tenant=tenant)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.count()
