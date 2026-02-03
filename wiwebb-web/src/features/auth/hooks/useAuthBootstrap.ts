"use client"

import { useEffect, useState } from 'react'
import { getKeycloak } from '@/lib/keycloak/keycloak'
import { useAppDispatch } from '@/lib/store/hooks'
import { authLoading, authReady, authError } from '../slice/authSlice'

export function useAuthBootstrap() {
  const dispatch = useAppDispatch()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    // Get the Keycloak instance (will be created if needed)
    const keycloak = getKeycloak()

    console.log('[useAuthBootstrap] Starting initialization...')
    console.log('[useAuthBootstrap] Keycloak instance obtained:', {
      exists: !!keycloak,
      authenticated: keycloak.authenticated,
      hasAdapter: !!(keycloak as any).adapter,
      hasInit: typeof keycloak.init === 'function',
    })

    // Check if Keycloak is already initialized by checking for the adapter
    // The adapter is only set after init() is called
    if ((keycloak as any).adapter) {
      // Already initialized - this handles React Strict Mode second mount
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
        onLoad: 'check-sso',  // Check SSO status without forcing redirect
        pkceMethod: 'S256',
        checkLoginIframe: false, // Required for Next.js - prevents SSR/hydration issues
      })
      .then((authenticated) => {
        console.log('Keycloak initialized:', {
          authenticated,
          hasAdapter: !!(keycloak as any).adapter,
          adapterType: (keycloak as any).adapter?.type,
          loginMethod: typeof keycloak.login,
          hasToken: !!keycloak.token,
        })
        dispatch(authReady(!!authenticated))
        setReady(true)
      })
      .catch((error: any) => {
        // This can happen if init() is called twice (React Strict Mode)
        if (error.message?.includes('only be initialized once')) {
          console.warn('[useAuthBootstrap] Keycloak init called twice (React Strict Mode)')
          // The adapter should be set from the first call, so just mark as ready
          if ((keycloak as any).adapter) {
            dispatch(authReady(!!keycloak.authenticated))
            setReady(true)
            return
          }
        }

        console.error('Keycloak initialization error:', error)
        dispatch(authError())
      })
  }, [dispatch])

  return { ready }
}
