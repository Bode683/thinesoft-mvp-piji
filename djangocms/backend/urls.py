from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include


def oauth2_logout(request):
    """
    Logout from Django and redirect to OAuth2-Proxy logout.

    Flow:
    1. Clear Django session (removes CSRF token, session data)
    2. Redirect to OAuth2-Proxy logout endpoint
    3. OAuth2-Proxy clears its cookie and redirects to Keycloak logout
    4. Keycloak ends SSO session
    """
    # CRITICAL: Flush the session to prevent CSRF token reuse
    request.session.flush()

    # Logout the user from Django
    logout(request)

    # Redirect to OAuth2-Proxy logout, which will cascade to Keycloak
    return redirect('http://auth.theddt.local/oauth2/sign_out?rd=/')


urlpatterns = [
    path("admin/", admin.site.urls),
    path("logout/", oauth2_logout, name="logout"),
]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns.append(path("", include("cms.urls")))

# the new django admin sidebar is bad UX in django CMS custom admin views.
admin.site.enable_nav_sidebar = False
