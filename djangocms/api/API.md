# API Documentation

This document describes the Tenant + User management API, roles/permissions model, and audit logging.

## Overview

- Role is the single source of truth for privileges.
- `is_staff` and `is_superuser` are derived from `role` in `User.save()` and cannot be edited through the API.
- Multitenant scoping:
  - SuperAdmin/Platform Admin: full visibility.
  - TenantOwner: scoped to own tenant.
  - Subscriber: no management privileges by default.
- Sensitive actions (role changes, password resets, activation changes) are audited via `AuditLog`.

## Authentication

- Standard Django auth (extended base user).
- All endpoints below require authentication unless otherwise noted.

## Endpoints

Base path: `/api/`

### Tenants
- GET `/tenants/` — list (SuperAdmin/Platform Admin)
- POST `/tenants/` — create (SuperAdmin/Platform Admin)
- GET `/tenants/{id}/` — retrieve (SuperAdmin/Platform Admin; TenantOwner for own tenant)
- PUT/PATCH `/tenants/{id}/` — update (SuperAdmin/Platform Admin; TenantOwner for own tenant)
- DELETE `/tenants/{id}/` — destroy (SuperAdmin/Platform Admin)
- GET `/tenants/me/` — current tenant for TenantOwner
- PATCH `/tenants/me/` — update own tenant (TenantOwner)

Tenant fields (serializer):
- id, uuid, name, slug, is_active, description, email, url, created_at, updated_at

### Users
- GET `/users/` — list
  - SuperAdmin/Admin: all users
  - TenantOwner: users within own tenant
- POST `/users/` — create
  - SuperAdmin/Admin: any user
  - TenantOwner: user within own tenant only; cannot create Admin/SuperAdmin
- GET `/users/{id}/` — retrieve (scoped per above)
- PUT/PATCH `/users/{id}/` — update (scoped per above)
- DELETE `/users/{id}/` — delete (policy-dependent; currently not limited for SuperAdmin/Admin; TenantOwner limited to own tenant)
- POST `/users/{id}/assign-role/` — set the user’s role
- POST `/users/{id}/set-password/` — set the user’s password
- POST `/users/{id}/activate/` — activate/deactivate user

User read fields (`UserSerializer`):
- id, username, email, first_name, last_name, is_active, is_staff, is_superuser,
  last_login, date_joined, role, tenant (mini), phone_number, bio, url, company,
  location, birth_date, password_updated

User write fields (`UserWriteSerializer`):
- username, email, first_name, last_name, role, tenant, phone_number, bio, url,
  company, location, birth_date, is_active

Note: `is_staff` and `is_superuser` are not writable and are derived from `role`.

### Action payloads

- Assign role
  - POST `/users/{id}/assign-role/`
  - Body: `{ "role": "tenant_owner" }`
- Set password
  - POST `/users/{id}/set-password/`
  - Body: `{ "new_password1": "S3cret", "new_password2": "S3cret" }`
- Activate/deactivate
  - POST `/users/{id}/activate/`
  - Body: `{ "is_active": true }`

## Roles and derived flags

The `User.save()` method enforces these mappings:
- SUPERADMIN → `is_staff=True`, `is_superuser=True`
- ADMIN → `is_staff=True`, `is_superuser=False`
- TENANT_OWNER / SUBSCRIBER → `is_staff=False`, `is_superuser=False`

These flags update automatically when a user’s `role` changes.

## Authorization matrix (summary)

- SuperAdmin
  - Full CRUD on tenants and users.
  - Can assign any role.
- Platform Admin (is_staff in Admin group)
  - Full CRUD on tenants and users.
  - Cannot assign SuperAdmin role.
- TenantOwner
  - Scoped to own tenant.
  - Can list/create/update users in own tenant.
  - Cannot assign Admin/SuperAdmin.
- Subscriber
  - No management permissions by default.

Role-assignment rules are centralized in `api/utils.py: can_assign_role()` and are reused by serializers and views.

## Audit logging

Model: `api.models.AuditLog`
- actor (nullable, when not known)
- target (user affected)
- action: one of `role_changed`, `password_reset`, `activation_changed`
- details: human-readable description
- timestamp: auto

Creation points:
- In views (`UserViewSet.assign_role`, `set_password`, `activate`) with the currently authenticated user as actor.
- In signals (`pre_save` + `post_save` of `User`) with `actor=None` when changes happen outside these view actions.

## Response examples

- Assign role
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -b cookiejar \
  http://localhost:8000/api/users/42/assign-role/ \
  -d '{"role": "tenant_owner"}'
```

- Set password
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -b cookiejar \
  http://localhost:8000/api/users/42/set-password/ \
  -d '{"new_password1":"S3cret", "new_password2":"S3cret"}'
```

- Activate
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -b cookiejar \
  http://localhost:8000/api/users/42/activate/ \
  -d '{"is_active": true}'
```

## Setup and migration

- Install dependencies and run migrations:
```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
```

- Create a superuser for initial access:
```bash
python manage.py createsuperuser
```

## Notes

- Default Django groups are maintained in signals for convenience (Admin, TenantOwner, Subscriber). SuperAdmin does not require a managed group.
