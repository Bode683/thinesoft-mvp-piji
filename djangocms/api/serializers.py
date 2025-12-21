from rest_framework import serializers
from .models import Todo, User, Tenant
from .utils import can_assign_role


class TenantMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "uuid", "name", "slug")


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = (
            "id",
            "uuid",
            "name",
            "slug",
            "is_active",
            "description",
            "email",
            "url",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "uuid", "created_at", "updated_at")

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ["task", "completed", "timestamp", "updated", "user"]


class UserSerializer(serializers.ModelSerializer):
    tenant = TenantMiniSerializer(read_only=True)

    class Meta:
        model = User
        # Include standard fields plus our custom fields
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            # Custom additions
            "role",
            "tenant",
            "phone_number",
            "bio",
            "url",
            "company",
            "location",
            "birth_date",
            "password_updated",
        )


class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "tenant",
            "phone_number",
            "bio",
            "url",
            "company",
            "location",
            "birth_date",
            "is_active",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        target_role = attrs.get("role")
        target_tenant = attrs.get("tenant")
        if user and user.is_authenticated:
            ok, reason = can_assign_role(user, target_role)
            if not ok:
                raise serializers.ValidationError(reason)
            # For TenantOwner, enforce same-tenant on create/update if tenant provided
            if getattr(user, "role", None) == user.Roles.TENANT_OWNER:
                if target_tenant and target_tenant_id(target_tenant) != getattr(user, "tenant_id", None):
                    raise serializers.ValidationError("TenantOwner can only manage users in their own tenant.")
        return attrs


def target_tenant_id(tenant):
    return getattr(tenant, "id", None)


class RoleAssignmentSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Roles.choices)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        role = attrs.get("role")
        ok, reason = can_assign_role(user, role)
        if not ok:
            raise serializers.ValidationError(reason)
        return attrs


class PasswordSetSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs


class ActivateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()