# Authentication Troubleshooting History (Frontend)

This document chronicles all authentication issues encountered during frontend development, the debugging process, and solutions that worked.

## Issue 1: CORS Error - No Access-Control-Allow-Origin Header

### Symptoms
- Django backend API working correctly with curl
- Frontend requests failing with CORS error:
  ```
  Access to fetch at 'http://api.theddt.local/api/v1/auth/me' from origin
  'http://localhost:3000' has been blocked by CORS policy: No
  'Access-Control-Allow-Origin' header is present on the requested resource
  ```

### Investigation Steps

1. **Verified Django CORS configuration:**
   - Checked `CORS_ALLOW_ALL_ORIGINS = True`
   - Checked `CORS_ALLOWED_ORIGINS` included `http://localhost:3000`
   - Checked `CORS_ALLOW_CREDENTIALS = True`
   - All configured correctly ✅

2. **Tested CORS with curl (simulating browser):**
   ```bash
   # Preflight request
   curl -X OPTIONS "http://api.theddt.local/api/v1/auth/me/" \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: authorization" \
     -v

   # Response headers:
   Access-Control-Allow-Origin: http://localhost:3000 ✅
   Access-Control-Allow-Credentials: true ✅
   Access-Control-Allow-Headers: authorization ✅
   ```

3. **Tested actual GET request with curl:**
   ```bash
   curl -X GET "http://api.theddt.local/api/v1/auth/me/" \
     -H "Origin: http://localhost:3000" \
     -H "Authorization: Bearer $TOKEN" \
     -v

   # Response headers:
   Access-Control-Allow-Origin: http://localhost:3000 ✅
   Access-Control-Allow-Credentials: true ✅
   ```

4. **Inspected frontend API configuration:**
   ```typescript
   // services/api/baseApi.ts
   baseQuery: fetchBaseQuery({
     baseUrl: process.env.NEXT_PUBLIC_API_URL,
     // ❌ Missing: credentials: 'include'
     prepareHeaders: async (headers) => {
       // ...
     }
   })
   ```

### Root Cause
When the backend sends `Access-Control-Allow-Credentials: true`, the frontend **must** include credentials in the fetch request. Without `credentials: 'include'`, the browser blocks the response even if all CORS headers are present.

**CORS with credentials requires:**
- Backend: `Access-Control-Allow-Credentials: true` ✅ (was present)
- Frontend: `credentials: 'include'` in fetch ❌ (was missing)

### Solution
**Added credentials: 'include' to RTK Query configuration:**

```typescript
// services/api/baseApi.ts
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    credentials: 'include', // ← Added this line
    prepareHeaders: async (headers) => {
      // Add Authorization header
      if (keycloak.token) {
        headers.set('Authorization', `Bearer ${keycloak.token}`)
      }
      return headers
    },
  }),
  // ...
})
```

**Result:** ✅ CORS errors resolved, API requests succeed

**Key Learning:**
When backend allows credentials (`Access-Control-Allow-Credentials: true`), frontend must send credentials even if only using Authorization header (not cookies).

---

## Issue 2: Login Error - Cannot Read Properties of Undefined

### Symptoms
After fixing CORS:
- Login button appears
- Clicking Login button throws error:
  ```
  Login error: TypeError: Cannot read properties of undefined (reading 'login')
  at keycloak.login
  ```
- No redirect to Keycloak login page

### Investigation Steps

1. **Checked browser console logs:**
   ```
   [useAuthBootstrap] Starting initialization...
   [useAuthBootstrap] Keycloak instance obtained: {exists: true, authenticated: false, hasInit: true}
   [useAuthBootstrap] Keycloak already initialized
   ```

2. **Checked LogoutButton component:**
   ```typescript
   const handleLogin = async () => {
     console.log('Initiating Keycloak login...', {
       keycloakInstance: !!keycloak,
       initialized,
       authenticated: keycloak.authenticated,
       hasLoginMethod: typeof keycloak.login === 'function',
     })

     await keycloak.login({ // ← Error occurs here
       redirectUri: window.location.origin,
     })
   }
   ```

