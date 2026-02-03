# Complete Authentication Flow

This document describes the end-to-end authentication flow from frontend to backend, including all components involved.

## Overview

```
┌─────────────┐      ┌──────────┐      ┌─────────┐      ┌────────┐
│   Browser   │◄────►│ Next.js  │◄────►│ Django  │◄────►│Keycloak│
│  (Frontend) │      │ Frontend │      │ Backend │      │  (IDP) │
└─────────────┘      └──────────┘      └─────────┘      └────────┘
```

## Initial Page Load (Unauthenticated User)

### Step 1: App Initialization

**Location:** `src/app/[lng]/layout.tsx`

```typescript
<Providers>
  <AuthBootstrap>
    {children}
  </AuthBootstrap>
</Providers>
```

**What Happens:**
1. Redux store is created with initial state
2. `AuthBootstrap` component mounts
3. `useAuthBootstrap` hook runs

---

### Step 2: Keycloak Initialization

**Location:** `src/features/auth/hooks/useAuthBootstrap.ts`

```typescript
const keycloak = getKeycloak() // Get singleton instance

if ((keycloak as any).adapter) {
  // Already initialized (React Strict Mode second mount)
  setReady(true)
  return
}

await keycloak.init({
  onLoad: 'check-sso',    // Check if user has session
  pkceMethod: 'S256',     // Security: PKCE flow
  checkLoginIframe: false // Disabled for Next.js
})
```

**What Happens:**
1. Check browser localStorage for existing tokens
2. If tokens exist and valid → authenticated = true
3. If no tokens or expired → authenticated = false
4. Set up Keycloak adapter (enables login/logout methods)
5. Update Redux state: `authReady(authenticated)`

**Network Activity:**
- GET `http://keycloak.theddt.local/realms/theddt/.well-known/openid-configuration`
- GET `http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/certs` (JWKS)

---

### Step 3: UI Renders Based on Auth State

**Location:** `src/components/LogoutButton.tsx`

```typescript
if (!isAuthenticated) {
  return <button onClick={handleLogin}>Login</button>
}

return <button onClick={handleLogout}>Logout</button>
```

**What User Sees:**
- "Loading..." (during initialization)
- "Login" button (if not authenticated)
- Main app content (if authenticated)

---

## Login Flow

### Step 4: User Clicks Login Button

**Location:** `src/components/LogoutButton.tsx`

```typescript
const handleLogin = async () => {
  await keycloak.login({
    redirectUri: window.location.origin
  })
}
```

**What Happens:**
1. Keycloak generates:
   - `state`: Random string for CSRF protection
   - `nonce`: Random string for replay protection
   - `code_challenge`: PKCE code challenge (SHA256 hash)
   - `code_verifier`: Stored in sessionStorage for later use

2. Browser redirects to Keycloak login page:
   ```
   http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/auth?
     client_id=wiwebb-web-client&
     redirect_uri=http://localhost:3000&
     state=56693728-ed44-4955-9467-11c83b0e1bba&
     response_mode=fragment&
     response_type=code&
     scope=openid&
     nonce=b26e1add-8050-4329-b00c-2a00d663b49a&
     code_challenge=SABi2mYQ9A8JfiwPByk2pQw3-6FmqY705gEDeSDgUIY&
     code_challenge_method=S256
   ```

---

### Step 5: User Enters Credentials

**Location:** Keycloak login page

**What Happens:**
1. User enters username and password
2. Keycloak validates credentials
3. Keycloak checks user exists and is enabled
4. If valid, Keycloak generates authorization code

---

### Step 6: Redirect Back to App

**What Happens:**
1. Keycloak redirects back to app:
   ```
   http://localhost:3000/#
     state=56693728-ed44-4955-9467-11c83b0e1bba&
     session_state=abc123...&
     code=def456...
   ```

2. Keycloak.js intercepts the redirect
3. Validates `state` matches (CSRF protection)
4. Extracts authorization code from URL

---

### Step 7: Token Exchange

**Location:** Keycloak.js library (automatic)

**What Happens:**
1. Keycloak.js makes POST request to Keycloak:
   ```
   POST http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&
   code=def456...&
   redirect_uri=http://localhost:3000&
   client_id=wiwebb-web-client&
   code_verifier=<original_code_verifier>
   ```

2. Keycloak validates:
   - Authorization code is valid and not expired
   - `code_verifier` matches the `code_challenge` (PKCE)
   - `redirect_uri` matches registered URI

