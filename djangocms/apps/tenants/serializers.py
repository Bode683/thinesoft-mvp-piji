"""
Tenant serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Tenant, TenantMembership

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "uuid",
            "description",
            "email",
            "url",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "is_active", "created_at", "updated_at"]


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Tenant."""

    class Meta:
        model = Tenant
        fields = ["name", "slug", "description", "email", "url"]
        extra_kwargs = {
            "slug": {"required": False},
        }


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Tenant."""

    class Meta:
        model = Tenant
        fields = ["name", "description", "email", "url"]


class TenantMinimalSerializer(serializers.ModelSerializer):
    """Minimal tenant serializer for nested representations."""

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug"]


class MemberUserSerializer(serializers.ModelSerializer):
    """Serializer for user in membership context."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class TenantMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TenantMembership model."""
    tenant = TenantMinimalSerializer(read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "tenant", "role", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class TenantMembershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for TenantMembership with user info."""
    user = MemberUserSerializer(read_only=True)
    tenant = TenantMinimalSerializer(read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "user", "tenant", "role", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a tenant."""
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(
        choices=TenantMembership.Role.choices,
        default=TenantMembership.Role.MEMBER
    )

    def validate(self, data):
        if not data.get('user_id') and not data.get('email'):
            raise serializers.ValidationError(
                "Either user_id or email must be provided"
            )
        return data


class UpdateMemberRoleSerializer(serializers.Serializer):
    """Serializer for updating a member's role."""
    role = serializers.ChoiceField(choices=TenantMembership.Role.choices)
