"use client"

import { useAppSelector } from '@/lib/store/hooks'
import { useKeycloak } from '@/lib/keycloak/KeycloakContext'
import { useEffect, useState } from 'react'

export function AuthDebug() {
  const authState = useAppSelector((state) => state.auth)
  const { keycloak, initialized } = useKeycloak()
  const [keycloakState, setKeycloakState] = useState({
    authenticated: keycloak?.authenticated,
    token: keycloak?.token ? '***' + keycloak.token.slice(-10) : null,
    tokenParsed: keycloak?.tokenParsed,
    ready: initialized,
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setKeycloakState({
        authenticated: keycloak?.authenticated,
        token: keycloak?.token ? '***' + keycloak.token.slice(-10) : null,
        tokenParsed: keycloak?.tokenParsed,
        ready: initialized,
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [keycloak, initialized])

  return (
    <div className="fixed bottom-4 right-4 max-w-md rounded-lg border bg-card p-4 text-xs shadow-lg">
      <h3 className="mb-2 font-bold">Auth Debug</h3>

      <div className="mb-3">
        <h4 className="font-semibold text-primary">Redux State:</h4>
        <pre className="mt-1 overflow-auto rounded bg-muted p-2">
          {JSON.stringify({
            status: authState.status,
            isAuthenticated: authState.isAuthenticated,
            profileLoaded: authState.profileLoaded,
            user: authState.user ? {
              id: authState.user.id,
              email: authState.user.email,
              username: authState.user.username,
            } : null,
          }, null, 2)}
        </pre>
      </div>

      <div className="mb-3">
        <h4 className="font-semibold text-primary">Keycloak State:</h4>
        <pre className="mt-1 overflow-auto rounded bg-muted p-2">
          {JSON.stringify({
            ready: keycloakState.ready,
            authenticated: keycloakState.authenticated,
            hasToken: !!keycloakState.token,
            tokenSnippet: keycloakState.token,
            user: keycloakState.tokenParsed ? {
              sub: keycloakState.tokenParsed.sub,
              email: keycloakState.tokenParsed.email,
              preferred_username: keycloakState.tokenParsed.preferred_username,
            } : null,
          }, null, 2)}
        </pre>
      </div>

      <div>
        <h4 className="font-semibold text-primary">Environment:</h4>
        <pre className="mt-1 overflow-auto rounded bg-muted p-2">
          {JSON.stringify({
            apiUrl: process.env.NEXT_PUBLIC_API_URL,
            keycloakUrl: process.env.NEXT_PUBLIC_KEYCLOAK_URL,
            realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM,
            clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID,
          }, null, 2)}
        </pre>
      </div>
    </div>
  )
}
