import { baseApi } from '@/services/api/baseApi'
import type { AuthMe } from '../types'
import { setUser, clearUser } from '../slice/authSlice'

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getMe: builder.query<AuthMe, void>({
      query: () => '/auth/me/',
      providesTags: ['User'],
      async onQueryStarted(_, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled
          dispatch(setUser(data))
        } catch (error) {
          console.error('Failed to fetch user profile:', error)
          dispatch(clearUser())
        }
      },
    }),
  }),
  overrideExisting: false,
})

export const { useGetMeQuery } = authApi
