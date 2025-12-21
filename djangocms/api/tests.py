from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib import admin
from rest_framework.test import APIClient
from rest_framework import status
from django.test import override_settings

from .models import User, Tenant, Todo


class AuthFlowTests(TestCase):
    """Covers registration, login, logout, and user details via dj-rest-auth."""

    def setUp(self):
        self.client = APIClient()
        # Common endpoints (using explicit paths to avoid name mismatch)
        self.login_url = "/api/v1/auth/login/"
        self.logout_url = "/api/v1/auth/logout/"
        self.user_url = "/api/v1/auth/user/"
        self.register_url = "/api/v1/auth/registration/"

    def test_registration_and_login_flow(self):
        # Register a user
        payload = {
            "username": "jane",
            "email": "jane@example.com",
            "password1": "S3curePass!123",
            "password2": "S3curePass!123",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        r = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
        self.assertTrue(User.objects.filter(username="jane").exists())

        # Login to get token
        r = self.client.post(self.login_url, {"username": "jane", "password": "S3curePass!123"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.assertIn("key", r.data)
        token = r.data["key"]

        # Access user details
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        r = self.client.get(self.user_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["username"], "jane")
        # Update editable fields
        r = self.client.patch(self.user_url, {"first_name": "Janet", "bio": "Hi"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Fetch fresh data to avoid serializer response differences across versions
        r = self.client.get(self.user_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data.get("first_name"), "Janet")
        if "bio" in r.data:
            self.assertEqual(r.data["bio"], "Hi")

        # Logout revokes token
        r = self.client.post(self.logout_url)
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_205_RESET_CONTENT))

        # Token should no longer authenticate
        r = self.client.get(self.user_url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_requires_valid_credentials(self):
        User.objects.create_user(username="mark", email="mark@example.com", password="BadPass!123")
        r = self.client.post(self.login_url, {"username": "mark", "password": "wrong"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class ProtectedEndpointsTests(TestCase):
    """Verify token-authenticated access and basic behavior of protected endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.todo_list_url = "/api/v1/"
        # Create a user and token via login
        self.user = User.objects.create_user(username="amy", email="amy@example.com", password="Pa$$w0rd!xyz")
        # Login to obtain token
        login = self.client.post("/api/v1/auth/login/", {"username": "amy", "password": "Pa$$w0rd!xyz"}, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK, login.content)
        self.token = login.data["key"]

    def test_unauthenticated_is_401(self):
        r = self.client.get(self.todo_list_url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_list_own_todos(self):
        # Seed two todos for this user, one for someone else
        Todo.objects.create(task="t1", user=self.user)
        Todo.objects.create(task="t2", user=self.user, completed=True)
        other = User.objects.create_user(username="bob", password="S0mething!")
        Todo.objects.create(task="t3", user=other)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        r = self.client.get(self.todo_list_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)
        self.assertEqual({t["task"] for t in r.data}, {"t1", "t2"})


class RoleAndPermissionsTests(TestCase):
    """Covers role-based access for TenantViewSet and UserViewSet, including Admin group logic."""

    def setUp(self):
        self.client = APIClient()
        # Ensure Admin group exists
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        # Tenants
        self.t1 = Tenant.objects.create(name="Alpha", slug="alpha")
        self.t2 = Tenant.objects.create(name="Beta", slug="beta")

        # SuperAdmin
        self.superuser = User.objects.create_user(username="super", password="Root!234", role=User.Roles.SUPERADMIN)
        # Role save() syncs flags
        self.superuser.save()

        # Platform Admin (staff + in Admin group)
        self.platform_admin = User.objects.create_user(username="plat", password="Plat!234", role=User.Roles.ADMIN)
        self.platform_admin.groups.add(self.admin_group)
        self.platform_admin.save()

        # Tenant Owner for t1
        self.owner_t1 = User.objects.create_user(
            username="owner1", password="Owner!234", role=User.Roles.TENANT_OWNER, tenant=self.t1
        )
        # Subscriber
        self.subscriber = User.objects.create_user(username="sub", password="Sub!234", role=User.Roles.SUBSCRIBER)

    def _login_token(self, user):
        r = self.client.post(
            "/api/v1/auth/login/", {"username": user.username, "password": "Root!234" if user.username=="super" else (
                "Plat!234" if user.username=="plat" else ("Owner!234" if user.username=="owner1" else "Sub!234")
            )}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {r.data['key']}")

    def test_tenant_list_permissions(self):
        # SuperAdmin can list
        self._login_token(self.superuser)
        r = self.client.get("/api/v1/tenants/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # Platform Admin can list
        self.client = APIClient()
        self._login_token(self.platform_admin)
        r = self.client.get("/api/v1/tenants/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # Tenant Owner cannot list (permission guarded in get_permissions -> IsSuperAdminOrPlatformAdmin)
        self.client = APIClient()
        self._login_token(self.owner_t1)
        r = self.client.get("/api/v1/tenants/")
        self.assertIn(r.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

        # Subscriber cannot list
        self.client = APIClient()
        self._login_token(self.subscriber)
        r = self.client.get("/api/v1/tenants/")
        self.assertIn(r.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_tenant_me_endpoint_for_owner(self):
        self._login_token(self.owner_t1)
        r = self.client.get("/api/v1/tenants/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["id"], self.t1.id)

    def test_user_viewset_queryset_restrictions(self):
        # Create extra users in both tenants
        u1 = User.objects.create_user(username="t1_u", password="x", tenant=self.t1)
        u2 = User.objects.create_user(username="t2_u", password="x", tenant=self.t2)

        # SuperAdmin sees all
        self._login_token(self.superuser)
        r = self.client.get("/api/v1/users/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data), 4)

        # Tenant owner sees only own-tenant users
        self.client = APIClient()
        self._login_token(self.owner_t1)
        r = self.client.get("/api/v1/users/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        usernames = {u["username"] for u in r.data}
        self.assertIn("owner1", usernames)
        self.assertIn("t1_u", usernames)
        self.assertNotIn("t2_u", usernames)

        # Subscriber cannot access (permission denied by CanManageTenantUsers)
        self.client = APIClient()
        self._login_token(self.subscriber)
        r = self.client.get("/api/v1/users/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(STORAGES={
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    }
})
class AdminPanelTests(TestCase):
    """Basic admin login and access tests."""

    def setUp(self):
        # Superuser
        self.superuser = User.objects.create_user(username="root", password="Root!123", role=User.Roles.SUPERADMIN)
        self.superuser.save()
        # Non-staff user
        self.user = User.objects.create_user(username="norm", password="Norm!123", role=User.Roles.SUBSCRIBER)

    def test_admin_access_for_superuser(self):
        # Use Django client (session auth) for admin
        from django.test import Client

        c = Client()
        logged_in = c.login(username="root", password="Root!123")
        self.assertTrue(logged_in)
        r = c.get("/admin/")
        self.assertEqual(r.status_code, 200)
        # Admin index contains site header
        self.assertIn(b"site administration", r.content.lower())

    def test_admin_redirect_for_non_staff(self):
        from django.test import Client

        c = Client()
        logged_in = c.login(username="norm", password="Norm!123")
        self.assertTrue(logged_in)
        r = c.get("/admin/", follow=False)
        # Non-staff users are redirected to admin login
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"]) 
