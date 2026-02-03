# Authentication Troubleshooting History

This document chronicles all authentication issues encountered during development, the debugging process, and solutions that worked.

## Issue 1: 403 Forbidden with drf-keycloak-auth

### Symptoms
- Frontend sends requests with valid Bearer token
- Django returns 403 Forbidden
- Error: "Authentication credentials were not provided"

### Investigation Steps

1. **Verified token was being sent:**
   ```bash
   curl -X GET "http://api.theddt.local/api/v1/auth/me/" \
     -H "Authorization: Bearer <token>"
   # Result: 403 Forbidden
   ```

2. **Checked Keycloak introspection endpoint:**
   ```bash
   curl -X POST "http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/token/introspect" \
     -d "token=<token>" \
     -d "client_id=wiwebb-web-client"
   # Result: {"active": false}
   ```

### Root Cause
The `drf-keycloak-auth` library was using token introspection, which requires the token to be validated by Keycloak. The introspection was returning `active: false` for valid tokens, causing authentication to fail.

### Attempted Fixes
1. ❌ Tried different Keycloak client settings
2. ❌ Verified token format and claims
3. ❌ Checked network connectivity to Keycloak

### Solution
**Migrated from token introspection to JWT signature validation:**

1. Removed `drf-keycloak-auth` dependency
2. Installed `PyJWT` and `cryptography`
3. Created custom `KeycloakJWTAuthentication` class in `apps/identity/authentication.py`
4. Configured to fetch public keys from Keycloak JWKS endpoint
5. Validate JWT signatures locally without network calls

**Result:** ✅ Authentication now works with JWT signature validation

---

## Issue 2: JWT Verification - Invalid Issuer

### Symptoms
After implementing PyJWT authentication:
- JWT signature validation passed
- Error: "Token has invalid issuer"
- Expected: `http://keycloak:8080/realms/theddt`
- Got: `http://keycloak.theddt.local/realms/theddt`

### Investigation Steps

1. **Decoded JWT token to inspect claims:**
   ```bash
   TOKEN_PAYLOAD=$(echo $TOKEN | cut -d'.' -f2)
   echo $TOKEN_PAYLOAD | base64 -d | jq .
   ```
   Result showed: `"iss": "http://keycloak.theddt.local/realms/theddt"`

2. **Checked Django configuration:**
   - `KEYCLOAK_SERVER_URL` was set to `http://keycloak:8080`
   - Code was using this URL as expected issuer

### Root Cause
- Django runs inside Docker network and accesses Keycloak via internal DNS (`keycloak:8080`)
- Keycloak issues tokens with its **public URL** in the `iss` claim (`http://keycloak.theddt.local`)
- JWT validation requires the `iss` claim to match the expected issuer exactly

### Solution
**Separated internal and public Keycloak URLs:**

1. Created two environment variables:
   - `KEYCLOAK_SERVER_URL=http://keycloak:8080` (for fetching JWKS)
   - `KEYCLOAK_ISSUER=http://keycloak.theddt.local/realms/theddt` (for JWT validation)

2. Updated `docker-compose.yml`:
   ```yaml
   environment:
     - KEYCLOAK_SERVER_URL=http://keycloak:8080
     - KEYCLOAK_ISSUER=http://keycloak.theddt.local/realms/theddt
   ```

3. Updated authentication code to use correct URL for each purpose

**Result:** ✅ Issuer validation now passes

---

## Issue 3: JWT Verification - Invalid Audience

### Symptoms
After fixing issuer issue:
- JWT signature validation passed
- Issuer validation passed
- Error: "Token has invalid audience"
- Expected audience: `wiwebb-web-client`
- Token audience: `["account"]`

### Investigation Steps

1. **Inspected JWT token claims:**
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.aud'
   # Result: ["account"]
   ```

2. **Checked Keycloak client configuration:**
   - Client ID: `wiwebb-web-client`
   - Access Type: `public`
   - Expected `aud` to contain client ID

3. **Researched Keycloak documentation:**
   - Found that public clients use `"account"` as default audience
   - Confidential clients can have custom audiences
   - This is standard Keycloak behavior

### Root Cause
Keycloak's default behavior for **public clients** (browser-based applications) is to set the audience to `"account"` rather than the client ID. This is by design for security reasons.

### Solution
**Changed expected audience from client ID to "account":**

1. Updated `backend/settings/base.py`:
   ```python
   KEYCLOAK_AUDIENCE = os.environ.get("KEYCLOAK_AUDIENCE", "account")
   ```

2. Updated authentication class to validate against `"account"` audience

**Result:** ✅ JWT validation fully working - 200 OK responses with user profile data

---

## Issue 4: CORS Error from Frontend

### Symptoms
After Django backend was working:
- curl tests with Authorization header worked fine
- Frontend requests failed with CORS error:
  ```
  Access to fetch at 'http://api.theddt.local/api/v1/auth/me' from origin
  'http://localhost:3000' has been blocked by CORS policy: No
  'Access-Control-Allow-Origin' header is present on the requested resource
  ```

### Investigation Steps

1. **Verified CORS configuration in Django:**
   ```python
   CORS_ALLOW_ALL_ORIGINS = True
   CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
   CORS_ALLOW_CREDENTIALS = True
   ```

2. **Tested CORS with curl (simulating browser):**
   ```bash
   # Preflight request
   curl -X OPTIONS "http://api.theddt.local/api/v1/auth/me/" \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -v

   # Result: ✅ All CORS headers present
   # - Access-Control-Allow-Origin: http://localhost:3000
   # - Access-Control-Allow-Credentials: true
   # - Access-Control-Allow-Headers: authorization
   ```

3. **Tested actual GET request:**
   ```bash
   curl -X GET "http://api.theddt.local/api/v1/auth/me/" \
     -H "Origin: http://localhost:3000" \
     -H "Authorization: Bearer $TOKEN" \
     -v

   # Result: ✅ CORS headers present
   ```

### Root Cause
CORS was configured correctly on the backend. The issue was on the **frontend** - RTK Query was not sending `credentials: 'include'` with requests.

When `CORS_ALLOW_CREDENTIALS = True` on the backend, the frontend **must** send credentials with the request. Otherwise, the browser blocks the response even if CORS headers are present.

### Solution
See frontend documentation (`/wiwebb-web/docs/`) for the frontend fix.

**Backend verification showed:** ✅ Django CORS correctly configured

---

## Testing Commands

### Test JWT token acquisition:
```bash
TOKEN=$(curl -s -X POST "http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=wiwebb-web-client" \
  -d "username=demo" \
  -d "password=password" | jq -r '.access_token')

echo "Token acquired: ${TOKEN:0:50}..."
```

### Test authenticated endpoint:
```bash
curl -X GET "http://api.theddt.local/api/v1/auth/me/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq .
```

### Test CORS preflight:
```bash
curl -X OPTIONS "http://api.theddt.local/api/v1/auth/me/" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization" \
  -v 2>&1 | grep -E "< HTTP|< Access-Control"
```

### Decode JWT token:
```bash
# Payload (claims)
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .

# Check specific claims
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '{iss, aud, exp, sub}'
```

## Key Learnings

1. **Token introspection adds latency** - JWT signature validation is faster and more scalable
2. **Docker networking requires URL separation** - Internal vs public URLs must be handled separately
3. **Keycloak public clients use "account" audience** - Not the client ID
4. **CORS credentials require frontend cooperation** - Both sides must be configured correctly
5. **Always inspect actual JWT claims** - Don't assume what's in the token, verify it
