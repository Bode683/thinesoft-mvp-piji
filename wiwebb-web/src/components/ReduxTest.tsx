"use client"

import { useAppSelector } from '@/lib/store/hooks'

export function ReduxTest() {
  const auth = useAppSelector((state) => state.auth)

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
      </div>
    </div>
  )
}
