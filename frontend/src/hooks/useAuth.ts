import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth.api'
import { settingsApi } from '@/api/settings.api'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'

export const authKeys = {
  me: ['auth', 'me'] as const,
}

export function useCurrentUser() {
  const token = useAuthStore((s) => s.token)
  return useQuery({
    queryKey: authKeys.me,
    queryFn: authApi.me,
    enabled: !!token,
    staleTime: Infinity,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  const setAuth = useAuthStore((s) => s.setAuth)
  const setTheme = useThemeStore((s) => s.setTheme)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const token = await authApi.login(email, password)
      // Store token immediately so subsequent API calls include Authorization header
      localStorage.setItem('access_token', token.access_token)
      const user = await authApi.me()
      const settings = await settingsApi.get()
      return { token, user, settings }
    },
    onSuccess: ({ token, user, settings }) => {
      setAuth(token, user)
      setTheme(settings.theme)
      queryClient.setQueryData(authKeys.me, user)
      navigate('/dashboard')
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  return () => {
    logout()
    queryClient.clear()
    navigate('/login')
  }
}

export function useRegister() {
  const navigate = useNavigate()
  return useMutation({
    mutationFn: (data: { email: string; password: string; full_name?: string }) =>
      authApi.register(data.email, data.password, data.full_name),
    onSuccess: () => navigate('/login'),
  })
}