3. Keycloak responds with tokens:
   ```json
   {
     "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "expires_in": 300,
     "refresh_expires_in": 1800,
     "token_type": "Bearer"
   }
   ```

4. Keycloak.js stores tokens in localStorage:
   - `kc-token-<realm>`
   - `kc-refresh-token-<realm>`

5. Updates state: `keycloak.authenticated = true`

---

### Step 8: Fetch User Profile

**Location:** `src/features/auth/api/authApi.ts`

**Automatic RTK Query Request:**
```typescript
const { data: user } = useGetMeQuery(undefined, {
  skip: !isAuthenticated
})
```

**What Happens:**
1. RTK Query prepares request
2. `prepareHeaders` hook runs:
   ```typescript
   prepareHeaders: async (headers) => {
     if (keycloak.authenticated && keycloak.token) {
       // Refresh token if expires in < 5 minutes
       await keycloak.updateToken(300)

       // Add Authorization header
       headers.set('Authorization', `Bearer ${keycloak.token}`)
     }
     return headers
   }
   ```

3. Fetch request sent:
   ```
   GET http://api.theddt.local/api/v1/auth/me/
   Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   Origin: http://localhost:3000
   ```

---

### Step 9: Django Validates JWT

**Location:** `apps/identity/authentication.py`

**Django Middleware Pipeline:**
```
Request → CORS Middleware → DRF Authentication → View
```

**Authentication Process:**
```python
class KeycloakJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # 1. Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = auth_header.replace('Bearer ', '')

        # 2. Get public key from JWKS (cached)
        public_key = self.get_public_key(token)

        # 3. Validate JWT signature
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            issuer=settings.KEYCLOAK_ISSUER,
            audience=settings.KEYCLOAK_AUDIENCE,
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_iat': True,
                'verify_aud': True,
            }
        )

        # 4. Extract user info from token
        keycloak_id = payload['sub']
        email = payload.get('email', '')
        username = payload.get('preferred_username', '')
        first_name = payload.get('given_name', '')
        last_name = payload.get('family_name', '')

        # 5. Get or create Django user
        user, created = User.objects.get_or_create(
            keycloak_id=keycloak_id,
            defaults={
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        # 6. Update user if already exists
        if not created:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()

        # 7. Return authenticated user
        return (user, None)
```

**What JWT Contains:**
```json
{
  "exp": 1738584542,
  "iat": 1738584242,
  "jti": "abc123...",
  "iss": "http://keycloak.theddt.local/realms/theddt",
  "aud": ["account"],
  "sub": "209bfb3c-bd5b-418e-848e-5fab20cbdd47",
  "typ": "Bearer",
  "azp": "wiwebb-web-client",
  "email": "demo@example.com",
  "email_verified": true,
  "preferred_username": "demo",
  "given_name": "Demo",
  "family_name": "User",
  "realm_access": {
    "roles": ["default-roles-theddt", "offline_access", "uma_authorization"]
  }
}
```

---

### Step 10: Django Returns User Profile

**Response:**
```json
{
  "id": 2,
  "keycloak_id": "209bfb3c-bd5b-418e-848e-5fab20cbdd47",
  "username": "demo",
  "email": "demo@example.com",
  "first_name": "Demo",
  "last_name": "User",
  "phone_number": "",
  "bio": "",
  "company": "",
  "location": "",
  "is_superuser": false,
  "date_joined": "2026-02-03T09:08:55.016184+00:00",
  "realm_roles": [
    "default-roles-theddt",
    "offline_access",
    "uma_authorization"
  ],
  "tenant_memberships": [],
  "subscriber_profile": null
}
```

**CORS Headers:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
```

---

### Step 11: Update Redux State

**Location:** RTK Query automatic cache update

```typescript
// RTK Query automatically:
// 1. Caches response
// 2. Updates all components using the hook
// 3. Sets loading state to false