3. **Console output showed:**
   ```
   keycloakInstance: true
   initialized: true
   hasLoginMethod: function  ← login method exists

   Error: Cannot read properties of undefined (reading 'login')
   ```

4. **Inspected Keycloak instance:**
   The error message indicated that the Keycloak adapter was not set up. The `login()` method tries to access `this.adapter.login()`, but `adapter` was undefined.

### Root Cause
The Keycloak instance was created but **never initialized**. The `keycloak.init()` method sets up the adapter, but it was never being called.

**Why init() wasn't called:**
```typescript
// useAuthBootstrap.ts - BUGGY CODE
if (keycloak.authenticated !== undefined) {
  // ❌ BUG: This condition is always true!
  console.log('[useAuthBootstrap] Keycloak already initialized')
  dispatch(authReady(!!keycloak.authenticated))
  setReady(true)
  return // ← Never reaches init()
}

// This code never executes:
await keycloak.init({...})
```

**The Problem:**
- When Keycloak is first created, `keycloak.authenticated` is `false` (not `undefined`)
- The condition `keycloak.authenticated !== undefined` is `true` (because false !== undefined)
- Code assumes Keycloak is already initialized and returns early
- `keycloak.init()` is never called
- Adapter is never set up
- `login()` method fails

### Attempted Fixes

**Attempt 1: Check for adapter instead of authenticated**
```typescript
// Check if adapter exists (adapter is only set after init())
if ((keycloak as any).adapter) {
  console.log('[useAuthBootstrap] Keycloak already initialized')
  dispatch(authReady(!!keycloak.authenticated))
  setReady(true)
  return
}

await keycloak.init({...})
```

**Result:** ❌ Still failing due to React Strict Mode (see Issue 3)

---

## Issue 3: React Strict Mode Double-Mount Preventing Initialization

### Symptoms
After fixing the adapter check:
- App stuck on "Loading..." screen forever
- Console shows initialization attempts but page never progresses
- Console logs:
  ```
  [useAuthBootstrap] Calling keycloak.init()...
  [useAuthBootstrap] Calling keycloak.init()...
  Error: A 'Keycloak' instance can only be initialized once.
  ```

### Investigation Steps

1. **Understood React Strict Mode behavior:**
   - In development, React Strict Mode **deliberately mounts components twice**
   - This helps detect bugs with side effects
   - Effects run: mount → unmount → mount

2. **Traced the execution flow:**
   ```
   First Mount (React Strict Mode):
   1. useEffect runs
   2. Call keycloak.init()
   3. Init starts (async operation)
   4. React unmounts component (Strict Mode)
   5. cancelled = true
   6. Init completes, but !cancelled prevents setState
   7. ready never becomes true

   Second Mount (React Strict Mode):
   1. useEffect runs again
   2. Adapter check passes (from first mount)
   3. Should mark as ready, but...
   4. React unmounts again (Strict Mode)
   5. cancelled = true again
   6. State never updates
   ```

3. **Verified with browser console:**
   ```
   [useAuthBootstrap] Calling keycloak.init()...
   [useAuthBootstrap] Calling keycloak.init()...  ← Called twice
   Keycloak initialization error: Error: A 'Keycloak' instance can only be initialized once.
   ```

4. **Checked adapter status:**
   ```javascript
   // After initialization attempts
   const kc = window.keycloak
   console.log({
     hasAdapter: !!(kc as any).adapter,  // false ❌
     hasLoginMethod: typeof kc.login     // "function" but undefined internally
   })
   ```

### Root Cause
**React Strict Mode double-mount with async initialization:**

1. First mount calls `init()` but gets unmounted before completion
2. Cleanup function sets `cancelled = true`
3. When `init()` completes, the `!cancelled` check prevents setting `ready = true`
4. Second mount tries to call `init()` again
5. Keycloak throws "already initialized" error
6. Error handler runs but also gets cancelled
7. App stuck in loading state forever

