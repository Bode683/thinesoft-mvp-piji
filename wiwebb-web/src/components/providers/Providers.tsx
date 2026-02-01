"use client"

import { Provider } from 'react-redux'
import { store } from '@/lib/store/store'
import { AuthBootstrap } from '@/features/auth/components/AuthBootstrap'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <AuthBootstrap>{children}</AuthBootstrap>
    </Provider>
  )
}
