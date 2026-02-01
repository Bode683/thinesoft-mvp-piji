"""
Tenant views.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from apps.common.exceptions import TenantNotFoundException
from apps.platform.permissions import IsPlatformAdmin
from .models import Tenant, TenantMembership
from .permissions import IsTenantMember, IsTenantOwner, IsTenantAdmin
from .serializers import (
    TenantSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantMembershipDetailSerializer,
    AddMemberSerializer,
    UpdateMemberRoleSerializer,
)
from . import selectors, services

User = get_user_model()


class TenantListView(APIView):
    """
    Tenant management endpoints.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Tenants"],
        summary="List user's tenants",
        description="""
List all tenants where the authenticated user has membership.

Returns tenants where the user is an owner, admin, or member.
Platform admins see all active tenants.

### Authentication Required
JWT bearer token from Keycloak.

### Permission Required
Authenticated user (returns user's own tenants).
""",
        responses={
            200: OpenApiExample(
                "Success Response",
                value=[
                    {
                        "id": 1,
                        "name": "Acme Corp",
                        "slug": "acme-corp",
                        "description": "Main organization",
                        "email": "admin@acme.com",
                        "url": "https://acme.com",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "member_count": 5,
                    }
                ],
                response_only=True,
            )
        },
    )
    def get(self, request):
        """List all tenants the user is a member of."""
        tenants = selectors.get_user_tenants(request.user)
        serializer = TenantSerializer(tenants, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Tenants"],
        summary="Create new tenant",
        description="""
Create a new tenant organization.

**IMPORTANT:** Only platform administrators can create tenants.

The creating user automatically becomes the tenant owner with full permissions.

### Authentication Required
JWT bearer token from Keycloak.

### Permission Required
- `platform_admin` realm role OR
- Django superuser

### Auto-Created Resources
When a tenant is created:
1. Tenant record with unique slug
2. Owner membership for the creating user
""",
        request=TenantCreateSerializer,
        responses={
            201: TenantSerializer,
            403: OpenApiExample(
                "Permission Denied",
                value={"detail": "Only platform administrators can create tenants."},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Create Tenant",
                value={
                    "name": "New Organization",
                    "slug": "new-org",
                    "description": "Our new tenant",
                    "email": "admin@neworg.com",
                    "url": "https://neworg.com"
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        """Create a new tenant (platform admin or superuser only)."""
        # Check platform admin permission
        is_platform_admin = (
            request.user.is_superuser or
            (hasattr(request, 'auth_context') and request.auth_context.is_platform_admin())
        )

        if not is_platform_admin:
            return Response(
                {"detail": "Only platform administrators can create tenants."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = services.create_tenant(
            owner_user=request.user,
            **serializer.validated_data
        )

        return Response(
            TenantSerializer(tenant).data,
            status=status.HTTP_201_CREATED
        )


class TenantDetailView(APIView):
    """
    Tenant detail and management endpoints.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant(self, slug):
        tenant = selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()
        return tenant

    @extend_schema(
        tags=["Tenants"],
        summary="Get tenant details",
        description="""
Retrieve detailed information about a specific tenant.

### Authentication Required
JWT bearer token from Keycloak.

### Permission Required
- User must be a member of the tenant (owner/admin/member) OR
- Platform admin OR
- Django superuser

### Path Parameters
- `slug` - Tenant identifier (e.g., 'acme-corp')
""",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Tenant slug identifier",
                required=True,
            )
        ],
        responses={
            200: TenantSerializer,
            403: OpenApiExample(
                "Not a Member",
                value={"detail": "You are not a member of this tenant."},
                response_only=True,
            ),
            404: OpenApiExample(
                "Not Found",
                value={"detail": "Tenant not found."},
                response_only=True,
            ),
        },
    )
    def get(self, request, slug):
        """Get tenant details (members only)."""
        tenant = self.get_tenant(slug)

        # Check membership
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_member(request.user, tenant):
                return Response(
                    {"detail": "You are not a member of this tenant."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

    @extend_schema(
        tags=["Tenants"],
        summary="Update tenant details",
        description="""
Update tenant information.

### Authentication Required
JWT bearer token from Keycloak.

### Permission Required
- Tenant owner OR
- Platform admin OR
- Django superuser

### Path Parameters
- `slug` - Tenant identifier

### Updatable Fields
- `name` - Organization name
- `description` - Organization description
- `email` - Contact email
- `url` - Organization website
""",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Tenant slug identifier",
                required=True,
            )
        ],
        request=TenantUpdateSerializer,
        responses={
            200: TenantSerializer,
            403: OpenApiExample(
                "Permission Denied",
                value={"detail": "Only tenant owners can update tenant details."},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Update Tenant",
                value={
                    "name": "Updated Name",
                    "description": "New description",
                },
                request_only=True,
            )
        ],
    )
    def patch(self, request, slug):
        """Update tenant details (owner only)."""
        tenant = self.get_tenant(slug)

        # Check owner permission
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_owner(request.user, tenant):
                return Response(
                    {"detail": "Only tenant owners can update tenant details."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TenantUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tenant = services.update_tenant(
            tenant=tenant,
            requesting_user=request.user,
            **serializer.validated_data
        )

        return Response(TenantSerializer(tenant).data)

    @extend_schema(
        tags=["Tenants"],
        summary="Deactivate tenant",
        description="""
Soft-delete a tenant by marking it as inactive.

This does NOT delete the tenant data, only sets `is_active=False`.

### Permission Required
- Tenant owner OR
- Django superuser
""",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Tenant slug identifier",
                required=True,
            )
        ],
        responses={
            204: None,
            403: OpenApiExample(
                "Permission Denied",
                value={"detail": "Only tenant owners can deactivate the tenant."},
                response_only=True,
            ),
        },
    )
    def delete(self, request, slug):
        """Deactivate tenant (owner only)."""
        tenant = self.get_tenant(slug)

        # Check owner permission
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_owner(request.user, tenant):
                return Response(
                    {"detail": "Only tenant owners can deactivate the tenant."},
                    status=status.HTTP_403_FORBIDDEN
                )

        tenant.is_active = False
        tenant.save(update_fields=['is_active'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class TenantMemberListView(APIView):
    """
    Tenant member management endpoints.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant(self, slug):
        tenant = selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()
        return tenant

    @extend_schema(
        tags=["Members"],
        summary="List tenant members",
        description="""
List all members of a tenant with their roles.

### Permission Required
- Tenant member (any role: owner/admin/member)

Returns all memberships including:
- User details
- Role (owner, admin, or member)
- Join date
""",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Tenant slug identifier",
                required=True,
            )
        ],
        responses={
            200: TenantMembershipDetailSerializer(many=True),
        },
    )
    def get(self, request, slug):
        """List all members of the tenant."""
        tenant = self.get_tenant(slug)

        # Check membership
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_member(request.user, tenant):
                return Response(
                    {"detail": "You are not a member of this tenant."},
                    status=status.HTTP_403_FORBIDDEN
                )

        members = selectors.get_tenant_members(tenant)
        serializer = TenantMembershipDetailSerializer(members, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Members"],
        summary="Add member to tenant",
        description="""
Add a new member to the tenant.

### Permission Required
- Tenant admin or owner

### Request Parameters
Provide either `user_id` or `email`:
- `user_id` - User's database ID
- `email` - User's email address
- `role` - Member role: 'member', 'admin', or 'owner'

### Role Hierarchy
- `owner` - Full control, can manage all members
- `admin` - Can manage members and subscribers
- `member` - Read-only access
""",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Tenant slug identifier",
                required=True,
            )
        ],
        request=AddMemberSerializer,
        responses={
            201: TenantMembershipDetailSerializer,
            200: TenantMembershipDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "Add by Email",
                value={"email": "newuser@example.com", "role": "member"},
                request_only=True,
            ),
            OpenApiExample(
                "Add by User ID",
                value={"user_id": 5, "role": "admin"},
                request_only=True,
            ),
        ],
    )
    def post(self, request, slug):
        """Add a member to the tenant (admin only)."""
        tenant = self.get_tenant(slug)

        # Check admin permission
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can add members."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find user by id or email
        user_id = serializer.validated_data.get('user_id')
        email = serializer.validated_data.get('email')
        role = serializer.validated_data['role']

        if user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            user = get_object_or_404(User, email=email)

        membership, created = services.add_member(
            tenant=tenant,
            user=user,
            role=role,
            requesting_user=request.user
        )

        return Response(
            TenantMembershipDetailSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class TenantMemberDetailView(APIView):
    """
    Tenant member detail and modification endpoints.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant_and_membership(self, slug, membership_id):
        tenant = selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()

        membership = TenantMembership.objects.filter(
            id=membership_id,
            tenant=tenant
        ).select_related('user', 'tenant').first()

        if not membership:
            return tenant, None

        return tenant, membership

    @extend_schema(
        tags=["Members"],
        summary="Get member details",
        description="Retrieve details of a specific tenant member.",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="membership_id", type=int, location=OpenApiParameter.PATH),
        ],
        responses={200: TenantMembershipDetailSerializer},
    )
    def get(self, request, slug, membership_id):
        """Get member details."""
        tenant, membership = self.get_tenant_and_membership(slug, membership_id)

        if not membership:
            return Response(
                {"detail": "Membership not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check membership
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_member(request.user, tenant):
                return Response(
                    {"detail": "You are not a member of this tenant."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TenantMembershipDetailSerializer(membership)
        return Response(serializer.data)

    @extend_schema(
        tags=["Members"],
        summary="Update member role",
        description="""
Change a member's role within the tenant.

### Permission Required
- Tenant owner only
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="membership_id", type=int, location=OpenApiParameter.PATH),
        ],
        request=UpdateMemberRoleSerializer,
        responses={200: TenantMembershipDetailSerializer},
        examples=[
            OpenApiExample(
                "Promote to Admin",
                value={"role": "admin"},
                request_only=True,
            )
        ],
    )
    def patch(self, request, slug, membership_id):
        """Update member role (owner only)."""
        tenant, membership = self.get_tenant_and_membership(slug, membership_id)

        if not membership:
            return Response(
                {"detail": "Membership not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check owner permission
        if not request.user.is_superuser:
            if not selectors.user_is_tenant_owner(request.user, tenant):
                return Response(
                    {"detail": "Only tenant owners can change member roles."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = services.update_member_role(
            membership=membership,
            new_role=serializer.validated_data['role'],
            requesting_user=request.user
        )

        return Response(TenantMembershipDetailSerializer(membership).data)

    @extend_schema(
        tags=["Members"],
        summary="Remove member from tenant",
        description="""
Remove a member from the tenant.

### Permission Required
- Tenant admin or owner

### Important
- Cannot remove the last owner
- Service layer enforces business rules
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="membership_id", type=int, location=OpenApiParameter.PATH),
        ],
        responses={204: None},
    )
    def delete(self, request, slug, membership_id):
        """Remove member from tenant (admin only)."""
        tenant, membership = self.get_tenant_and_membership(slug, membership_id)

        if not membership:
            return Response(
                {"detail": "Membership not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        services.remove_member(
            membership=membership,
            requesting_user=request.user
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveTenantView(APIView):
    """
    Leave tenant endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Members"],
        summary="Leave tenant voluntarily",
        description="""
Allow a user to voluntarily leave a tenant.

### Business Rules
- Cannot leave if you're the last owner
- Automatically removes your membership
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
        ],
        request=None,
        responses={
            200: OpenApiExample(
                "Success",
                value={"detail": "Successfully left the tenant."},
                response_only=True,
            )
        },
    )
    def post(self, request, slug):
        """Leave a tenant voluntarily."""
        tenant = selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()

        services.leave_tenant(tenant=tenant, user=request.user)

        return Response(
            {"detail": "Successfully left the tenant."},
            status=status.HTTP_200_OK
        )
