"""
Platform admin serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, TenantMembership
from apps.subscribers.models import Subscriber

User = get_user_model()


class PlatformUserSerializer(serializers.ModelSerializer):
    """Serializer for User in platform admin context."""
    tenant_count = serializers.SerializerMethodField()
    has_subscriber_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "keycloak_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "tenant_count",
            "has_subscriber_profile",
        ]

    def get_tenant_count(self, obj):
        return obj.tenant_memberships.count()

    def get_has_subscriber_profile(self, obj):
        return hasattr(obj, 'subscriber_profile')


class PlatformTenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant in platform admin context."""
    member_count = serializers.SerializerMethodField()
    subscriber_count = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "uuid",
            "is_active",
            "description",
            "email",
            "url",
            "created_at",
            "updated_at",
            "member_count",
            "subscriber_count",
            "owner_email",
        ]

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_subscriber_count(self, obj):
        return obj.subscribers.count()

    def get_owner_email(self, obj):
        owner = obj.memberships.filter(role=TenantMembership.Role.OWNER).first()
        return owner.user.email if owner else None


class PlatformStatsSerializer(serializers.Serializer):
    """Serializer for platform-wide statistics."""
    total_users = serializers.IntegerField()
    total_tenants = serializers.IntegerField()
    total_subscribers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    tenants_created_this_month = serializers.IntegerField()
    users_created_this_month = serializers.IntegerField()
