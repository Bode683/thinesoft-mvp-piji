# Authentication Architecture (Frontend)

## Overview

The Next.js frontend uses Keycloak for authentication via OAuth2/OIDC flow, with Redux Toolkit for state management and RTK Query for API calls.

## Architecture Decision: Redux Toolkit + RTK Query

### Decision
We use Redux Toolkit (RTK) for global state management and RTK Query for API calls.

### Rationale

**Redux Toolkit Benefits:**
- Centralized state management across the application
- Predictable state updates with actions and reducers
- DevTools for debugging state changes
- Persistence support for UI preferences

**RTK Query Benefits:**
- Automatic caching of API responses
- Request deduplication (multiple components requesting same data = 1 network call)
- Automatic refetching and cache invalidation
- Built-in loading and error states
- Optimistic updates support

**State Structure:**
```typescript
{
  auth: {
    status: 'idle' | 'loading' | 'ready' | 'error',
    isAuthenticated: boolean,
    profileLoaded: boolean,
    user: User | null
  },
  ui: {
    darkMode: boolean
  }
}
```

### Files
- `src/lib/store/store.ts` - Redux store configuration
- `src/features/auth/slice/authSlice.ts` - Auth state slice
- `src/features/ui/slice/uiSlice.ts` - UI state slice

---

## Architecture Decision: Keycloak-js for Authentication

### Decision
We use the official `keycloak-js` client library for OAuth2/OIDC authentication flow.

### Rationale

**Why Keycloak-js:**
- Official Keycloak JavaScript client
- Handles OAuth2/OIDC flow automatically
- Token refresh management
- Cross-tab session synchronization
- Battle-tested in production environments

**Why Not NextAuth.js:**
- NextAuth.js adds unnecessary server-side complexity
- We already have a Django backend handling auth
- Keycloak-js works purely client-side
- Direct integration with Keycloak features

**Configuration:**
```typescript
// lib/keycloak/keycloak.ts
const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL,
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM,
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID,
})
```

**Environment Variables:**
```bash
NEXT_PUBLIC_KEYCLOAK_URL=http://keycloak.theddt.local
NEXT_PUBLIC_KEYCLOAK_REALM=theddt
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=wiwebb-web-client
```

---

## Architecture Decision: Singleton Keycloak Instance

### Decision
We create a single Keycloak instance that is reused across the application.

### Rationale

**Why Singleton:**
- Keycloak maintains internal state (tokens, session)
- Multiple instances would cause sync issues
- `keycloak.init()` can only be called once per instance
- Browser storage (localStorage) is shared

**Implementation:**
```typescript
// lib/keycloak/keycloak.ts
let keycloakInstance: Keycloak | null = null

export function getKeycloak(): Keycloak {
  if (!keycloakInstance) {
    keycloakInstance = new Keycloak({...config})
  }
  return keycloakInstance
}
```

**Critical for React Strict Mode:**
React Strict Mode in development mounts components twice. A singleton ensures both mounts use the same Keycloak instance.

---

## Architecture Decision: Separation of Keycloak and Redux State

### Decision
Keycloak state (auth tokens, session) is separate from Redux state (user profile, auth status).

### Rationale

**Keycloak Handles:**
- OAuth2/OIDC flow
- Token storage (localStorage)
- Token refresh
- Session management

**Redux Handles:**
- Application auth state (`loading`, `ready`, `error`)
- User profile data from Django API
- UI state and preferences

**Why Separate:**
- Clear separation of concerns
- Keycloak state is managed by Keycloak library
- Redux state is application-specific
- Easier to test and debug
- Can swap auth providers without changing app state logic

**Integration Point:**
```typescript
// features/auth/hooks/useAuthBootstrap.ts
// 1. Initialize Keycloak
// 2. Update Redux state based on Keycloak auth status
// 3. Fetch user profile from Django if authenticated
```

---

## Architecture Decision: RTK Query with Credentials

### Decision
RTK Query's `fetchBaseQuery` is configured with `credentials: 'include'`.

### Rationale

**Why credentials: 'include':**
```typescript
// services/api/baseApi.ts
baseQuery: fetchBaseQuery({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  credentials: 'include', // ← Required for CORS
  prepareHeaders: async (headers) => {
    // Add Authorization header with Keycloak token
  }
})
```

**The Requirement:**
- Django backend sends `Access-Control-Allow-Credentials: true`
- When this header is present, browsers enforce stricter CORS rules
- Frontend **must** send `credentials: 'include'` or request will be blocked
- Even though we use Authorization header (not cookies), this is still required

**What credentials: 'include' does:**
- Sends cookies cross-origin
- Sends Authorization headers cross-origin
- Tells browser to include credentials in request
- Required when backend allows credentials

---

## Architecture Decision: Token Management

### Decision
Keycloak tokens are automatically refreshed by the `keycloak-js` library and injected into API requests.

### Implementation

