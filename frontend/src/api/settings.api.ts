import { apiClient } from './client'
import type { UserSettings, UserSettingsUpdate, Theme } from './types'

export const settingsApi = {
  get: async (): Promise<UserSettings> => {
    const { data } = await apiClient.get<UserSettings>('/settings')
    return data
  },

  update: async (patch: UserSettingsUpdate): Promise<UserSettings> => {
    const { data } = await apiClient.patch<UserSettings>('/settings', patch)
    return data
  },

  setTheme: async (theme: Theme): Promise<UserSettings> => {
    const { data } = await apiClient.patch<UserSettings>(`/settings/theme?theme=${theme}`)
    return data
  },
}
