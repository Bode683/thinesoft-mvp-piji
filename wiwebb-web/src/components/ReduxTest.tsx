"use client"

import { useAppSelector } from '@/lib/store/hooks'

export function ReduxTest() {
  const auth = useAppSelector((state) => state.auth)
  const ui = useAppSelector((state) => state.ui)

  return (
    <div className="fixed bottom-4 right-4 rounded-lg border bg-card p-4 text-xs shadow-lg max-w-xs">
      <div className="font-semibold mb-2">Redux Status</div>
      <div className="space-y-1">
        <div className="text-muted-foreground">
          ✅ Store connected
        </div>
        <div className="text-muted-foreground">
          Auth status: <span className="font-mono">{auth.status}</span>
        </div>
        <div className="text-muted-foreground">
          Authenticated: <span className="font-mono">{auth.isAuthenticated ? 'true' : 'false'}</span>
        </div>
        {auth.user && (
          <>
            <div className="mt-2 border-t pt-2 text-muted-foreground">
              User: <span className="font-mono text-[10px]">{auth.user.name}</span>
            </div>
            <div className="text-muted-foreground">
              Tenant: <span className="font-mono text-[10px]">{auth.selectedTenant}</span>
            </div>
          </>
        )}
        <div className="mt-2 border-t pt-2 text-muted-foreground">
          UI darkMode: <span className="font-mono">{ui.darkMode ? 'true' : 'false'}</span>
        </div>
        <div className="text-[10px] text-muted-foreground">
          ℹ️ Only UI state persists
        </div>
      </div>
    </div>
  )
}
