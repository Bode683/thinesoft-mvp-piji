"""
Identity serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            "id",
            "keycloak_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "bio",
            "company",
            "location",
            "date_joined",
        ]
        read_only_fields = ["id", "keycloak_id", "username", "date_joined"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile fields."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "bio",
            "company",
            "location",
        ]
