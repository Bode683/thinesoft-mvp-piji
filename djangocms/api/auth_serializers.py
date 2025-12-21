from typing import Any, Dict
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from .models import User
from .serializers import TenantMiniSerializer


class CustomRegisterSerializer(RegisterSerializer):
    """Extend registration to accept and save first_name/last_name (and optional profile fields)."""

    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def get_cleaned_data(self) -> Dict[str, Any]:
        data = super().get_cleaned_data()
        data["first_name"] = self.validated_data.get("first_name", "")
        data["last_name"] = self.validated_data.get("last_name", "")
        return data

    def save(self, request):
        user = super().save(request)
        cleaned = self.get_cleaned_data()
        user.first_name = cleaned.get("first_name", "")
        user.last_name = cleaned.get("last_name", "")
        # Do NOT set role/tenant from public registration
        user.save()
        return user


class AuthUserDetailsSerializer(UserDetailsSerializer):
    """User details for /dj-rest-auth/user/ endpoint.

    - Allows updating first_name, last_name, and safe profile fields.
    - Exposes role and tenant as read-only for transparency.
    - Hides/is read-only for permission flags.
    """

    # Display tenant in a minimal form, read-only
    tenant = TenantMiniSerializer(read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = User
        # Base fields from UserDetailsSerializer are (usually): ('pk','username','email','first_name','last_name')
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            # read-only context
            "role",
            "tenant",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "password_updated",
            # editable profile fields
            "phone_number",
            "bio",
            "url",
            "company",
            "location",
            "birth_date",
        )
        read_only_fields = (
            "id",
            "role",
            "tenant",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "password_updated",
        )
