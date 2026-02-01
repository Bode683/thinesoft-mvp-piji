"""
Platform admin views - cross-tenant administration.
"""
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from apps.tenants.models import Tenant
from apps.subscribers.models import Subscriber
from .permissions import IsPlatformAdmin
from .serializers import (
    PlatformUserSerializer,
    PlatformTenantSerializer,
    PlatformStatsSerializer,
)

User = get_user_model()


class PlatformStatsView(APIView):
    """
    Platform statistics endpoint.
    """
    permission_classes = [IsPlatformAdmin]

    @extend_schema(
        tags=["Platform"],
        summary="Get platform statistics",
        description="""
Retrieve platform-wide statistics and metrics.

### Permission Required
- `platform_admin` realm role OR Django superuser

### Statistics Included
- Total users
- Total active tenants
- Total subscribers (all and active)
- New tenants this month
- New users this month
""",
        responses={200: PlatformStatsSerializer},
    )
    def get(self, request):
        """Get platform-wide statistics."""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        stats = {
            "total_users": User.objects.count(),
            "total_tenants": Tenant.objects.filter(is_active=True).count(),
            "total_subscribers": Subscriber.objects.count(),
            "active_subscribers": Subscriber.objects.filter(is_active=True).count(),
            "tenants_created_this_month": Tenant.objects.filter(
                created_at__gte=month_ago
            ).count(),
            "users_created_this_month": User.objects.filter(
                date_joined__gte=month_ago
            ).count(),
        }

        serializer = PlatformStatsSerializer(stats)
        return Response(serializer.data)


class PlatformUserListView(APIView):
    """
    Platform user management endpoint.
    """
    permission_classes = [IsPlatformAdmin]

    @extend_schema(
        tags=["Platform"],
        summary="List all users",
        description="""
List all users in the system with filtering and pagination.

### Permission Required
- `platform_admin` realm role OR Django superuser

### Query Parameters
- `is_active` - Filter by active status (true/false)
- `has_keycloak` - Filter by Keycloak ID presence (true/false)
- `search` - Search by email, username, first/last name
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
""",
        parameters=[
            OpenApiParameter(name="is_active", type=bool, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="has_keycloak", type=bool, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
        ],
        responses={
            200: OpenApiExample(
                "Paginated Response",
                value={
                    "count": 100,
                    "page": 1,
                    "page_size": 20,
                    "results": [{"id": 1, "email": "user@example.com"}]
                },
                response_only=True,
            )
        },
    )
    def get(self, request):
        """List all users with optional filtering."""
        users = User.objects.all().order_by('-date_joined')

        # Optional filters
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')

        has_keycloak = request.query_params.get('has_keycloak')
        if has_keycloak is not None:
            if has_keycloak.lower() == 'true':
                users = users.filter(keycloak_id__isnull=False)
            else:
                users = users.filter(keycloak_id__isnull=True)

        search = request.query_params.get('search')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size

        total = users.count()
        users = users[offset:offset + page_size]

        serializer = PlatformUserSerializer(users, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data
        })


class PlatformUserDetailView(APIView):
    """
    Platform user detail endpoint.
    """
    permission_classes = [IsPlatformAdmin]

    @extend_schema(
        tags=["Platform"],
        summary="Get user details",
        description="Retrieve detailed information about a specific user. Requires platform admin permission.",
        parameters=[
            OpenApiParameter(name="user_id", type=int, location=OpenApiParameter.PATH),
        ],
        responses={200: PlatformUserSerializer},
    )
    def get(self, request, user_id):
        """Get detailed user information."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlatformUserSerializer(user)
        return Response(serializer.data)


class PlatformTenantListView(APIView):
    """
    Platform tenant management endpoint.
    """
    permission_classes = [IsPlatformAdmin]

    @extend_schema(
        tags=["Platform"],
        summary="List all tenants",
        description="""
List all tenants in the system with filtering and pagination.

### Permission Required
- `platform_admin` realm role OR Django superuser

### Query Parameters
- `is_active` - Filter by active status (true/false)
- `search` - Search by name, slug, or email
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
""",
        parameters=[
            OpenApiParameter(name="is_active", type=bool, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
        ],
        responses={
            200: OpenApiExample(
                "Paginated Response",
                value={
                    "count": 50,
                    "page": 1,
                    "page_size": 20,
                    "results": [{"id": 1, "name": "Tenant", "slug": "tenant"}]
                },
                response_only=True,
            )
        },
    )
    def get(self, request):
        """List all tenants with optional filtering."""
        tenants = Tenant.objects.all().order_by('-created_at')

        # Optional filters
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            tenants = tenants.filter(is_active=is_active.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            tenants = tenants.filter(
                Q(name__icontains=search) |
                Q(slug__icontains=search) |
                Q(email__icontains=search)
            )

        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size

        total = tenants.count()
        tenants = tenants[offset:offset + page_size]

        serializer = PlatformTenantSerializer(tenants, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data
        })


class PlatformTenantDetailView(APIView):
    """
    Platform tenant detail and management endpoint.
    """
    permission_classes = [IsPlatformAdmin]

    @extend_schema(
        tags=["Platform"],
        summary="Get tenant details",
        description="Retrieve detailed tenant information. Requires platform admin permission.",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
        ],
        responses={200: PlatformTenantSerializer},
    )
    def get(self, request, slug):
        """Get detailed tenant information."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlatformTenantSerializer(tenant)
        return Response(serializer.data)

    @extend_schema(
        tags=["Platform"],
        summary="Update tenant (admin)",
        description="""
Update tenant fields as a platform administrator.

Platform admins can update any tenant field without ownership restrictions.

### Updatable Fields
- `name`
- `description`
- `email`
- `url`
- `is_active`
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
        ],
        responses={200: PlatformTenantSerializer},
    )
    def patch(self, request, slug):
        """Update tenant (platform admin can update any field)."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Platform admins can update any field
        allowed_fields = ['name', 'description', 'email', 'url', 'is_active']
        for field in allowed_fields:
            if field in request.data:
                setattr(tenant, field, request.data[field])

        tenant.save()
        serializer = PlatformTenantSerializer(tenant)
        return Response(serializer.data)

    @extend_schema(
        tags=["Platform"],
        summary="Deactivate tenant (admin)",
        description="""
Soft-delete a tenant by marking it as inactive.

Platform admins can deactivate any tenant regardless of ownership.
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
        ],
        responses={204: None},
    )
    def delete(self, request, slug):
        """Deactivate tenant (soft delete)."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        tenant.is_active = False
        tenant.save(update_fields=['is_active'])

        return Response(status=status.HTTP_204_NO_CONTENT)
