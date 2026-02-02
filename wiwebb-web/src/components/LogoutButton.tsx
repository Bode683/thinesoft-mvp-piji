"use client"

import { keycloak } from '@/lib/keycloak/keycloak'
import { useAppDispatch } from '@/lib/store/hooks'
import { clearUser, authReset } from '@/features/auth/slice/authSlice'
import { baseApi } from '@/services/api/baseApi'

export function LogoutButton() {
  const dispatch = useAppDispatch()

  const handleLogout = () => {
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

  return (
    <button
      onClick={handleLogout}
      className="rounded-md border border-destructive bg-background px-4 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive hover:text-destructive-foreground"
    >
      Logout
    </button>
  )
}
