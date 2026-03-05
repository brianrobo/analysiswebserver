import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Theme } from '@/api/types'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme: Theme) => {
        document.documentElement.classList.remove('light', 'dark')
        document.documentElement.classList.add(theme)
        set({ theme })
      },
    }),
    { name: 'theme-storage' }
  )
)
