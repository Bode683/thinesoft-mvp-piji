import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { REHYDRATE } from 'redux-persist'
import type { AuthMe } from '../types'

interface AuthState {
  // Keycloak authentication state
  isAuthenticated: boolean
  status: 'idle' | 'loading' | 'ready' | 'error'

  // User profile state (from /auth/me)
  user: AuthMe | null
  selectedTenant: string | null
  profileLoaded: boolean
}

const initialState: AuthState = {
  isAuthenticated: false,
  status: 'idle',
  user: null,
  selectedTenant: null,
  profileLoaded: false,
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Keycloak reducers (Phase 1)
    authLoading: (state) => {
      state.status = 'loading'
    },
    authReady: (state, action: PayloadAction<boolean>) => {
      state.isAuthenticated = action.payload
      state.status = 'ready'
    },
    authError: (state) => {
      state.status = 'error'
      state.isAuthenticated = false
    },

    // User profile reducers (Phase 3)
    setUser: (state, action: PayloadAction<AuthMe>) => {
      state.user = action.payload
      state.selectedTenant = state.selectedTenant ?? action.payload.defaultTenant
      state.profileLoaded = true
    },
    clearUser: (state) => {
      state.user = null
      state.selectedTenant = null
      state.profileLoaded = false
    },
    setTenant: (state, action: PayloadAction<string>) => {
      state.selectedTenant = action.payload
    },

    // Full reset
    authReset: () => initialState,
  },
  extraReducers: (builder) => {
    builder.addCase(REHYDRATE, (state) => {
      // Auth state always comes from Keycloak, never from localStorage
      // This prevents bugs if someone accidentally adds 'auth' to whitelist
      return state
    })
  },
})

export const {
  authLoading,
  authReady,
  authError,
  setUser,
  clearUser,
  setTenant,
  authReset,
} = authSlice.actions

export const authReducer = authSlice.reducer
