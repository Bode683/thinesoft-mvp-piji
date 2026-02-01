"""
Read-only queries for tenants.

Selectors contain query logic without side effects.
"""
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import Tenant, TenantMembership

User = get_user_model()


def get_user_tenants(user) -> QuerySet[Tenant]:
    """
    Get all tenants user is a member of.

    Args:
        user: User instance

    Returns:
        QuerySet of Tenant objects
    """
    return Tenant.objects.filter(
        memberships__user=user,
        is_active=True
    ).distinct()


def get_user_membership(user, tenant: Tenant) -> Optional[TenantMembership]:
    """
    Get user's membership in a specific tenant.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        TenantMembership or None
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant
    ).first()


def get_user_membership_by_slug(user, tenant_slug: str) -> Optional[TenantMembership]:
    """
    Get user's membership in a tenant by slug.

    Args:
        user: User instance
        tenant_slug: Tenant slug

    Returns:
        TenantMembership or None
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant__slug=tenant_slug
    ).select_related('tenant').first()


def get_tenant_members(tenant: Tenant) -> QuerySet[TenantMembership]:
    """
    Get all members of a tenant.

    Args:
        tenant: Tenant instance

    Returns:
        QuerySet of TenantMembership objects with related users
    """
    return TenantMembership.objects.filter(
        tenant=tenant
    ).select_related('user').order_by('-role', 'joined_at')


def get_tenant_by_slug(slug: str) -> Optional[Tenant]:
    """
    Get tenant by slug.

    Args:
        slug: Tenant slug

    Returns:
        Tenant or None
    """
    return Tenant.objects.filter(slug=slug, is_active=True).first()


def get_tenant_by_uuid(uuid_str: str) -> Optional[Tenant]:
    """
    Get tenant by UUID.

    Args:
        uuid_str: Tenant UUID string

    Returns:
        Tenant or None
    """
    try:
        return Tenant.objects.filter(uuid=uuid_str, is_active=True).first()
    except ValueError:
        return None


def get_tenant_owners(tenant: Tenant) -> QuerySet[User]:
    """
    Get all owners of a tenant.

    Args:
        tenant: Tenant instance

    Returns:
        QuerySet of User objects
    """
    return User.objects.filter(
        tenant_memberships__tenant=tenant,
        tenant_memberships__role=TenantMembership.Role.OWNER
    )


def get_tenant_admins(tenant: Tenant) -> QuerySet[User]:
    """
    Get all admins (including owners) of a tenant.

    Args:
        tenant: Tenant instance

    Returns:
        QuerySet of User objects
    """
    return User.objects.filter(
        tenant_memberships__tenant=tenant,
        tenant_memberships__role__in=[
            TenantMembership.Role.OWNER,
            TenantMembership.Role.ADMIN
        ]
    )


def user_is_tenant_member(user, tenant: Tenant) -> bool:
    """
    Check if user is a member of the tenant.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        Boolean
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant
    ).exists()


def user_is_tenant_admin(user, tenant: Tenant) -> bool:
    """
    Check if user is an admin (owner or admin) of the tenant.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        Boolean
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN]
    ).exists()


def user_is_tenant_owner(user, tenant: Tenant) -> bool:
    """
    Check if user is the owner of the tenant.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        Boolean
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        role=TenantMembership.Role.OWNER
    ).exists()
