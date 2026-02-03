"use client"

import { useAppDispatch, useAppSelector } from '@/lib/store/hooks'
import { clearUser, authReset } from '@/features/auth/slice/authSlice'
import { baseApi } from '@/services/api/baseApi'
import { useKeycloak } from '@/lib/keycloak/KeycloakContext'

export function LogoutButton() {
  const dispatch = useAppDispatch()
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated)
  const { keycloak, initialized } = useKeycloak()

  const handleLogout = () => {
    if (!keycloak || !initialized) {
      console.error('Keycloak not initialized')
      return
    }

    // Clear Redux state
    dispatch(clearUser())
    dispatch(authReset())

    // Clear RTK Query cache
    dispatch(baseApi.util.resetApiState())

    // Logout from Keycloak
    keycloak.logout({
      redirectUri: window.location.origin,
    })
  }

  const handleLogin = async () => {
    if (!keycloak || !initialized) {
      console.error('Keycloak not initialized')
      return
    }

    try {
      console.log('Initiating Keycloak login...', {
        keycloakUrl: process.env.NEXT_PUBLIC_KEYCLOAK_URL,
        realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM,
        clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID,
        keycloakInstance: !!keycloak,
        initialized,
        authenticated: keycloak.authenticated,
        hasLoginMethod: typeof keycloak.login === 'function',
      })

      // Redirect to Keycloak login
      await keycloak.login({
        redirectUri: window.location.origin,
      })
    } catch (error) {
      console.error('Login error:', error)
    }
  }

  // Don't render until keycloak is loaded and initialized
  if (!keycloak || !initialized) {
    return (
      <button
        disabled
        className="rounded-md border border-muted bg-muted px-4 py-2 text-sm font-medium text-muted-foreground"
      >
        Loading...
      </button>
    )
  }

  // Show Login button if not authenticated
  if (!isAuthenticated) {
    return (
      <button
        onClick={handleLogin}
        className="rounded-md border border-primary bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Login
      </button>
    )
  }

  // Show Logout button if authenticated
  return (
    <button
      onClick={handleLogout}
      className="rounded-md border border-destructive bg-background px-4 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive hover:text-destructive-foreground"
    >
      Logout
    </button>
  )
}
