# Authentication Architecture

## Overview

The Django backend uses JWT (JSON Web Token) authentication with Keycloak as the identity provider. This document describes the architectural decisions made and the rationale behind them.

## Architecture Decision: PyJWT over drf-keycloak-auth

### Decision
We use `PyJWT` for JWT signature validation instead of `drf-keycloak-auth` which uses token introspection.

### Rationale

**Token Introspection (drf-keycloak-auth) Issues:**
- Makes a network call to Keycloak's introspection endpoint for EVERY request
- Adds latency (100-300ms per request)
- Creates a tight coupling with Keycloak availability
- Scale concerns: High request volume = High introspection requests

**JWT Signature Validation (PyJWT) Benefits:**
- No network call needed - validation happens locally
- Fast verification using public key from JWKS endpoint
- Public keys are cached and only refreshed when needed
- Works even if Keycloak is temporarily unavailable (using cached keys)
- Industry-standard approach used by most production systems

### Implementation

**Dependencies:**
```python
PyJWT==2.10.1
cryptography==44.0.0
requests==2.32.3
```

**Authentication Class:**
```python
# apps/identity/authentication.py
class KeycloakJWTAuthentication(BaseAuthentication)
```

**Key Features:**
1. Fetches Keycloak's JWKS (public keys) on startup
2. Validates JWT signature using public key
3. Verifies issuer, audience, and expiration
4. Creates or updates Django user from token claims
5. Extracts realm roles from JWT

## Architecture Decision: Separate Internal and Public Keycloak URLs

### Decision
We maintain two separate Keycloak URLs:
- `KEYCLOAK_SERVER_URL`: Internal Docker network URL (`http://keycloak:8080`)
- `KEYCLOAK_ISSUER`: Public URL in JWT tokens (`http://keycloak.theddt.local/realms/theddt`)

### Rationale

**The Problem:**
- Django runs inside Docker network and must access Keycloak via internal DNS (`keycloak:8080`)
- JWT tokens are issued by Keycloak with a public URL in the `iss` claim
- The issuer URL in the token must match what we validate against
- If we use the internal URL for validation, tokens appear invalid

**The Solution:**
- `KEYCLOAK_SERVER_URL`: Used to fetch JWKS (public keys) from Keycloak
- `KEYCLOAK_ISSUER`: Used to validate the `iss` claim in JWT tokens

**Configuration:**
```python
# backend/settings/base.py
KEYCLOAK_SERVER_URL = os.environ.get("KEYCLOAK_SERVER_URL", "http://keycloak:8080")
KEYCLOAK_ISSUER = os.environ.get("KEYCLOAK_ISSUER", "http://keycloak.theddt.local/realms/theddt")
```

**docker-compose.yml:**
```yaml
environment:
  - KEYCLOAK_SERVER_URL=http://keycloak:8080
  - KEYCLOAK_ISSUER=http://keycloak.theddt.local/realms/theddt
```

## Architecture Decision: JWT Audience is "account"

### Decision
We validate JWT tokens with audience set to `"account"` instead of the client ID.

### Rationale

**The Problem:**
- Initially expected `aud` claim to contain the client ID (`wiwebb-web-client`)
- JWT validation was failing with "Invalid audience" error
- Inspecting actual tokens showed `aud: ["account"]`

**Keycloak Behavior:**
- For **public clients** (browser-based apps), Keycloak uses `"account"` as the default audience
- For **confidential clients** (server-to-server), Keycloak can use client ID as audience
- This is standard Keycloak behavior and documented in their architecture

**Configuration:**
```python
# backend/settings/base.py
KEYCLOAK_AUDIENCE = os.environ.get("KEYCLOAK_AUDIENCE", "account")
```

## Authentication Flow

```
1. Frontend obtains JWT token from Keycloak (OAuth2/OIDC flow)
2. Frontend includes token in Authorization header: "Bearer <token>"
3. Django receives request with token
4. KeycloakJWTAuthentication validates:
   - JWT signature using cached public key
   - Issuer matches KEYCLOAK_ISSUER
   - Audience contains "account"
   - Token hasn't expired
5. If valid:
   - Extract user info from token (sub, email, name, roles)
   - Get or create Django User with keycloak_id = sub
   - Attach user to request.user
6. View processes authenticated request
```

## CORS Configuration

### Decision
Allow credentials and configure specific origins.

### Configuration

```python
# backend/settings/base.py
CORS_ALLOW_ALL_ORIGINS = True  # Development only
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://api.theddt.local",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    # ... other headers
]
```

**Why CORS_ALLOW_CREDENTIALS = True:**
- Required when frontend uses `credentials: 'include'`
- Allows cookies and authorization headers to be sent cross-origin
- Browser enforces stricter CORS checks when this is enabled

## Files Modified

### New Files
- `apps/identity/authentication.py` - JWT authentication class

### Modified Files
- `backend/settings/base.py` - Authentication configuration
- `requirements.txt` - Added PyJWT dependencies

### Removed Files
- `apps/identity/keycloak.py` - Old introspection-based auth

### Configuration
- `docker-compose.yml` - Added KEYCLOAK_SERVER_URL and KEYCLOAK_ISSUER environment variables
