"""
Business rules for tenant operations.

Services contain business logic with side effects.
"""
import logging
from typing import Tuple, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.common.exceptions import (
    PermissionDeniedException,
    TenantNotFoundException,
    MembershipNotFoundException,
)
from .models import Tenant, TenantMembership
from . import selectors

logger = logging.getLogger(__name__)
User = get_user_model()


@transaction.atomic
def create_tenant(
    name: str,
    owner_user,
    slug: Optional[str] = None,
    description: str = "",
    email: str = "",
    url: str = ""
) -> Tenant:
    """
    Create a tenant and set the creator as owner.

    Args:
        name: Tenant name (unique)
        owner_user: User to be set as owner
        slug: Optional custom slug (auto-generated if not provided)
        description: Optional description
        email: Optional contact email
        url: Optional website URL

    Returns:
        Created Tenant instance
    """
    if slug is None:
        slug = slugify(name)

    tenant = Tenant.objects.create(
        name=name,
        slug=slug,
        description=description,
        email=email,
        url=url
    )

    # Create owner membership
    TenantMembership.objects.create(
        user=owner_user,
        tenant=tenant,
        role=TenantMembership.Role.OWNER
    )

    logger.info(f"Created tenant '{tenant.name}' with owner {owner_user.email}")
    return tenant


