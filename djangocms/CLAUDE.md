# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django CMS application with **Keycloak SSO integration** and **multi-tenant architecture**. The codebase implements a clean separation between:
- **Django Admin Dashboard**: Standard username/password authentication (for staff/superusers)
- **REST API**: JWT-only authentication via Keycloak tokens
- **Multi-tenancy**: Organization-based access control with tenant-scoped roles

## Architecture Principles

### Authentication & Authorization Model

**Critical Design Decision**: This system uses a **dual authentication strategy**:

1. **Keycloak (via JWT)** = Source of truth for:
   - User identity (`keycloak_id` from `sub` claim)
   - **Platform-level authority ONLY**: `platform_admin` realm role

2. **Django Database** = Source of truth for:
   - **Tenant-scoped roles**: `TenantMembership.role` (owner/admin/member)
   - **Business state**: `Subscriber` model (NOT an auth role)

**Never mix these concerns**: Platform roles come from JWT claims, tenant roles come from database models.

### Domain-Driven Structure

```
apps/
├── identity/       # Auth infrastructure (NOT business logic)
│   ├── models.py           # User model (lean: only keycloak_id, no role field)
│   ├── auth_context.py     # AuthContext dataclass (attached to request)
│   ├── authentication.py   # KeycloakJWTAuthentication (extracts roles from JWT)
│   └── keycloak.py         # JWKSCache helper
│
├── tenants/        # Multi-tenant domain
│   ├── models.py           # Tenant, TenantMembership (THIS is where tenant auth lives)
│   ├── selectors.py        # Read-only queries
│   ├── services.py         # Business rules (create_tenant, add_member, etc.)
│   └── permissions.py      # IsTenantOwner, IsTenantAdmin (check TenantMembership)
│
├── subscribers/    # Subscriber lifecycle (business state, not auth)
│   ├── models.py           # Subscriber (is_active, expires_at)
│   ├── services.py         # create_subscriber, extend_subscription
│   └── permissions.py      # IsActiveSubscriber (checks model state)
│
├── platform/       # Platform admin (cross-tenant)
│   ├── permissions.py      # IsPlatformAdmin (ONLY permission checking realm roles)
│   └── views.py            # Stats, user management across tenants
│
└── common/         # Shared utilities
    ├── models.py           # TimeStampedModel base
    └── exceptions.py       # API exceptions
```

### Service Layer Pattern

**Always use this pattern for business logic**:

```python
# selectors.py - Read-only queries (no side effects)
def get_user_membership(user, tenant):
    return TenantMembership.objects.filter(user=user, tenant=tenant).first()

# services.py - Business rules with side effects
@transaction.atomic
def create_tenant(name: str, owner_user, **kwargs):
    tenant = Tenant.objects.create(name=name, **kwargs)
    TenantMembership.objects.create(user=owner_user, tenant=tenant, role='owner')
    return tenant
```

**Never put business logic directly in views** - views should orchestrate selectors and services.

## Development Commands

### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (for Django admin)
python manage.py createsuperuser
```

### Running the Application

```bash
# Development server
python manage.py runserver

# With Docker Compose (from parent directory)
cd /home/nkem/Desktop/itlds/mvp
docker compose up djangocms --build
```

### Database Operations

```bash
# Create migrations for specific apps
python manage.py makemigrations identity tenants subscribers

# Show migration SQL
python manage.py sqlmigrate tenants 0001

# Reset database (DANGEROUS)
python manage.py flush

# Shell with Django models loaded
python manage.py shell
```

### Testing & Debugging

```bash
# Run Django tests
python manage.py test apps.tenants
python manage.py test apps.identity.tests.test_auth

# Django shell for manual testing
python manage.py shell_plus  # if django-extensions installed

# Check for issues
python manage.py check
```

### Settings Environment

The project uses a **settings package** (not a single file):

```python
# backend/settings/
#   __init__.py    # Auto-selects dev/prod based on DJANGO_ENV
#   base.py        # Shared settings
#   dev.py         # Development overrides
#   prod.py        # Production settings
```

**To switch environments**:
```bash
export DJANGO_ENV=prod  # Uses backend.settings.prod
export DJANGO_ENV=dev   # Uses backend.settings.dev (default)
```

## Critical Implementation Rules

### 1. User Model

**User model is LEAN** - no role field:

```python
# ✅ CORRECT
class User(AbstractUser):
    keycloak_id = models.UUIDField(...)  # From JWT 'sub' claim
    phone_number = models.CharField(...)  # Profile fields only
    # NO role field
    # NO tenant FK
```

**Roles come from**:
- `request.auth_context.realm_roles` (platform-level, from JWT)
- `TenantMembership.role` (tenant-scoped, from database)

### 2. Permission Classes

**Platform Admin (realm role check)**:
```python
from apps.platform.permissions import IsPlatformAdmin

class CreateTenantView(APIView):
    permission_classes = [IsPlatformAdmin]  # Checks JWT realm role
```

**Tenant Admin (database check)**:
```python
from apps.tenants.permissions import IsTenantAdmin

class AddMemberView(APIView):
    permission_classes = [IsTenantAdmin]  # Checks TenantMembership

    def post(self, request, slug):
        tenant = get_tenant_by_slug(slug)
        # Permission class already verified user is admin of THIS tenant
```

### 3. API Authentication

**REST Framework uses JWT ONLY**:

```python
# backend/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.identity.authentication.KeycloakJWTAuthentication",
        # NO SessionAuthentication - JWT only
    ],
}
```

**Django Admin uses standard authentication** (username/password, ModelBackend).

### 4. Subscriber is Business State

**Subscriber is NOT an auth role**:

```python
# ❌ WRONG - Don't check realm roles or TenantMembership
if request.auth_context.has_realm_role('subscriber'):  # NO!