**The Core Problem:**
Using a `cancelled` flag with async operations in React Strict Mode doesn't work well because:
- First mount's async operation completes after unmount
- Cancelled flag prevents state updates
- Second mount sees incomplete initialization
- Both mounts get cancelled before completing

### Solution
**Removed cancelled flag and handled double-initialization gracefully:**

```typescript
// features/auth/hooks/useAuthBootstrap.ts
useEffect(() => {
  // Get Keycloak instance (singleton)
  const keycloak = getKeycloak()

  // Check if already initialized (handles second mount)
  if ((keycloak as any).adapter) {
    // Already initialized from first mount
    console.log('[useAuthBootstrap] Keycloak already initialized, using existing instance')
    dispatch(authReady(!!keycloak.authenticated))
    setReady(true)
    return
  }

  // Mark as loading
  dispatch(authLoading())

  // Initialize Keycloak
  console.log('[useAuthBootstrap] Calling keycloak.init()...')
  keycloak
    .init({
      onLoad: 'check-sso',
      pkceMethod: 'S256',
      checkLoginIframe: false,
    })
    .then((authenticated) => {
      console.log('Keycloak initialized:', { authenticated })
      dispatch(authReady(!!authenticated))
      setReady(true)
    })
    .catch((error: any) => {
      // Handle double-initialization from React Strict Mode
      if (error.message?.includes('only be initialized once')) {
        console.warn('[useAuthBootstrap] Keycloak init called twice (React Strict Mode)')
        // The adapter should be set from the first call
        if ((keycloak as any).adapter) {
          dispatch(authReady(!!keycloak.authenticated))
          setReady(true)
          return
        }
      }

      console.error('Keycloak initialization error:', error)
      dispatch(authError())
    })

  // No cleanup function - let the init complete
}, [dispatch])
```

**Key Changes:**
1. ✅ Removed `cancelled` flag - let init complete even after unmount
2. ✅ Check for adapter before calling init (handles second mount)
3. ✅ Catch "already initialized" error gracefully
4. ✅ If error caught and adapter exists, mark as ready
5. ✅ Use Keycloak singleton so both mounts share same instance

**Result:** ✅ Login button appears, clicking redirects to Keycloak successfully

**Why This Works:**
- First mount: Calls `init()`, sets up adapter, completes successfully
- React Strict Mode unmounts and remounts
- Second mount: Sees adapter already exists, skips init, marks as ready immediately
- If both mounts try to init simultaneously, second one catches error but sees adapter from first mount

---

## Issue 4: Browser Console Warning - Keycloak Init Called Twice

### Symptoms
After fixing the double-mount issue, app works but console shows warning:
```
[useAuthBootstrap] Keycloak init called twice (React Strict Mode)
Keycloak initialization error: Error: A 'Keycloak' instance can only be initialized once.
```

### Root Cause
This is **expected behavior** in development due to React Strict Mode:
- React deliberately mounts components twice to detect bugs
- First mount initializes Keycloak successfully
- Second mount tries to initialize but catches the error
- Error is handled gracefully and doesn't break the app

### Solution
**No fix needed.** This warning only appears in development mode:
- Production builds don't use React Strict Mode
- Warning is informational, not an error
- App functions correctly despite the warning
- Could be suppressed but better to see it for debugging

**Key Learning:**
React Strict Mode is intentionally aggressive to help find bugs. Handle double-mount gracefully rather than trying to prevent it.

---

## Testing Strategy

### Browser DevTools Testing

1. **Check Keycloak initialization:**
   ```javascript
   // In browser console
   const kc = window.keycloak || window.__keycloak
   console.log({
     exists: !!kc,
     authenticated: kc?.authenticated,
     hasAdapter: !!kc?.adapter,
     hasToken: !!kc?.token
   })
   ```

2. **Check Redux state:**
   ```javascript
   // In browser console (with Redux DevTools)
   window.__REDUX_DEVTOOLS_EXTENSION__

   // Check auth state
   store.getState().auth
   ```

