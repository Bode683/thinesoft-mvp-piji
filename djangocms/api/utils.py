from typing import Optional, Tuple
from .models import User


def can_assign_role(actor: User, target_role: str, target: Optional[User] = None) -> Tuple[bool, Optional[str]]:
    """Centralized rule for whether `actor` can assign `target_role` to `target`.

    Rules:
    - SuperAdmin: can assign any role.
    - Platform Admin (is_staff and not superuser): can assign any non-SuperAdmin role by default.
    - TenantOwner: can assign only within own tenant and cannot assign Admin/SuperAdmin.
    - Subscribers: cannot assign roles.
    - If `target` provided, enforce same-tenant constraint for TenantOwner.
    """
    if not actor or not actor.is_authenticated:
        return False, "Authentication required."

    if actor.is_superuser:
        return True, None

    if actor.is_staff:
        # Platform admin: allow all except SuperAdmin
        if target_role == User.Roles.SUPERADMIN:
            return False, "Platform Admin cannot assign SuperAdmin role."
        return True, None

    # TenantOwner rules
    if getattr(actor, "role", None) == User.Roles.TENANT_OWNER:
        if target_role in (User.Roles.ADMIN, User.Roles.SUPERADMIN):
            return False, "TenantOwner cannot assign Admin or SuperAdmin roles."
        if target is not None and getattr(target, "tenant_id", None) != getattr(actor, "tenant_id", None):
            return False, "TenantOwner can only manage users in their own tenant."
        return True, None

    return False, "Insufficient permissions to assign roles."
