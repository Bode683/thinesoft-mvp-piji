"use client"

import { useEffect, useState } from 'react'
import { keycloak } from '@/lib/keycloak/keycloak'

export function KeycloakSmokeTest() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'authenticated' | 'error'>('idle')
  const [error, setError] = useState<string>()

  useEffect(() => {
    setStatus('loading')

    keycloak
      .init({
        onLoad: 'login-required',
        pkceMethod: 'S256',
        checkLoginIframe: false, // Required for Next.js - prevents SSR/hydration issues
      })
      .then((authenticated) => {
        if (authenticated) {
          setStatus('authenticated')
        } else {
          setError('Not authenticated')
          setStatus('error')
        }
      })
      .catch((err) => {
        setError(err.message || 'Keycloak init failed')
        setStatus('error')
      })
  }, [])

  return (
    <div className="fixed top-4 right-4 rounded-lg border bg-card p-4 text-sm shadow-lg max-w-xs">
      <div className="font-semibold mb-2">Keycloak Smoke Test</div>

      {status === 'loading' && (
        <div className="text-muted-foreground">Initializing...</div>
      )}

      {status === 'authenticated' && (
        <div className="space-y-2">
          <div className="text-green-600 dark:text-green-400">✅ Authenticated</div>
          <div className="text-xs text-muted-foreground break-all">
            <div>User: {keycloak.tokenParsed?.preferred_username || 'unknown'}</div>
            <div>Email: {keycloak.tokenParsed?.email || 'unknown'}</div>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="text-red-600 dark:text-red-400">
          ❌ Error: {error}
        </div>
      )}
    </div>
  )
}