def update_tenant(
    tenant: Tenant,
    requesting_user,
    **kwargs
) -> Tenant:
    """
    Update tenant details.

    Only owners can update tenant details (unless platform admin).

    Args:
        tenant: Tenant to update
        requesting_user: User making the request
        **kwargs: Fields to update (name, description, email, url)

    Returns:
        Updated Tenant instance

    Raises:
        PermissionDeniedException: If user is not owner or platform admin
    """
    # Check permissions
    if not requesting_user.is_superuser:
        if not selectors.user_is_tenant_owner(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant owners can update tenant details")

    # Update allowed fields
    allowed_fields = ['name', 'description', 'email', 'url']
    for field in allowed_fields:
        if field in kwargs:
            setattr(tenant, field, kwargs[field])

    tenant.save()
    logger.info(f"Updated tenant '{tenant.name}' by {requesting_user.email}")
    return tenant


@transaction.atomic
def add_member(
    tenant: Tenant,
    user,
    role: str = TenantMembership.Role.MEMBER,
    requesting_user=None
) -> Tuple[TenantMembership, bool]:
    """
    Add a user as a member of a tenant.

    Args:
        tenant: Tenant to add member to
        user: User to add
        role: Role to assign (default: member)
        requesting_user: User making the request (for permission check)

    Returns:
        Tuple of (TenantMembership, created: bool)

    Raises:
        PermissionDeniedException: If requesting user lacks permission
    """
    # Check permissions if requesting_user is provided
    if requesting_user and not requesting_user.is_superuser:
        if not selectors.user_is_tenant_admin(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant admins can add members")

    membership, created = TenantMembership.objects.get_or_create(
        user=user,
        tenant=tenant,
        defaults={'role': role}
    )

    if created:
        logger.info(f"Added {user.email} to tenant '{tenant.name}' as {role}")
    else:
        logger.info(f"User {user.email} already member of tenant '{tenant.name}'")

    return membership, created


def update_member_role(
    membership: TenantMembership,
    new_role: str,
    requesting_user
) -> TenantMembership:
    """
    Update a member's role within a tenant.

    Args:
        membership: TenantMembership to update
        new_role: New role to assign
        requesting_user: User making the request

    Returns:
        Updated TenantMembership

    Raises:
        PermissionDeniedException: If requesting user lacks permission
    """
    tenant = membership.tenant

    # Check permissions
    if not requesting_user.is_superuser:
        # Only owners can change roles
        if not selectors.user_is_tenant_owner(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant owners can change member roles")

        # Cannot demote yourself as owner (must transfer ownership first)
        if membership.user == requesting_user and membership.role == TenantMembership.Role.OWNER:
            raise PermissionDeniedException("Cannot demote yourself. Transfer ownership first.")

    old_role = membership.role
    membership.role = new_role
    membership.save(update_fields=['role'])

    logger.info(
        f"Changed {membership.user.email} role in '{tenant.name}' "
        f"from {old_role} to {new_role}"
    )
    return membership


@transaction.atomic
def remove_member(
    membership: TenantMembership,
    requesting_user
) -> None:
    """
    Remove a member from a tenant.

    Args:
        membership: TenantMembership to remove
        requesting_user: User making the request

    Raises:
        PermissionDeniedException: If requesting user lacks permission
    """
    tenant = membership.tenant

    # Check permissions
    if not requesting_user.is_superuser:
        # Admins can remove members (but not other admins/owners)
        if not selectors.user_is_tenant_admin(requesting_user, tenant):
            raise PermissionDeniedException("Only tenant admins can remove members")

        # Cannot remove owners
        if membership.role == TenantMembership.Role.OWNER:
            raise PermissionDeniedException("Cannot remove tenant owner")

        # Cannot remove yourself (use leave_tenant instead)
        if membership.user == requesting_user:
            raise PermissionDeniedException("Use leave_tenant to remove yourself")

        # Admins cannot remove other admins (only owners can)
        if membership.role == TenantMembership.Role.ADMIN:
            if not selectors.user_is_tenant_owner(requesting_user, tenant):
                raise PermissionDeniedException("Only owners can remove admins")

    user_email = membership.user.email
    membership.delete()
    logger.info(f"Removed {user_email} from tenant '{tenant.name}'")


def leave_tenant(
    tenant: Tenant,
    user
) -> None:
    """
    User leaves a tenant voluntarily.

    Args:
        tenant: Tenant to leave
        user: User leaving

    Raises:
        MembershipNotFoundException: If user is not a member
        PermissionDeniedException: If user is the sole owner
    """
    membership = selectors.get_user_membership(user, tenant)
    if not membership:
        raise MembershipNotFoundException()

    # Check if sole owner
    if membership.role == TenantMembership.Role.OWNER:
        owner_count = TenantMembership.objects.filter(
            tenant=tenant,
            role=TenantMembership.Role.OWNER
        ).count()
        if owner_count == 1:
            raise PermissionDeniedException(
                "Cannot leave as sole owner. Transfer ownership first."
            )

    membership.delete()
    logger.info(f"User {user.email} left tenant '{tenant.name}'")


@transaction.atomic
def transfer_ownership(
    tenant: Tenant,
    from_user,
    to_user
) -> Tuple[TenantMembership, TenantMembership]:
    """
    Transfer tenant ownership from one user to another.

    Args:
        tenant: Tenant to transfer
        from_user: Current owner
        to_user: New owner

    Returns:
        Tuple of (old_owner_membership, new_owner_membership)

    Raises:
        PermissionDeniedException: If from_user is not owner
        MembershipNotFoundException: If to_user is not a member
    """
    # Verify from_user is owner
    from_membership = selectors.get_user_membership(from_user, tenant)
    if not from_membership or from_membership.role != TenantMembership.Role.OWNER:
        raise PermissionDeniedException("Only current owner can transfer ownership")

    # Verify to_user is a member
    to_membership = selectors.get_user_membership(to_user, tenant)
    if not to_membership:
        raise MembershipNotFoundException("Target user is not a member of this tenant")

    # Transfer ownership
    from_membership.role = TenantMembership.Role.ADMIN
    from_membership.save(update_fields=['role'])

    to_membership.role = TenantMembership.Role.OWNER
    to_membership.save(update_fields=['role'])

    logger.info(
        f"Transferred ownership of '{tenant.name}' "
        f"from {from_user.email} to {to_user.email}"
    )

    return from_membership, to_membership


def can_user_manage_tenant(user, tenant: Tenant) -> bool:
    """
    Check if user can manage the tenant (owner or admin).

    Args:
        user: User to check
        tenant: Tenant to check

    Returns:
        Boolean
    """
    if user.is_superuser:
        return True
    return selectors.user_is_tenant_admin(user, tenant)
