import { createSlice } from '@reduxjs/toolkit'

interface UIState {
  darkMode: boolean
}

const initialState: UIState = {
  darkMode: false,
}

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleDarkMode: (state) => {
      state.darkMode = !state.darkMode
    },
    setDarkMode: (state, action) => {
      state.darkMode = action.payload
    },
  },
})

export const { toggleDarkMode, setDarkMode } = uiSlice.actions
export const uiReducer = uiSlice.reducer
