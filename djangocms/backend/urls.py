from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from api import urls as api_urls
from payment_gateway import urls as payment_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("dj_rest_auth.urls")),  # <-- Add this
    path(
        "api/v1/auth/registration/", include("dj_rest_auth.registration.urls")
    ),  # <-- Add this for registration
    path("api/v1/", include("api.urls")),
    path("api/v1/", include("payment_gateway.urls")),
    path("djstripe/", include("djstripe.urls", namespace="djstripe")),
]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns.append(path("", include("cms.urls")))

# the new django admin sidebar is bad UX in django CMS custom admin views.
admin.site.enable_nav_sidebar = False
