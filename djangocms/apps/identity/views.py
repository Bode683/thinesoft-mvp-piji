"""
Identity views - authentication and user profile endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import UserSerializer, UserProfileUpdateSerializer


class MeView(APIView):
    """
    Current user profile endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Get current user profile",
        description="""
Retrieve the authenticated user's complete profile including:
- Basic user information (email, name, phone, etc.)
- Keycloak ID and realm roles from JWT
- All tenant memberships with roles
- Subscriber profile if exists

This endpoint provides the full context needed for the authenticated user to understand their
permissions and access across the platform.

### Authentication Required
JWT bearer token from Keycloak.

### Response Fields
- `realm_roles` - Platform-level roles from JWT (e.g., platform_admin)
- `tenant_memberships` - Array of tenant memberships with roles (owner/admin/member)
- `subscriber_profile` - Subscriber details if user has subscriber access
""",
        responses={
            200: OpenApiExample(
                "Success Response",
                value={
                    "id": 1,
                    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "john@example.com",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone_number": "+1234567890",
                    "bio": "Software engineer",
                    "company": "Acme Corp",
                    "location": "San Francisco",
                    "is_superuser": False,
                    "date_joined": "2024-01-01T00:00:00Z",
                    "realm_roles": ["platform_admin"],
                    "tenant_memberships": [
                        {
                            "id": 1,
                            "tenant": {"slug": "acme-corp", "name": "Acme Corp"},
                            "role": "owner",
                            "joined_at": "2024-01-01T00:00:00Z"
                        }
                    ],
                    "subscriber_profile": {
                        "id": 1,
                        "radius_username": "john_sub",
                        "is_active": True,
                        "is_valid": True,
                        "tenant_slug": "acme-corp"
                    }
                },
                response_only=True,
            )
        },
    )
    def get(self, request):
        """Get current user profile with all context."""
        user = request.user

        # Base user data
        data = {
            "id": user.id,
            "keycloak_id": str(user.keycloak_id) if user.keycloak_id else None,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": getattr(user, 'phone_number', ''),
            "bio": getattr(user, 'bio', ''),
            "company": getattr(user, 'company', ''),
            "location": getattr(user, 'location', ''),
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined.isoformat(),
            "realm_roles": [],
            "tenant_memberships": [],
            "subscriber_profile": None,
        }

        # Add realm roles if auth_context available (JWT authentication)
        if hasattr(request, 'auth_context'):
            data["realm_roles"] = request.auth_context.realm_roles

        # Add tenant memberships
        if hasattr(user, 'tenant_memberships'):
            from apps.tenants.serializers import TenantMembershipSerializer
            memberships = user.tenant_memberships.select_related('tenant').all()
            data["tenant_memberships"] = TenantMembershipSerializer(
                memberships, many=True
            ).data

        # Add subscriber profile if exists
        if hasattr(user, 'subscriber_profile'):
            try:
                subscriber = user.subscriber_profile
                data["subscriber_profile"] = {
                    "id": subscriber.id,
                    "radius_username": subscriber.radius_username,
                    "is_active": subscriber.is_active,
                    "is_valid": subscriber.is_valid,
                    "tenant_slug": subscriber.tenant.slug if subscriber.tenant else None,
                }
            except Exception:
                # subscriber_profile might raise DoesNotExist for OneToOne
                pass

        return Response(data)

    @extend_schema(
        tags=["Authentication"],
        summary="Update current user profile",
        description="""
Update the authenticated user's profile fields.

Allowed fields:
- `first_name`
- `last_name`
- `phone_number`
- `bio`
- `company`
- `location`

Returns the complete updated user profile (same as GET /api/v1/auth/me/).

### Authentication Required
JWT bearer token from Keycloak.
""",
        request=UserProfileUpdateSerializer,
        responses={
            200: OpenApiExample(
                "Success Response",
                value={
                    "id": 1,
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Smith",
                    "phone_number": "+1234567890",
                    "bio": "Updated bio",
                    "company": "New Company",
                },
                response_only=True,
            )
        },
        examples=[
            OpenApiExample(
                "Update Profile",
                value={
                    "first_name": "John",
                    "last_name": "Smith",
                    "phone_number": "+1234567890",
                    "bio": "Software engineer with 5 years experience",
                    "company": "Tech Corp",
                    "location": "New York"
                },
                request_only=True,
            )
        ],
    )
    def patch(self, request):
        """Update user profile fields."""
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return full user data
        return self.get(request)
