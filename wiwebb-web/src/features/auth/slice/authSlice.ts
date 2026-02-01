import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AuthState {
  isAuthenticated: boolean
  status: 'idle' | 'loading' | 'ready' | 'error'
}

const initialState: AuthState = {
  isAuthenticated: false,
  status: 'idle',
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
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
    authReset: () => initialState,
  },
})

export const {
  authLoading,
  authReady,
  authError,
  authReset,
} = authSlice.actions

export const authReducer = authSlice.reducer
