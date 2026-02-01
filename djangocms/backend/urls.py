"""
Root URL configuration.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    # Admin (standard Django admin with username/password)
    path("admin/", admin.site.urls),

    # OpenAPI Schema - always available (for CI/CD, client generation)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # API v1 endpoints (JWT authentication only)
    path("api/v1/auth/", include("apps.identity.urls", namespace="identity")),
    path("api/v1/tenants/", include("apps.tenants.urls", namespace="tenants")),
    path("api/v1/subscribers/", include("apps.subscribers.urls", namespace="subscribers")),
    path("api/v1/platform/", include("apps.platform.urls", namespace="platform")),
]

# API Documentation UI
if settings.DEBUG:
    # In development, Swagger UI is publicly accessible
    urlpatterns.extend([
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ])
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
else:
    # In production, protect Swagger UI with platform admin permission
    from rest_framework.decorators import api_view, permission_classes
    from apps.platform.permissions import IsPlatformAdmin

    @api_view(["GET"])
    @permission_classes([IsPlatformAdmin])
    def protected_swagger_view(request):
        return SpectacularSwaggerView.as_view(url_name="schema")(request)

    @api_view(["GET"])
    @permission_classes([IsPlatformAdmin])
    def protected_redoc_view(request):
        return SpectacularRedocView.as_view(url_name="schema")(request)

    urlpatterns.extend([
        path("api/docs/", protected_swagger_view, name="swagger-ui"),
        path("api/redoc/", protected_redoc_view, name="redoc"),
    ])

# CMS URLs (catch-all, must be last)
urlpatterns.append(path("", include("cms.urls")))

# Disable the new Django admin sidebar (bad UX in django CMS custom admin views)
admin.site.enable_nav_sidebar = False