# ✅ CORRECT - Check model existence and state
from apps.subscribers.permissions import IsActiveSubscriber

class SubscriberOnlyView(APIView):
    permission_classes = [IsActiveSubscriber]  # Checks Subscriber.is_valid
```

### 5. AuthContext Usage

**AuthContext is attached to request by KeycloakJWTAuthentication**:

```python
def get(self, request):
    # Available in views after JWT authentication
    if hasattr(request, 'auth_context'):
        user_keycloak_id = request.auth_context.keycloak_id
        is_platform_admin = request.auth_context.is_platform_admin()
        realm_roles = request.auth_context.realm_roles
```

## API Endpoint Patterns

### Tenant-Scoped Endpoints

```
GET    /api/tenants/{slug}/members/              # List members (check: IsTenantMember)
POST   /api/tenants/{slug}/members/              # Add member (check: IsTenantAdmin)
PATCH  /api/tenants/{slug}/members/{id}/         # Update role (check: IsTenantOwner)
GET    /api/tenants/{slug}/subscribers/          # List subscribers (check: IsTenantAdmin)
POST   /api/tenants/{slug}/subscribers/          # Create subscriber (check: IsTenantAdmin)
```

### Platform-Scoped Endpoints

```
GET    /api/platform/stats/                      # Platform stats (check: IsPlatformAdmin)
GET    /api/platform/users/                      # All users (check: IsPlatformAdmin)
POST   /api/tenants/                             # Create tenant (check: IsPlatformAdmin)
```

### User-Scoped Endpoints

```
GET    /api/auth/me/                             # Current user + tenants + roles
GET    /api/subscribers/me/                      # Own subscriber profile
```

## Keycloak Configuration

### Realm Roles (Keycloak)

**Only ONE realm role should exist**:
- `platform_admin` - Cross-tenant administrator

**Do NOT create these in Keycloak** (they belong in Django):
- ~~`tenant_owner`~~ (use TenantMembership.role = 'owner')
- ~~`subscriber`~~ (use Subscriber model existence)

### JWT Token Structure

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "preferred_username": "john@example.com",
  "email": "john@example.com",
  "given_name": "John",
  "family_name": "Doe",
  "realm_access": {
    "roles": ["platform_admin"]
  },
  "resource_access": {
    "djangocms-client": {
      "roles": []
    }
  }
}
```

## Common Gotchas

### 1. Don't Use SessionAuthentication for API

```python
# ❌ WRONG
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.identity.authentication.KeycloakJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # NO!
    ],
}

# ✅ CORRECT - JWT only
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.identity.authentication.KeycloakJWTAuthentication",
    ],
}
```

### 2. Don't Store Roles in User Model

```python
# ❌ WRONG
class User(AbstractUser):
    role = models.CharField(choices=ROLE_CHOICES)  # NO!

# ✅ CORRECT - Roles come from TenantMembership
membership = TenantMembership.objects.get(user=user, tenant=tenant)
is_admin = membership.role in ['owner', 'admin']
```

### 3. Don't Mix Platform and Tenant Permissions

```python
# ❌ WRONG - Checking realm role for tenant-scoped action
if request.auth_context.has_realm_role('admin'):  # NO!
    # Add member to tenant

# ✅ CORRECT - Check TenantMembership
if user_is_tenant_admin(request.user, tenant):
    # Add member to tenant
```

### 4. Always Use Services for Business Logic

```python
# ❌ WRONG - Business logic in views
def post(self, request):
    tenant = Tenant.objects.create(name=request.data['name'])
    TenantMembership.objects.create(user=request.user, tenant=tenant)

# ✅ CORRECT - Use service layer
from apps.tenants import services

def post(self, request):
    tenant = services.create_tenant(
        name=request.data['name'],
        owner_user=request.user
    )
```

## File Naming Conventions

- `selectors.py` - Read-only queries (returns QuerySets or model instances)
- `services.py` - Business logic with side effects (creates, updates, deletes)
- `permissions.py` - DRF permission classes
- `serializers.py` - DRF serializers
- `views.py` - API views (orchestrates selectors and services)
- `urls.py` - URL routing
- `admin.py` - Django admin configuration
- `models.py` - Django models

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Django
DEBUG=True
SECRET_KEY=<secret>
DJANGO_ENV=dev  # or 'prod'

# Database
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=django_db
SQL_USER=django_user
SQL_PASSWORD=<password>
SQL_HOST=django_db
SQL_PORT=5432

# Keycloak
KEYCLOAK_SERVER_URL=http://keycloak:8080
KEYCLOAK_REALM=theddt
KEYCLOAK_CLIENT_ID=djangocms-client
KEYCLOAK_CLIENT_SECRET=<secret>
```

## Custom User Model

**AUTH_USER_MODEL is set in base.py**:

```python
AUTH_USER_MODEL = "identity.User"
```

**All migrations referencing User must use**:

```python
from django.conf import settings

user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

## Docker Integration

This project runs in a Docker Compose stack with:
- **djangocms**: This Django application
- **django_db**: PostgreSQL database
- **keycloak**: Keycloak SSO server
- **traefik**: Reverse proxy
- **oauth2-proxy**: OAuth2 proxy (not used for API auth)

Docker Compose is located in the parent directory: `/home/nkem/Desktop/itlds/mvp/docker-compose.yml`
