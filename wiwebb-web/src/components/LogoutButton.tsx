"use client"

import { keycloak } from '@/lib/keycloak/keycloak'

export function LogoutButton() {
  const handleLogout = () => {
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