**Token Refresh:**
```typescript
// services/api/baseApi.ts
prepareHeaders: async (headers) => {
  if (keycloak.authenticated && keycloak.token) {
    // Refresh token if it expires in the next 5 minutes
    await keycloak.updateToken(300)

    // Add fresh token to request
    if (keycloak.token) {
      headers.set('Authorization', `Bearer ${keycloak.token}`)
    }
  }
  return headers
}
```

**How it Works:**
1. Before each API request, `prepareHeaders` is called
2. Check if token expires soon (within 5 minutes)
3. If yes, call `keycloak.updateToken(300)` to refresh
4. Keycloak uses refresh token to get new access token
5. Add fresh access token to Authorization header
6. Request proceeds with valid token

**Benefits:**
- Automatic token refresh
- No manual token management
- Tokens always fresh
- Seamless user experience

---

## Authentication Flow

```
1. User visits app
   ↓
2. AuthBootstrap initializes Keycloak
   - Calls keycloak.init({ onLoad: 'check-sso' })
   - Checks if user has existing session
   ↓
3a. Not Authenticated:
   - Show Login button
   - User clicks Login
   - Redirect to Keycloak login page
   - User enters credentials
   - Redirect back to app with auth code
   - Keycloak exchanges code for tokens

3b. Already Authenticated:
   - Keycloak loads tokens from localStorage
   - Skip login page
   ↓
4. Fetch user profile from Django API
   - RTK Query adds Authorization header with token
   - Django validates JWT and returns user data
   ↓
5. Update Redux state
   - authReady(true)
   - setUser(userData)
   ↓
6. App renders authenticated UI
```

## Component Structure

```
App
├── AuthBootstrap (Keycloak initialization)
│   ├── KeycloakContext.Provider (provides keycloak instance)
│   └── Children (app content)
│       ├── LogoutButton (uses keycloak.login/logout)
│       └── ProtectedRoutes (checks auth state)
```

**Key Components:**

1. **AuthBootstrap** (`src/features/auth/components/AuthBootstrap.tsx`)
   - Initializes Keycloak on app load
   - Shows loading screen during initialization
   - Shows error screen if initialization fails
   - Provides Keycloak instance via context

2. **useAuthBootstrap** (`src/features/auth/hooks/useAuthBootstrap.ts`)
   - Hook that handles Keycloak initialization
   - Updates Redux auth state
   - Handles React Strict Mode double-mount

3. **KeycloakContext** (`src/lib/keycloak/KeycloakContext.tsx`)
   - React context providing Keycloak instance
   - Makes keycloak available to all components
   - Tracks initialization status

4. **LogoutButton** (`src/components/LogoutButton.tsx`)
   - Shows Login button when not authenticated
   - Shows Logout button when authenticated
   - Calls keycloak.login() or keycloak.logout()

## Files Structure

```
src/
├── lib/
│   ├── store/
│   │   ├── store.ts                    # Redux store
│   │   └── hooks.ts                    # Typed hooks
│   └── keycloak/
│       ├── keycloak.ts                 # Keycloak singleton
│       └── KeycloakContext.tsx         # Context provider
├── features/
│   ├── auth/
│   │   ├── slice/
│   │   │   └── authSlice.ts            # Auth state
│   │   ├── hooks/
│   │   │   └── useAuthBootstrap.ts     # Init hook
│   │   ├── components/
│   │   │   └── AuthBootstrap.tsx       # Init component
│   │   └── api/
│   │       └── authApi.ts              # RTK Query endpoints
│   └── ui/
│       └── slice/
│           └── uiSlice.ts              # UI state
├── services/
│   └── api/
│       └── baseApi.ts                  # RTK Query config
└── components/
    └── LogoutButton.tsx                # Login/Logout
```

## Environment Variables

```bash
# Keycloak Configuration
NEXT_PUBLIC_KEYCLOAK_URL=http://keycloak.theddt.local
NEXT_PUBLIC_KEYCLOAK_REALM=theddt
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=wiwebb-web-client

# Django API
NEXT_PUBLIC_API_URL=http://api.theddt.local/api/v1
```

**Note:** All variables are prefixed with `NEXT_PUBLIC_` because they are used in browser-side code.

## Security Considerations

1. **Public Client Configuration:**
   - Keycloak client is configured as "public"
   - No client secret (would be exposed in browser)
   - Uses PKCE (Proof Key for Code Exchange) for security

2. **Token Storage:**
   - Tokens stored in browser localStorage by Keycloak
   - Vulnerable to XSS attacks
   - Mitigated by: CSP headers, token expiration, refresh tokens

3. **CORS:**
   - Only configured origins can make API requests
   - Credentials must be explicitly included
   - Pre-flight requests verify permissions

4. **Token Expiration:**
   - Access tokens expire in ~5 minutes
   - Refresh tokens used to get new access tokens
   - Automatic refresh before expiration