3. **Monitor console for errors:**
   - Open DevTools → Console tab
   - Filter by "error" or "warn"
   - Look for authentication-related messages

### Automated Browser Testing

We used Playwright via dev-browser skill to:
- Navigate to app
- Wait for initialization
- Capture console logs
- Check for error messages
- Click Login button
- Verify redirect to Keycloak

**Example test script:**
```typescript
import { connect, waitForPageLoad } from "@/client.js";

const client = await connect();
const page = await client.page("auth-test");

// Listen for console errors
page.on('console', msg => console.log(`[${msg.type()}]`, msg.text()));
page.on('pageerror', error => console.log('[ERROR]', error.message));

// Navigate and wait
await page.goto("http://localhost:3000");
await waitForPageLoad(page);
await page.waitForTimeout(5000);

// Check for Login button
const state = await page.evaluate(() => ({
  buttons: Array.from(document.querySelectorAll('button'))
    .map(b => b.textContent?.trim()),
  hasLoginButton: !!document.querySelector('button:text("Login")')
}));

console.log("Buttons found:", state.buttons);
console.log("Has Login:", state.hasLoginButton);

// Click Login
await page.click('button:text("Login")');
await page.waitForTimeout(2000);

// Check if redirected to Keycloak
console.log("URL after click:", page.url());
if (page.url().includes('keycloak')) {
  console.log("✅ SUCCESS! Redirected to Keycloak");
}
```

---

## Common Debugging Commands

### Check environment variables:
```bash
# In the browser console
console.log({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  keycloakUrl: process.env.NEXT_PUBLIC_KEYCLOAK_URL,
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM,
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID
})
```

### Check Keycloak token:
```javascript
// In browser console after login
const kc = window.keycloak
console.log({
  token: kc.token?.substring(0, 50) + '...',
  refreshToken: kc.refreshToken?.substring(0, 50) + '...',
  tokenParsed: kc.tokenParsed
})

// Decode token manually
const payload = kc.token.split('.')[1]
const decoded = JSON.parse(atob(payload))
console.log(decoded)
```

### Test API call manually:
```javascript
// In browser console
const kc = window.keycloak
fetch('http://api.theddt.local/api/v1/auth/me/', {
  credentials: 'include',
  headers: {
    'Authorization': `Bearer ${kc.token}`
  }
})
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

### Check CORS preflight:
```javascript
// In browser console
fetch('http://api.theddt.local/api/v1/auth/me/', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'http://localhost:3000',
    'Access-Control-Request-Method': 'GET',
    'Access-Control-Request-Headers': 'authorization'
  }
})
  .then(r => {
    console.log('Preflight response:')
    for (let [key, value] of r.headers.entries()) {
      if (key.startsWith('access-control')) {
        console.log(`${key}: ${value}`)
      }
    }
  })
```

---

## Key Learnings

1. **CORS with credentials requires both sides:**
   - Backend must send `Access-Control-Allow-Credentials: true`
   - Frontend must send `credentials: 'include'`
   - Both are required even when using Authorization header (not cookies)

2. **React Strict Mode double-mounts in development:**
   - Effects run twice: mount → unmount → mount
   - Async operations must handle being called twice
   - Using singletons helps share state between mounts
   - Don't use `cancelled` flags with async operations in Strict Mode

3. **Keycloak initialization is critical:**
   - Must call `keycloak.init()` exactly once
   - Adapter is only set up after `init()` completes
   - Methods like `login()` depend on adapter
   - Check for adapter presence to detect initialization status

4. **Browser testing is essential:**
   - curl tests don't catch browser-specific issues (CORS, HTTPS, etc.)
   - Automated browser testing (Playwright) catches real issues
   - Console logs are invaluable for debugging React apps

5. **Environment variables must be prefixed:**
   - Next.js requires `NEXT_PUBLIC_` prefix for browser-side variables
   - Without prefix, variables are `undefined` in browser
   - Always verify env vars are available in browser console
