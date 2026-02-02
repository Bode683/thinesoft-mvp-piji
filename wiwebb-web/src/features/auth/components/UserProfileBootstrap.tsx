"use client"

import { useGetMeQuery } from '../api/authApi'

export function UserProfileBootstrap({ children }: { children: React.ReactNode }) {
  const { isLoading, isError, error } = useGetMeQuery()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <div className="text-sm text-muted-foreground">Loading profile...</div>
        </div>
      </div>
    )
  }

  if (isError) {
    const statusCode = (error as any)?.status
    // Show non-blocking error notification instead of full-screen modal
    return (
      <>
        <div className="fixed top-20 right-4 z-50 rounded-lg border border-destructive bg-card p-4 shadow-lg max-w-sm">
          <div className="flex items-start gap-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-foreground">Profile Load Failed</h3>
              <p className="text-xs text-muted-foreground mt-1">
                {statusCode === 401
                  ? 'Session expired. Please log in again.'
                  : 'Unable to load your profile. Please try again.'}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-2 rounded-md bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:opacity-90"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
        {children}
      </>
    )
  }

  return <>{children}</>
}
