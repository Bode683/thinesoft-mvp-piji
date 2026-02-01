"use client"

import { useAuthBootstrap } from '../hooks/useAuthBootstrap'
import { useAppSelector } from '@/lib/store/hooks'

export function AuthBootstrap({ children }: { children: React.ReactNode }) {
  const { ready } = useAuthBootstrap()
  const status = useAppSelector((state) => state.auth.status)

  if (status === 'error') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="rounded-lg border bg-card p-8 text-center shadow-lg">
          <div className="mb-4 text-4xl">❌</div>
          <h2 className="mb-2 text-xl font-semibold text-foreground">Authentication Failed</h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Unable to initialize authentication. Please try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
