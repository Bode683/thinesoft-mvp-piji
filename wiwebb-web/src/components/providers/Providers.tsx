"use client"

import { Provider } from 'react-redux'
import { PersistGate } from 'redux-persist/integration/react'
import { store, persistor } from '@/lib/store/store'
import { AuthBootstrap } from '@/features/auth/components/AuthBootstrap'
import { UserProfileBootstrap } from '@/features/auth/components/UserProfileBootstrap'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <AuthBootstrap>
          <UserProfileBootstrap>
            {children}
          </UserProfileBootstrap>
        </AuthBootstrap>
      </PersistGate>
    </Provider>
  )
}