// Redux state after update:
{
  auth: {
    status: 'ready',
    isAuthenticated: true,
    profileLoaded: true,
    user: { /* user data */ }
  }
}
```

---

### Step 12: UI Renders Authenticated State

**What User Sees:**
- Profile information displays
- "Logout" button instead of "Login"
- Protected routes become accessible
- User-specific content loads

---

## Subsequent API Requests

### Token Refresh Flow

**Before Each Request:**
```typescript
// services/api/baseApi.ts
prepareHeaders: async (headers) => {
  if (keycloak.authenticated && keycloak.token) {
    // Check if token expires in next 5 minutes (300 seconds)
    await keycloak.updateToken(300)

    // Add refreshed token to request
    headers.set('Authorization', `Bearer ${keycloak.token}`)
  }
  return headers
}
```

**What `updateToken(300)` Does:**
1. Check token expiration time
2. If expires in < 300 seconds:
   - POST to Keycloak token endpoint
   - Send refresh token
   - Get new access token
   - Update localStorage
   - Return new token
3. If still valid:
   - Return existing token

**Token Refresh Request:**
```
POST http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=<refresh_token>&
client_id=wiwebb-web-client
```

---

## Logout Flow

### Step 13: User Clicks Logout

**Location:** `src/components/LogoutButton.tsx`

```typescript
const handleLogout = () => {
  // 1. Clear Redux state
  dispatch(clearUser())
  dispatch(authReset())

  // 2. Clear RTK Query cache
  dispatch(baseApi.util.resetApiState())

  // 3. Logout from Keycloak
  keycloak.logout({
    redirectUri: window.location.origin
  })
}
```

**What Happens:**
1. Redux state reset to initial values
2. All cached API data cleared
3. Redirect to Keycloak logout endpoint:
   ```
   http://keycloak.theddt.local/realms/theddt/protocol/openid-connect/logout?
     redirect_uri=http://localhost:3000
   ```

4. Keycloak:
   - Invalidates tokens
   - Clears session
   - Removes cookies
   - Redirects back to app

5. App redirects to home page
6. Keycloak.js clears localStorage:
   - Removes access token
   - Removes refresh token
   - Sets `authenticated = false`

7. UI re-renders showing "Login" button

---

## Security Considerations

### PKCE (Proof Key for Code Exchange)

**Why:** Public clients (browser apps) can't securely store secrets. PKCE prevents authorization code interception attacks.

**Flow:**
1. Generate random `code_verifier` (43-128 characters)
2. Create `code_challenge` = BASE64URL(SHA256(code_verifier))
3. Send `code_challenge` in authorization request
4. Store `code_verifier` in sessionStorage
5. Send `code_verifier` in token exchange request
6. Keycloak validates: SHA256(code_verifier) == code_challenge

**Benefit:** Even if authorization code is intercepted, attacker can't exchange it for tokens without the code_verifier.

---

### JWT Signature Validation

**Why:** Ensures token hasn't been tampered with.

**How:**
1. Keycloak signs tokens with private key (RSA)
2. Django fetches public key from JWKS endpoint
3. Django verifies signature using public key
4. If signature invalid, token is rejected

**Benefit:**
- No need to call Keycloak for every request
- Fast local validation
- Keycloak can be temporarily down

---

### Token Expiration

**Access Token:** 5 minutes (short-lived)
- Limits damage if token is stolen
- Requires frequent refresh

**Refresh Token:** 30 minutes
- Used to get new access tokens
- Longer lifetime for better UX
- Can be revoked by Keycloak

**Session:** 30 minutes idle, 10 hours max
- Keycloak tracks session
- Logout invalidates session
- Cross-tab synchronization

---

## Troubleshooting

### Check Authentication State

**Browser Console:**
```javascript
// Check Keycloak state
const kc = window.keycloak
console.log({
  authenticated: kc?.authenticated,
  token: kc?.token?.substring(0, 50),
  tokenParsed: kc?.tokenParsed
})

// Check Redux state
// (Requires Redux DevTools)
console.log(store.getState().auth)
```

### Test API Request

**Browser Console:**
```javascript
const kc = window.keycloak
fetch('http://api.theddt.local/api/v1/auth/me/', {
  credentials: 'include',
  headers: {
    'Authorization': `Bearer ${kc.token}`
  }
})
  .then(r => r.json())
  .then(console.log)
```

### Common Issues

1. **401 Unauthorized:** Token expired or invalid
   - Check token expiration: `kc.tokenParsed.exp`
   - Manually refresh: `kc.updateToken(-1)`

2. **403 Forbidden:** Token valid but insufficient permissions
   - Check roles in token: `kc.tokenParsed.realm_access.roles`

3. **CORS Error:** Frontend/backend configuration mismatch
   - Verify `credentials: 'include'` in frontend
   - Verify CORS config in Django

4. **Infinite Loading:** Keycloak not initializing
   - Check console for errors
   - Verify environment variables
   - Check network tab for failed requests
