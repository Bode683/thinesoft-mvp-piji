# Frontend Documentation

## Authentication Documentation

This directory contains comprehensive documentation about the frontend authentication implementation.

### Documents

1. **[authentication-architecture.md](./authentication-architecture.md)**
   - Architectural decisions and rationale
   - Why Redux Toolkit + RTK Query
   - Why Keycloak-js (not NextAuth.js)
   - Singleton Keycloak instance pattern
   - Separation of Keycloak and Redux state
   - RTK Query with credentials: 'include'
   - Token refresh strategy
   - Component structure
   - Files structure

2. **[authentication-troubleshooting.md](./authentication-troubleshooting.md)**
   - Complete history of issues encountered
   - CORS error resolution
   - "Cannot read properties of undefined" login error
   - React Strict Mode double-mount issues
   - Step-by-step debugging process
   - Solutions that worked (and what didn't)
   - Testing strategy with browser DevTools
   - Common debugging commands

3. **[authentication-flow.md](./authentication-flow.md)**
   - End-to-end authentication flow
   - Step-by-step breakdown from page load to authenticated state
   - Login flow with OAuth2/OIDC
   - Token exchange and JWT validation
   - User profile fetching
   - Token refresh mechanism
   - Logout flow
   - Security considerations (PKCE, JWT signatures)
   - Troubleshooting tips

### Quick Reference

#### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_KEYCLOAK_URL=http://keycloak.theddt.local
NEXT_PUBLIC_KEYCLOAK_REALM=theddt
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=wiwebb-web-client
NEXT_PUBLIC_API_URL=http://api.theddt.local/api/v1
```

**Important:** All variables must have `NEXT_PUBLIC_` prefix to be available in the browser.

#### Key Components

```
src/
├── lib/
│   ├── store/store.ts                    # Redux store
│   └── keycloak/
│       ├── keycloak.ts                   # Singleton instance
│       └── KeycloakContext.tsx           # Context provider
├── features/auth/
│   ├── hooks/useAuthBootstrap.ts         # Initialization hook
│   ├── components/AuthBootstrap.tsx      # Initialization component
│   └── api/authApi.ts                    # RTK Query endpoints
├── services/api/baseApi.ts               # RTK Query config
└── components/LogoutButton.tsx           # Login/Logout UI
```

#### Browser Console Debugging

```javascript
// Check Keycloak state
const kc = window.keycloak
console.log({
  authenticated: kc?.authenticated,
  hasAdapter: !!(kc as any)?.adapter,
  token: kc?.token?.substring(0, 50),
  tokenParsed: kc?.tokenParsed
})

// Check Redux state (requires Redux DevTools)
console.log(store.getState().auth)

// Test API call manually
fetch('http://api.theddt.local/api/v1/auth/me/', {
  credentials: 'include',
  headers: {
    'Authorization': `Bearer ${kc.token}`
  }
})
  .then(r => r.json())
  .then(console.log)
```

#### Common Issues

See [authentication-troubleshooting.md](./authentication-troubleshooting.md) for detailed solutions to:
- CORS errors (missing `credentials: 'include'`)
- Login button errors (Keycloak not initialized)
- React Strict Mode double-mount issues
- Infinite loading screens

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              React Components                     │  │
│  │  ┌────────────────┐  ┌──────────────────────┐   │  │
│  │  │ AuthBootstrap  │  │   LogoutButton       │   │  │
│  │  │ (Initialize)   │  │   (Login/Logout)     │   │  │
│  │  └───────┬────────┘  └──────────┬───────────┘   │  │
│  └──────────┼──────────────────────┼───────────────┘  │
│             │                      │                   │
│  ┌──────────▼──────────────────────▼───────────────┐  │
│  │           Keycloak.js Singleton                  │  │
│  │  - Token storage (localStorage)                 │  │
│  │  - OAuth2/OIDC flow                             │  │
│  │  - Token refresh                                │  │
│  │  - login() / logout() methods                   │  │
│  └──────────┬──────────────────────┬───────────────┘  │
│             │                      │                   │
│  ┌──────────▼──────────┐  ┌────────▼──────────────┐  │
│  │   Redux Store       │  │   RTK Query           │  │
│  │  - Auth state       │  │  - API calls          │  │
│  │  - User profile     │  │  - Token injection    │  │
│  │  - UI state         │  │  - Auto refresh       │  │
│  └─────────────────────┘  └───────┬───────────────┘  │
│                                    │                   │
└────────────────────────────────────┼───────────────────┘
                                     │
                                     │ HTTP + JWT
                                     │
                          ┌──────────▼─────────────┐
                          │   Django Backend       │
                          │  - JWT validation      │
                          │  - User endpoints      │
                          └────────────────────────┘
```

### State Flow

```
App Load
   ↓
Keycloak.init()
   ↓
Check localStorage for tokens
   ↓
   ├─ Tokens found & valid → authenticated = true
   │                         ↓
   │                    Fetch user profile
   │                         ↓
   │                    Update Redux
   │                         ↓
   │                    Render authenticated UI
   │
   └─ No tokens / expired → authenticated = false
                            ↓
                       Show Login button
                            ↓
                       User clicks Login
                            ↓
                       Redirect to Keycloak
                            ↓
                       User enters credentials
                            ↓
                       Redirect back with code
                            ↓
                       Exchange code for tokens
                            ↓
                       Store in localStorage
                            ↓
                       authenticated = true
                            ↓
                       Fetch user profile
                            ↓
                       Update Redux
                            ↓
                       Render authenticated UI
```

### Critical Configuration

#### RTK Query Base Configuration

```typescript
// services/api/baseApi.ts
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    credentials: 'include', // ← CRITICAL for CORS
    prepareHeaders: async (headers) => {
      if (keycloak.authenticated && keycloak.token) {
        // Refresh token if expires in < 5 minutes
        await keycloak.updateToken(300)

        // Add Authorization header
        if (keycloak.token) {
          headers.set('Authorization', `Bearer ${keycloak.token}`)
        }
      }
      return headers
    },
  }),
  tagTypes: ['User', 'Tenant', 'Project'],
  endpoints: () => ({}),
})
```

#### Keycloak Initialization

```typescript
// features/auth/hooks/useAuthBootstrap.ts
useEffect(() => {
  const keycloak = getKeycloak() // Singleton

  // Check if already initialized (React Strict Mode second mount)
  if ((keycloak as any).adapter) {
    dispatch(authReady(!!keycloak.authenticated))
    setReady(true)
    return
  }

  // Initialize
  keycloak
    .init({
      onLoad: 'check-sso',    // Check existing session
      pkceMethod: 'S256',     // Security: PKCE flow
      checkLoginIframe: false // Required for Next.js
    })
    .then((authenticated) => {
      dispatch(authReady(!!authenticated))
      setReady(true)
    })
    .catch((error) => {
      // Handle React Strict Mode double-init
      if (error.message?.includes('only be initialized once')) {
        if ((keycloak as any).adapter) {
          dispatch(authReady(!!keycloak.authenticated))
          setReady(true)
          return
        }
      }
      dispatch(authError())
    })
}, [dispatch])
```

### Key Learnings

1. **CORS requires both backend and frontend configuration:**
   - Backend: `Access-Control-Allow-Credentials: true`
   - Frontend: `credentials: 'include'`

2. **React Strict Mode double-mounts in development:**
   - Use singleton pattern for Keycloak instance
   - Check adapter presence before initializing
   - Handle "already initialized" errors gracefully

3. **Keycloak.init() must be called exactly once:**
   - Adapter is set up by init()
   - Methods like login() depend on adapter
   - Check for adapter to detect initialization status

4. **Token refresh is automatic:**
   - Call `keycloak.updateToken(minValidity)` before API requests
   - Keycloak handles refresh automatically
   - Always use fresh token in Authorization header

### Getting Help

1. Check the troubleshooting guide first: [authentication-troubleshooting.md](./authentication-troubleshooting.md)
2. Review the complete flow: [authentication-flow.md](./authentication-flow.md)
3. Use browser DevTools console to inspect state
4. Check Network tab for failed requests
5. Verify environment variables in browser console
6. Test API calls manually with fetch()

### Running the Frontend

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# App runs on http://localhost:3000
```

### Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build for production (test for build errors)
npm run build
```
