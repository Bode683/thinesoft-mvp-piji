import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { keycloak } from '@/lib/keycloak/keycloak'

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    prepareHeaders: async (headers) => {
      try {
        // Only attempt token refresh if Keycloak is authenticated
        if (keycloak.authenticated && keycloak.token) {
          // Refresh token if it expires in the next 5 minutes (300 seconds)
          await keycloak.updateToken(300)

          // Add Authorization header with fresh token
          if (keycloak.token) {
            headers.set('Authorization', `Bearer ${keycloak.token}`)
          }
        } else {
          console.warn('Keycloak not authenticated, skipping token refresh')
        }
      } catch (error) {
        console.error('Token refresh failed:', error)
        // Don't fail the request - let backend return 401 if token is invalid
        // This allows proper error handling in the UI
      }

      return headers
    },
  }),
  tagTypes: ['User', 'Tenant', 'Project'],
  endpoints: () => ({}),
})
