"use client"

import { useAppDispatch, useAppSelector } from '@/lib/store/hooks'
import { toggleDarkMode } from '@/features/ui/slice/uiSlice'

export function DarkModeToggle() {
  const darkMode = useAppSelector((state) => state.ui.darkMode)
  const dispatch = useAppDispatch()

  return (
    <div className="fixed top-4 left-4 rounded-lg border bg-card p-4 shadow-lg">
      <div className="mb-2 text-xs font-semibold text-muted-foreground">
        Persistence Test
      </div>
      <button
        onClick={() => dispatch(toggleDarkMode())}
        className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
          darkMode
            ? 'bg-primary text-primary-foreground'
            : 'border border-input bg-background hover:bg-accent'
        }`}
      >
        Dark mode: {darkMode ? 'ON' : 'OFF'}
      </button>
      <div className="mt-2 text-[10px] text-muted-foreground">
        Toggle and reload page to test persistence
      </div>
    </div>
  )
}
