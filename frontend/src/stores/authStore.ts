import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Token } from '@/api/types'

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: Token, user: User) => void
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token: Token, user: User) => {
        localStorage.setItem('access_token', token.access_token)
        set({ token: token.access_token, user })
      },
      setUser: (user: User) => set({ user }),
      logout: () => {
        localStorage.removeItem('access_token')
        set({ token: null, user: null })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
