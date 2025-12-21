from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate, post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

from .models import User, AuditLog

MANAGED_GROUPS = {
    User.Roles.ADMIN: "Admin",
    User.Roles.TENANT_OWNER: "TenantOwner",
    User.Roles.SUBSCRIBER: "Subscriber",
}


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Ensure default groups exist after migrations.

    This runs for every app; limit to our app label.
    """
    # Only run when the auth app and our app are ready
    for group_name in MANAGED_GROUPS.values():
        Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender=User)
def sync_role_groups(sender, instance: User, **kwargs):
    """Keep user's Django Groups in sync with their role.

    - SuperAdmin: no managed group required.
    - Admin/TenantOwner/Subscriber: ensure membership in corresponding group.
    """
    # If superuser, do not enforce group membership (optional decision)
    if instance.role == User.Roles.SUPERADMIN:
        # Remove from managed groups if present (optional):
        for role, group_name in MANAGED_GROUPS.items():
            try:
                group = Group.objects.get(name=group_name)
                instance.groups.remove(group)
            except Group.DoesNotExist:
                continue
        return

    target_group_name = MANAGED_GROUPS.get(instance.role)
    if not target_group_name:
        return

    # Ensure target group exists and membership is correct
    target_group, _ = Group.objects.get_or_create(name=target_group_name)

    # Remove from other managed groups
    for role, group_name in MANAGED_GROUPS.items():
        if group_name != target_group_name:
            try:
                group = Group.objects.get(name=group_name)
                instance.groups.remove(group)
            except Group.DoesNotExist:
                pass

    # Add to target group
    instance.groups.add(target_group)


# ---- Audit logging for sensitive user changes ----

@receiver(pre_save, sender=User)
def cache_previous_user_state(sender, instance: User, **kwargs):
    """Cache previous values to compare in post_save."""
    if not instance.pk:
        instance._prev_role = None
        instance._prev_is_active = instance.is_active
        return
    try:
        prev = User.objects.get(pk=instance.pk)
        instance._prev_role = prev.role
        instance._prev_is_active = prev.is_active
        # Password hash compare
        instance._prev_password = prev.password
    except User.DoesNotExist:
        instance._prev_role = None
        instance._prev_is_active = instance.is_active
        instance._prev_password = instance.password


@receiver(post_save, sender=User)
def create_user_audit_logs(sender, instance: User, created: bool, **kwargs):
    """Create AuditLog entries when role/password/activation changes happen
    via non-API flows. The API sets `_skip_auto_audit` to avoid duplicates.
    """
    if getattr(instance, "_skip_auto_audit", False):
        return

    # Role change
    prev_role = getattr(instance, "_prev_role", None)
    if prev_role is not None and prev_role != instance.role:
        AuditLog.objects.create(
            actor=None,
            target=instance,
            action=AuditLog.Actions.ROLE_CHANGED,
            details=f"role changed from {prev_role} to {instance.role}",
        )

    # Activation change
    prev_active = getattr(instance, "_prev_is_active", instance.is_active)
    if prev_active != instance.is_active:
        AuditLog.objects.create(
            actor=None,
            target=instance,
            action=AuditLog.Actions.ACTIVATION_CHANGED,
            details=f"is_active changed from {prev_active} to {instance.is_active}",
        )

    # Password change (hash changed)
    prev_password = getattr(instance, "_prev_password", None)
    if prev_password is not None and prev_password != instance.password:
        AuditLog.objects.create(
            actor=None,
            target=instance,
            action=AuditLog.Actions.PASSWORD_RESET,
            details="password hash changed",
        )
