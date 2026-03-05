import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings.api'
import { useThemeStore } from '@/stores/themeStore'
import type { Theme } from '@/api/types'

export const settingsKeys = {
  settings: ['settings'] as const,
}

export function useSettings() {
  return useQuery({
    queryKey: settingsKeys.settings,
    queryFn: settingsApi.get,
  })
}

export function useUpdateTheme() {
  const queryClient = useQueryClient()
  const setTheme = useThemeStore((s) => s.setTheme)

  return useMutation({
    mutationFn: (theme: Theme) => settingsApi.setTheme(theme),
    onMutate: (theme) => {
      setTheme(theme)
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(settingsKeys.settings, settings)
    },
    onError: (_err, theme) => {
      const previousTheme: Theme = theme === 'dark' ? 'light' : 'dark'
      setTheme(previousTheme)
    },
  })
}
