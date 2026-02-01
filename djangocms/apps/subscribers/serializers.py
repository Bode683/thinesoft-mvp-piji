"""
Subscriber serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.tenants.serializers import TenantMinimalSerializer
from .models import Subscriber

User = get_user_model()


class SubscriberSerializer(serializers.ModelSerializer):
    """Serializer for Subscriber model."""
    tenant = TenantMinimalSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()

    class Meta:
        model = Subscriber
        fields = [
            "id",
            "tenant",
            "radius_username",
            "is_active",
            "is_valid",
            "is_expired",
            "data_limit_mb",
            "time_limit_minutes",
            "expires_at",
            "days_until_expiry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "radius_username", "created_at", "updated_at",
            "is_valid", "is_expired", "days_until_expiry"
        ]


class SubscriberDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with user info (for tenant admins)."""
    tenant = TenantMinimalSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Subscriber
        fields = [
            "id",
            "user_email",
            "user_name",
            "tenant",
            "radius_username",
            "is_active",
            "is_valid",
            "is_expired",
            "data_limit_mb",
            "time_limit_minutes",
            "expires_at",
            "days_until_expiry",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class CreateSubscriberSerializer(serializers.Serializer):
    """Serializer for creating a subscriber."""
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)
    radius_username = serializers.CharField(max_length=64, required=False)
    data_limit_mb = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    time_limit_minutes = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    expires_in_days = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def validate(self, data):
        if not data.get('user_id') and not data.get('email'):
            raise serializers.ValidationError(
                "Either user_id or email must be provided"
            )
        if data.get('expires_at') and data.get('expires_in_days'):
            raise serializers.ValidationError(
                "Cannot specify both expires_at and expires_in_days"
            )
        return data


class UpdateSubscriberSerializer(serializers.Serializer):
    """Serializer for updating a subscriber."""
    is_active = serializers.BooleanField(required=False)
    data_limit_mb = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    time_limit_minutes = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class ExtendSubscriptionSerializer(serializers.Serializer):
    """Serializer for extending a subscription."""
    days = serializers.IntegerField(min_value=1)
