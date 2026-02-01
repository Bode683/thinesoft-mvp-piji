"use client"

import { useEffect, useState } from 'react'
import { keycloak } from '@/lib/keycloak/keycloak'
import { useAppDispatch } from '@/lib/store/hooks'
import { authLoading, authReady, authError } from '../slice/authSlice'

export function useAuthBootstrap() {
  const dispatch = useAppDispatch()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false

    dispatch(authLoading())

    keycloak
      .init({
        onLoad: 'login-required',
        pkceMethod: 'S256',
        checkLoginIframe: false, // Required for Next.js - prevents SSR/hydration issues
      })
      .then((authenticated) => {
        if (!cancelled) {
          dispatch(authReady(!!authenticated))
          setReady(true)
        }
      })
      .catch(() => {
        if (!cancelled) {
          dispatch(authError())
        }
      })

    // Cleanup function to prevent state updates on unmounted component
    return () => {
      cancelled = true
    }
  }, [dispatch])

  return { ready }
}
