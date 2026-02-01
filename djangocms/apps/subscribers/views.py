"""
Subscriber views.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from apps.common.exceptions import TenantNotFoundException, SubscriberNotFoundException
from apps.tenants.models import Tenant
from apps.tenants import selectors as tenant_selectors
from .models import Subscriber
from .permissions import IsActiveSubscriber
from .serializers import (
    SubscriberSerializer,
    SubscriberDetailSerializer,
    CreateSubscriberSerializer,
    UpdateSubscriberSerializer,
    ExtendSubscriptionSerializer,
)
from . import selectors, services

User = get_user_model()


class MySubscriberView(APIView):
    """
    Own subscriber profile endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Subscribers"],
        summary="Get own subscriber profile",
        description="""
Retrieve the authenticated user's subscriber profile.

**Note:** Subscriber is a business entity, not an auth role.

Returns subscriber details including:
- RADIUS username
- Active status
- Expiration date
- Usage limits (data, time)
- Associated tenant

### Authentication Required
JWT bearer token from Keycloak.
""",
        responses={
            200: SubscriberSerializer,
            404: OpenApiExample(
                "No Subscriber Profile",
                value={"detail": "You do not have a subscriber profile."},
                response_only=True,
            ),
        },
    )
    def get(self, request):
        """Get the current user's subscriber profile."""
        subscriber = selectors.get_subscriber_by_user(request.user)

        if not subscriber:
            return Response(
                {"detail": "You do not have a subscriber profile."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubscriberSerializer(subscriber)
        return Response(serializer.data)


class TenantSubscriberListView(APIView):
    """
    Tenant subscriber management endpoints.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant(self, slug):
        tenant = tenant_selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()
        return tenant

    @extend_schema(
        tags=["Subscribers"],
        summary="List tenant subscribers",
        description="""
List all subscribers within a tenant.

### Permission Required
- Tenant admin or owner

### Query Parameters
- `active_only` - Filter to only active subscribers (default: false)
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(
                name="active_only",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter to only active subscribers",
                required=False,
            ),
        ],
        responses={200: SubscriberDetailSerializer(many=True)},
    )
    def get(self, request, slug):
        """List all subscribers of the tenant (admin only)."""
        tenant = self.get_tenant(slug)

        # Check admin permission
        if not request.user.is_superuser:
            if not tenant_selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can view subscribers."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Get query parameters
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'

        subscribers = selectors.get_tenant_subscribers(tenant, active_only=active_only)
        serializer = SubscriberDetailSerializer(subscribers, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Subscribers"],
        summary="Create subscriber",
        description="""
Create a new subscriber within the tenant.

### Permission Required
- Tenant admin or owner

### Request Parameters
Provide either `user_id` or `email`:
- `user_id` or `email` - Identify the user
- `radius_username` - Optional RADIUS username (auto-generated if not provided)
- `data_limit_mb` - Data usage limit in MB
- `time_limit_minutes` - Time usage limit in minutes
- `expires_at` - Specific expiration date (optional)
- `expires_in_days` - Days until expiration (alternative to expires_at)
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
        ],
        request=CreateSubscriberSerializer,
        responses={
            201: SubscriberDetailSerializer,
            400: OpenApiExample(
                "Already Has Profile",
                value={"detail": "User already has a subscriber profile."},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Create Subscriber",
                value={
                    "email": "subscriber@example.com",
                    "data_limit_mb": 1024,
                    "time_limit_minutes": 60,
                    "expires_in_days": 30,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request, slug):
        """Create a subscriber in the tenant (admin only)."""
        tenant = self.get_tenant(slug)

        # Check admin permission
        if not request.user.is_superuser:
            if not tenant_selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can create subscribers."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = CreateSubscriberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find user by id or email
        user_id = serializer.validated_data.get('user_id')
        email = serializer.validated_data.get('email')

        if user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            user = get_object_or_404(User, email=email)

        # Check if user already has a subscriber profile
        if selectors.user_is_subscriber(user):
            return Response(
                {"detail": "User already has a subscriber profile."},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscriber = services.create_subscriber(
            user=user,
            tenant=tenant,
            requesting_user=request.user,
            radius_username=serializer.validated_data.get('radius_username'),
            data_limit_mb=serializer.validated_data.get('data_limit_mb'),
            time_limit_minutes=serializer.validated_data.get('time_limit_minutes'),
            expires_at=serializer.validated_data.get('expires_at'),
            expires_in_days=serializer.validated_data.get('expires_in_days'),
        )

        return Response(
            SubscriberDetailSerializer(subscriber).data,
            status=status.HTTP_201_CREATED
        )


class TenantSubscriberDetailView(APIView):
    """
    Subscriber detail and management endpoints.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant_and_subscriber(self, slug, subscriber_id):
        tenant = tenant_selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()

        subscriber = Subscriber.objects.filter(
            id=subscriber_id,
            tenant=tenant
        ).select_related('user', 'tenant').first()

        return tenant, subscriber

    @extend_schema(
        tags=["Subscribers"],
        summary="Get subscriber details",
        description="Retrieve detailed subscriber information. Requires tenant admin permission.",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="subscriber_id", type=int, location=OpenApiParameter.PATH),
        ],
        responses={200: SubscriberDetailSerializer},
    )
    def get(self, request, slug, subscriber_id):
        """Get subscriber details (admin only)."""
        tenant, subscriber = self.get_tenant_and_subscriber(slug, subscriber_id)

        if not subscriber:
            raise SubscriberNotFoundException()

        # Check admin permission
        if not request.user.is_superuser:
            if not tenant_selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can view subscriber details."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = SubscriberDetailSerializer(subscriber)
        return Response(serializer.data)

    @extend_schema(
        tags=["Subscribers"],
        summary="Update subscriber",
        description="Update subscriber limits and settings. Requires tenant admin permission.",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="subscriber_id", type=int, location=OpenApiParameter.PATH),
        ],
        request=UpdateSubscriberSerializer,
        responses={200: SubscriberDetailSerializer},
    )
    def patch(self, request, slug, subscriber_id):
        """Update subscriber details (admin only)."""
        tenant, subscriber = self.get_tenant_and_subscriber(slug, subscriber_id)

        if not subscriber:
            raise SubscriberNotFoundException()

        # Check admin permission
        if not request.user.is_superuser:
            if not tenant_selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can update subscribers."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = UpdateSubscriberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscriber = services.update_subscriber(
            subscriber=subscriber,
            requesting_user=request.user,
            **serializer.validated_data
        )

        return Response(SubscriberDetailSerializer(subscriber).data)

    @extend_schema(
        tags=["Subscribers"],
        summary="Delete subscriber",
        description="Permanently delete a subscriber profile. Requires tenant admin permission.",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="subscriber_id", type=int, location=OpenApiParameter.PATH),
        ],
        responses={204: None},
    )
    def delete(self, request, slug, subscriber_id):
        """Delete subscriber (admin only)."""
        tenant, subscriber = self.get_tenant_and_subscriber(slug, subscriber_id)

        if not subscriber:
            raise SubscriberNotFoundException()

        services.delete_subscriber(subscriber, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ExtendSubscriptionView(APIView):
    """
    Extend subscription expiration endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Subscribers"],
        summary="Extend subscription",
        description="""
Extend a subscriber's expiration date by a specified number of days.

### Permission Required
- Tenant admin or owner

### Business Rules
- Adds days to current `expires_at` date
- If already expired, extends from current time
""",
        parameters=[
            OpenApiParameter(name="slug", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="subscriber_id", type=int, location=OpenApiParameter.PATH),
        ],
        request=ExtendSubscriptionSerializer,
        responses={200: SubscriberDetailSerializer},
        examples=[
            OpenApiExample(
                "Extend by 30 days",
                value={"days": 30},
                request_only=True,
            )
        ],
    )
    def post(self, request, slug, subscriber_id):
        """Extend subscriber's expiration date (admin only)."""
        tenant = tenant_selectors.get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundException()

        subscriber = Subscriber.objects.filter(
            id=subscriber_id,
            tenant=tenant
        ).first()

        if not subscriber:
            raise SubscriberNotFoundException()

        # Check admin permission
        if not request.user.is_superuser:
            if not tenant_selectors.user_is_tenant_admin(request.user, tenant):
                return Response(
                    {"detail": "Only tenant admins can extend subscriptions."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = ExtendSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscriber = services.extend_subscription(
            subscriber=subscriber,
            requesting_user=request.user,
            days=serializer.validated_data['days']
        )

        return Response(SubscriberDetailSerializer(subscriber).data)
