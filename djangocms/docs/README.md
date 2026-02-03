# Django Backend Documentation

## Authentication Documentation

This directory contains comprehensive documentation about the authentication system implementation.

### Documents

1. **[authentication-architecture.md](./authentication-architecture.md)**
   - Architectural decisions and rationale
   - Why we chose PyJWT over drf-keycloak-auth
   - Internal vs public Keycloak URL separation
   - JWT audience configuration ("account" vs client_id)
   - CORS configuration
   - List of modified files

2. **[authentication-troubleshooting.md](./authentication-troubleshooting.md)**
   - Complete history of issues encountered
   - Debugging process for each issue
   - Solutions that worked (and what didn't)
   - Testing commands for verification
   - Key learnings

### Quick Reference

#### Testing Authentication

```bash
# Get JWT token
TOKEN=$(curl -s -X POST "http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=wiwebb-web-client" \
  -d "username=demo" \
  -d "password=password" | jq -r '.access_token')

# Test authenticated endpoint
curl -X GET "http://api.theddt.local/api/v1/auth/me/" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Decode JWT token
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .
```

#### Key Configuration

**Environment Variables (docker-compose.yml):**
```yaml
environment:
  - KEYCLOAK_SERVER_URL=http://keycloak:8080
  - KEYCLOAK_ISSUER=http://keycloak.theddt.local/realms/theddt
  - KEYCLOAK_AUDIENCE=account
```

**Django Settings (backend/settings/base.py):**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.identity.authentication.KeycloakJWTAuthentication',
    ]
}

KEYCLOAK_SERVER_URL = os.environ.get("KEYCLOAK_SERVER_URL", "http://keycloak:8080")
KEYCLOAK_ISSUER = os.environ.get("KEYCLOAK_ISSUER", "http://keycloak.theddt.local/realms/theddt")
KEYCLOAK_AUDIENCE = os.environ.get("KEYCLOAK_AUDIENCE", "account")
```

#### Important Files

- `apps/identity/authentication.py` - JWT authentication class
- `backend/settings/base.py` - Authentication configuration
- `requirements.txt` - PyJWT dependencies

#### Common Issues

See [authentication-troubleshooting.md](./authentication-troubleshooting.md) for detailed solutions to:
- 403 Forbidden errors
- JWT validation failures (invalid issuer/audience)
- CORS errors
- Token introspection issues

### Getting Help

1. Check the troubleshooting guide first
2. Verify environment variables are set correctly
3. Test with curl commands to isolate frontend vs backend issues
4. Check Django logs: `docker-compose logs web`
5. Inspect actual JWT token claims to verify configuration
